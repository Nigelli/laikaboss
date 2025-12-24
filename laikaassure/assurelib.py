# Copyright 2025 Lockheed Martin Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Laika Assure - Core Library

Provides functionality for:
- Sending samples to laikaboss endpoints (ZMQ or REST)
- Loading and validating test case definitions
- Comparing scan results against expected outcomes
"""

import json
import logging
import os
import re
import yaml
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import laikaboss client for ZMQ communication
try:
    from laikaboss.clientLib import Client as ZMQClient
    from laikaboss.objectmodel import ExternalObject, ExternalVars
    from laikaboss.constants import level_metadata
    HAS_ZMQ = True
except ImportError:
    ZMQClient = None
    ExternalObject = None
    ExternalVars = None
    level_metadata = None
    HAS_ZMQ = False

# Import requests for REST API communication
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    requests = None
    HAS_REQUESTS = False


class AssertionType(Enum):
    """Types of assertions that can be made against scan results."""
    EQUALS = "equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"  # regex
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


@dataclass
class Assertion:
    """A single assertion to validate against scan results."""
    path: str  # JSONPath-like path to the value (e.g., "disposition", "flags", "metadata.SCAN_YARA.matches")
    assertion_type: AssertionType
    expected: Any = None
    message: Optional[str] = None  # Custom failure message

    def evaluate(self, actual_value: Any) -> tuple[bool, str]:
        """
        Evaluate the assertion against an actual value.

        Returns:
            Tuple of (passed: bool, message: str)
        """
        if self.assertion_type == AssertionType.EQUALS:
            passed = actual_value == self.expected
            msg = f"Expected {self.path} to equal '{self.expected}', got '{actual_value}'"

        elif self.assertion_type == AssertionType.CONTAINS:
            if isinstance(actual_value, (list, tuple)):
                passed = self.expected in actual_value
            elif isinstance(actual_value, str):
                passed = self.expected in actual_value
            elif isinstance(actual_value, dict):
                passed = self.expected in actual_value
            else:
                passed = False
            msg = f"Expected {self.path} to contain '{self.expected}', got '{actual_value}'"

        elif self.assertion_type == AssertionType.NOT_CONTAINS:
            if isinstance(actual_value, (list, tuple)):
                passed = self.expected not in actual_value
            elif isinstance(actual_value, str):
                passed = self.expected not in actual_value
            elif isinstance(actual_value, dict):
                passed = self.expected not in actual_value
            else:
                passed = True
            msg = f"Expected {self.path} to not contain '{self.expected}', but it did"

        elif self.assertion_type == AssertionType.MATCHES:
            if isinstance(actual_value, str):
                passed = bool(re.search(self.expected, actual_value))
            elif isinstance(actual_value, (list, tuple)):
                passed = any(re.search(self.expected, str(v)) for v in actual_value)
            else:
                passed = bool(re.search(self.expected, str(actual_value)))
            msg = f"Expected {self.path} to match pattern '{self.expected}', got '{actual_value}'"

        elif self.assertion_type == AssertionType.EXISTS:
            passed = actual_value is not None
            msg = f"Expected {self.path} to exist, but it was not found"

        elif self.assertion_type == AssertionType.NOT_EXISTS:
            passed = actual_value is None
            msg = f"Expected {self.path} to not exist, but found '{actual_value}'"

        elif self.assertion_type == AssertionType.GREATER_THAN:
            try:
                passed = float(actual_value) > float(self.expected)
            except (TypeError, ValueError):
                passed = False
            msg = f"Expected {self.path} > {self.expected}, got '{actual_value}'"

        elif self.assertion_type == AssertionType.LESS_THAN:
            try:
                passed = float(actual_value) < float(self.expected)
            except (TypeError, ValueError):
                passed = False
            msg = f"Expected {self.path} < {self.expected}, got '{actual_value}'"
        else:
            passed = False
            msg = f"Unknown assertion type: {self.assertion_type}"

        if self.message and not passed:
            msg = self.message

        return passed, msg


@dataclass
class TestCase:
    """A test case definition with sample file and expected outcomes."""
    name: str
    sample_path: str
    description: str = ""
    assertions: List[Assertion] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'TestCase':
        """Load a test case from a YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        assertions = []
        for assertion_data in data.get('assertions', []):
            # Determine assertion type from the keys present
            if 'equals' in assertion_data:
                assertion_type = AssertionType.EQUALS
                expected = assertion_data['equals']
            elif 'contains' in assertion_data:
                assertion_type = AssertionType.CONTAINS
                expected = assertion_data['contains']
            elif 'not_contains' in assertion_data:
                assertion_type = AssertionType.NOT_CONTAINS
                expected = assertion_data['not_contains']
            elif 'matches' in assertion_data:
                assertion_type = AssertionType.MATCHES
                expected = assertion_data['matches']
            elif 'exists' in assertion_data:
                assertion_type = AssertionType.EXISTS
                expected = None
            elif 'not_exists' in assertion_data:
                assertion_type = AssertionType.NOT_EXISTS
                expected = None
            elif 'greater_than' in assertion_data:
                assertion_type = AssertionType.GREATER_THAN
                expected = assertion_data['greater_than']
            elif 'less_than' in assertion_data:
                assertion_type = AssertionType.LESS_THAN
                expected = assertion_data['less_than']
            else:
                continue

            assertions.append(Assertion(
                path=assertion_data['path'],
                assertion_type=assertion_type,
                expected=expected,
                message=assertion_data.get('message')
            ))

        # Resolve sample path relative to yaml file location
        yaml_dir = os.path.dirname(os.path.abspath(yaml_path))
        sample_path = data.get('sample', '')
        if sample_path and not os.path.isabs(sample_path):
            sample_path = os.path.join(yaml_dir, sample_path)

        return cls(
            name=data.get('name', os.path.basename(yaml_path)),
            sample_path=sample_path,
            description=data.get('description', ''),
            assertions=assertions,
            tags=data.get('tags', []),
            enabled=data.get('enabled', True)
        )

    def to_yaml(self) -> str:
        """Serialize the test case to YAML format."""
        data = {
            'name': self.name,
            'sample': os.path.basename(self.sample_path),
            'description': self.description,
            'tags': self.tags,
            'enabled': self.enabled,
            'assertions': []
        }

        for assertion in self.assertions:
            assertion_data = {'path': assertion.path}

            if assertion.assertion_type == AssertionType.EQUALS:
                assertion_data['equals'] = assertion.expected
            elif assertion.assertion_type == AssertionType.CONTAINS:
                assertion_data['contains'] = assertion.expected
            elif assertion.assertion_type == AssertionType.NOT_CONTAINS:
                assertion_data['not_contains'] = assertion.expected
            elif assertion.assertion_type == AssertionType.MATCHES:
                assertion_data['matches'] = assertion.expected
            elif assertion.assertion_type == AssertionType.EXISTS:
                assertion_data['exists'] = True
            elif assertion.assertion_type == AssertionType.NOT_EXISTS:
                assertion_data['not_exists'] = True
            elif assertion.assertion_type == AssertionType.GREATER_THAN:
                assertion_data['greater_than'] = assertion.expected
            elif assertion.assertion_type == AssertionType.LESS_THAN:
                assertion_data['less_than'] = assertion.expected

            if assertion.message:
                assertion_data['message'] = assertion.message

            data['assertions'].append(assertion_data)

        return yaml.dump(data, default_flow_style=False, sort_keys=False)


@dataclass
class AssertionResult:
    """Result of evaluating a single assertion."""
    assertion: Assertion
    passed: bool
    message: str
    actual_value: Any = None


@dataclass
class TestResult:
    """Result of running a single test case."""
    test_case: TestCase
    passed: bool
    assertion_results: List[AssertionResult] = field(default_factory=list)
    scan_result: Optional[Dict] = None
    error: Optional[str] = None
    duration_ms: float = 0


class ScanClient:
    """Abstract base for scan clients."""

    def scan(self, file_path: str, filename: Optional[str] = None) -> Dict:
        """
        Scan a file and return the result as a dictionary.

        Args:
            file_path: Path to the file to scan
            filename: Optional filename to use (defaults to basename of file_path)

        Returns:
            Dictionary containing scan results
        """
        raise NotImplementedError


class ZMQScanClient(ScanClient):
    """Scan client using ZMQ protocol (laikad)."""

    def __init__(self, broker_url: str, timeout: int = 30000):
        """
        Initialize ZMQ scan client.

        Args:
            broker_url: ZMQ broker URL (e.g., "tcp://localhost:5558")
            timeout: Timeout in milliseconds
        """
        if not HAS_ZMQ:
            raise ImportError("laikaboss.clientlib not available. Install laikaboss or use REST client.")

        self.broker_url = broker_url
        self.timeout = timeout
        self._client = None

    def _get_client(self) -> ZMQClient:
        """Get or create ZMQ client."""
        if self._client is None:
            self._client = ZMQClient(self.broker_url)
        return self._client

    def scan(self, file_path: str, filename: Optional[str] = None) -> Dict:
        """Scan a file via ZMQ."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Sample file not found: {file_path}")

        with open(file_path, 'rb') as f:
            file_buffer = f.read()

        if filename is None:
            filename = os.path.basename(file_path)

        # Create external object for scanning
        # Use level_metadata to get moduleMetadata in response (not level_minimal which strips it)
        ext_vars = ExternalVars(filename=filename)
        ext_obj = ExternalObject(
            buffer=file_buffer,
            externalVars=ext_vars,
            level=level_metadata
        )

        client = self._get_client()
        result = client.send(ext_obj, timeout=self.timeout)

        if result is None:
            raise TimeoutError(f"Scan timed out after {self.timeout}ms")

        # Convert result to JSON-serializable dict
        return self._result_to_dict(result)

    def _result_to_dict(self, result) -> Dict:
        """Convert scan result object to dictionary."""
        # Use the existing getJSON function logic
        from laikaboss.clientLib import getJSON
        json_str = getJSON(result)
        return json.loads(json_str)

    def close(self):
        """Close the ZMQ client."""
        if self._client:
            self._client.close()
            self._client = None


class RESTScanClient(ScanClient):
    """Scan client using REST API (laikarestd)."""

    def __init__(self, base_url: str, timeout: int = 30, verify_ssl: bool = True):
        """
        Initialize REST scan client.

        Args:
            base_url: Base URL of laikarestd (e.g., "http://localhost:5000")
            timeout: Timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library not available. Install with: pip install requests")

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def scan(self, file_path: str, filename: Optional[str] = None) -> Dict:
        """Scan a file via REST API."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Sample file not found: {file_path}")

        if filename is None:
            filename = os.path.basename(file_path)

        url = f"{self.base_url}/api/scan"

        with open(file_path, 'rb') as f:
            files = {'file': (filename, f)}
            response = requests.post(
                url,
                files=files,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

        response.raise_for_status()
        return response.json()


def get_value_at_path(data: Dict, path: str) -> Any:
    """
    Get a value from a nested dictionary using a dot-notation path.

    Supports special paths:
    - "disposition" -> root object's DISPOSITIONER result
    - "flags" -> rollup of all flags
    - "modules" -> list of all scan modules run
    - "metadata.MODULE_NAME.field" -> specific module metadata

    Args:
        data: The scan result dictionary
        path: Dot-notation path to the value

    Returns:
        The value at the path, or None if not found
    """
    try:
        scan_results = data.get('scan_result', [])
        if not scan_results:
            return None

        # Find root object (depth=0, order=0 or first object)
        root_obj = None
        for obj in scan_results:
            if obj.get('depth', 0) == 0 and obj.get('order', 0) == 0:
                root_obj = obj
                break
        if root_obj is None and scan_results:
            root_obj = scan_results[0]

        # Handle special paths
        if path == 'disposition':
            return root_obj.get('moduleMetadata', {}).get('DISPOSITIONER', {}).get('Disposition', {}).get('Result')

        elif path == 'disposition_matches':
            return root_obj.get('moduleMetadata', {}).get('DISPOSITIONER', {}).get('Disposition', {}).get('Matches', [])

        elif path == 'flags':
            # Rollup all flags from all objects
            all_flags = []
            for obj in scan_results:
                all_flags.extend(obj.get('flags', []))
            return list(set(all_flags))

        elif path == 'modules':
            # Get list of all modules run on root object
            return root_obj.get('scanModules', [])

        elif path == 'all_modules':
            # Get list of all modules run on all objects
            all_modules = []
            for obj in scan_results:
                all_modules.extend(obj.get('scanModules', []))
            return list(set(all_modules))

        elif path == 'file_count':
            return len(scan_results)

        elif path == 'content_types':
            return root_obj.get('contentType', [])

        elif path == 'file_types':
            return root_obj.get('fileType', [])

        elif path.startswith('metadata.'):
            # Navigate into moduleMetadata
            parts = path.split('.')[1:]  # Remove 'metadata' prefix
            current = root_obj.get('moduleMetadata', {})
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current

        elif path.startswith('root.'):
            # Direct access to root object fields
            parts = path.split('.')[1:]
            current = root_obj
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current

        else:
            # Try direct path on root object
            parts = path.split('.')
            current = root_obj
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current

    except Exception as e:
        logging.debug(f"Error getting value at path '{path}': {e}")
        return None


class TestRunner:
    """Runs test cases against a scan endpoint."""

    def __init__(self, client: ScanClient):
        """
        Initialize test runner.

        Args:
            client: Scan client to use for scanning
        """
        self.client = client

    def run_test(self, test_case: TestCase) -> TestResult:
        """
        Run a single test case.

        Args:
            test_case: The test case to run

        Returns:
            TestResult with pass/fail status and details
        """
        import time

        if not test_case.enabled:
            return TestResult(
                test_case=test_case,
                passed=True,
                error="Test case disabled"
            )

        start_time = time.time()

        try:
            # Scan the sample
            scan_result = self.client.scan(test_case.sample_path)

            # Evaluate all assertions
            assertion_results = []
            all_passed = True

            for assertion in test_case.assertions:
                actual_value = get_value_at_path(scan_result, assertion.path)
                passed, message = assertion.evaluate(actual_value)

                assertion_results.append(AssertionResult(
                    assertion=assertion,
                    passed=passed,
                    message=message,
                    actual_value=actual_value
                ))

                if not passed:
                    all_passed = False

            duration_ms = (time.time() - start_time) * 1000

            return TestResult(
                test_case=test_case,
                passed=all_passed,
                assertion_results=assertion_results,
                scan_result=scan_result,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_case=test_case,
                passed=False,
                error=str(e),
                duration_ms=duration_ms
            )

    def run_tests(self, test_cases: List[TestCase], tags: Optional[List[str]] = None) -> List[TestResult]:
        """
        Run multiple test cases.

        Args:
            test_cases: List of test cases to run
            tags: Optional list of tags to filter by (runs tests matching any tag)

        Returns:
            List of TestResult objects
        """
        results = []

        for test_case in test_cases:
            # Filter by tags if specified
            if tags:
                if not any(tag in test_case.tags for tag in tags):
                    continue

            result = self.run_test(test_case)
            results.append(result)

        return results


def load_test_cases(directory: str, recursive: bool = True) -> List[TestCase]:
    """
    Load all test cases from a directory.

    Args:
        directory: Directory containing test case YAML files
        recursive: Whether to search subdirectories

    Returns:
        List of TestCase objects
    """
    test_cases = []
    directory = Path(directory)

    if recursive:
        yaml_files = list(directory.rglob('*.yaml')) + list(directory.rglob('*.yml'))
    else:
        yaml_files = list(directory.glob('*.yaml')) + list(directory.glob('*.yml'))

    for yaml_file in yaml_files:
        try:
            test_case = TestCase.from_yaml(str(yaml_file))
            test_cases.append(test_case)
        except Exception as e:
            logging.warning(f"Failed to load test case from {yaml_file}: {e}")

        return test_cases


def create_test_case_from_scan(
    name: str,
    sample_path: str,
    scan_result: Dict,
    description: str = "",
    tags: Optional[List[str]] = None,
    capture_disposition: bool = True,
    capture_flags: bool = True,
    capture_modules: bool = False,
    custom_assertions: Optional[List[Assertion]] = None
) -> TestCase:
    """
    Create a test case from an existing scan result.

    This is used by the web UI to generate test cases from interactive scans.

    Args:
        name: Name for the test case
        sample_path: Path to the sample file
        scan_result: The scan result dictionary
        description: Description of what the test validates
        tags: Tags for categorizing the test
        capture_disposition: Whether to assert on disposition
        capture_flags: Whether to assert on flags
        capture_modules: Whether to assert on modules run
        custom_assertions: Additional custom assertions to include

    Returns:
        A TestCase object ready to be saved
    """
    assertions = []

    if capture_disposition:
        disposition = get_value_at_path(scan_result, 'disposition')
        if disposition:
            assertions.append(Assertion(
                path='disposition',
                assertion_type=AssertionType.EQUALS,
                expected=disposition
            ))

    if capture_flags:
        flags = get_value_at_path(scan_result, 'flags')
        if flags:
            for flag in flags:
                assertions.append(Assertion(
                    path='flags',
                    assertion_type=AssertionType.CONTAINS,
                    expected=flag
                ))

    if capture_modules:
        modules = get_value_at_path(scan_result, 'modules')
        if modules:
            for module in modules:
                assertions.append(Assertion(
                    path='modules',
                    assertion_type=AssertionType.CONTAINS,
                    expected=module
                ))

    if custom_assertions:
        assertions.extend(custom_assertions)

    return TestCase(
        name=name,
        sample_path=sample_path,
        description=description,
        assertions=assertions,
        tags=tags or []
    )
