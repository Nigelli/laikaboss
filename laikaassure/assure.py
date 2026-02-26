#!/usr/bin/env python3
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
Laika Assure - CLI Tool

Run validation test cases against a laikaboss endpoint to verify
expected scanning outcomes before deploying to production.

Usage:
    # Run all tests against ZMQ endpoint
    assure.py --endpoint tcp://staging:5558 --tests ./testcases/

    # Run tests with specific tags
    assure.py --endpoint tcp://staging:5558 --tests ./testcases/ --tags email,critical

    # Run against REST endpoint
    assure.py --rest http://staging:5000 --tests ./testcases/

    # Output results as JSON
    assure.py --endpoint tcp://localhost:5558 --tests ./testcases/ --json

    # Scan a single file (no assertions, just show result)
    assure.py --endpoint tcp://localhost:5558 --scan ./sample.eml
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from laikaassure.assurelib import (
    TestCase,
    TestResult,
    TestRunner,
    ZMQScanClient,
    RESTScanClient,
    load_test_cases,
    get_value_at_path,
)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        cls.GREEN = ''
        cls.RED = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.BOLD = ''
        cls.RESET = ''


def print_result_summary(results: List[TestResult], verbose: bool = False):
    """Print a human-readable summary of test results."""
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print()
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Results{Colors.RESET}")
    print(f"{'=' * 60}")
    print()

    for result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result.passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  [{status}] {result.test_case.name} ({result.duration_ms:.0f}ms)")

        if result.error:
            print(f"         {Colors.RED}Error: {result.error}{Colors.RESET}")

        if not result.passed or verbose:
            for ar in result.assertion_results:
                if not ar.passed:
                    print(f"         {Colors.RED}- {ar.message}{Colors.RESET}")
                elif verbose:
                    print(f"         {Colors.GREEN}- {ar.assertion.path}: OK{Colors.RESET}")

        if verbose and result.test_case.description:
            print(f"         Description: {result.test_case.description}")

    print()
    print(f"{'=' * 60}")

    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}All {passed} tests passed!{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}{failed} of {len(results)} tests failed{Colors.RESET}")

    print(f"{'=' * 60}")
    print()


def print_json_results(results: List[TestResult]):
    """Print results as JSON."""
    output = {
        'summary': {
            'total': len(results),
            'passed': sum(1 for r in results if r.passed),
            'failed': sum(1 for r in results if not r.passed),
        },
        'results': []
    }

    for result in results:
        result_data = {
            'name': result.test_case.name,
            'passed': result.passed,
            'duration_ms': result.duration_ms,
            'error': result.error,
            'assertions': []
        }

        for ar in result.assertion_results:
            result_data['assertions'].append({
                'path': ar.assertion.path,
                'passed': ar.passed,
                'message': ar.message,
                'actual': ar.actual_value,
                'expected': ar.assertion.expected,
            })

        output['results'].append(result_data)

    print(json.dumps(output, indent=2, default=str))


def scan_single_file(client, file_path: str, output_json: bool = False):
    """Scan a single file and display the result."""
    print(f"Scanning: {file_path}")
    print()

    try:
        result = client.scan(file_path)

        if output_json:
            print(json.dumps(result, indent=2))
        else:
            # Pretty print key information
            disposition = get_value_at_path(result, 'disposition')
            flags = get_value_at_path(result, 'flags')
            modules = get_value_at_path(result, 'modules')
            file_count = get_value_at_path(result, 'file_count')

            print(f"{Colors.BOLD}Scan Result:{Colors.RESET}")
            print(f"  Disposition: {Colors.BLUE}{disposition}{Colors.RESET}")
            print(f"  Flags: {flags}")
            print(f"  Modules: {modules}")
            print(f"  Objects scanned: {file_count}")

            # Show disposition matches if any
            matches = get_value_at_path(result, 'disposition_matches')
            if matches:
                print(f"  Disposition matches: {matches}")

            print()
            print(f"{Colors.YELLOW}Use --json to see full scan result{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}Error scanning file: {e}{Colors.RESET}")
        return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Laika Assure - Validate laikaboss scanning outcomes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests against ZMQ endpoint (laikad)
  %(prog)s --endpoint tcp://staging:5558 --tests ./testcases/

  # Run tests with specific tags
  %(prog)s --endpoint tcp://staging:5558 --tests ./testcases/ --tags email,critical

  # Run against REST endpoint (laikarestd)
  %(prog)s --rest http://staging:5000 --tests ./testcases/

  # Scan a single file (no assertions)
  %(prog)s --endpoint tcp://localhost:5558 --scan ./sample.eml

  # Output results as JSON (for CI integration)
  %(prog)s --endpoint tcp://localhost:5558 --tests ./testcases/ --json
        """
    )

    # Endpoint options (mutually exclusive)
    endpoint_group = parser.add_mutually_exclusive_group(required=True)
    endpoint_group.add_argument(
        '--endpoint', '-e',
        help='ZMQ broker URL (e.g., tcp://localhost:5558)'
    )
    endpoint_group.add_argument(
        '--rest', '-r',
        help='REST API base URL (e.g., http://localhost:5000)'
    )

    # Mode options (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--tests', '-t',
        help='Directory containing test case YAML files'
    )
    mode_group.add_argument(
        '--scan', '-s',
        help='Scan a single file (no assertions, just show result)'
    )

    # Filter options
    parser.add_argument(
        '--tags',
        help='Comma-separated list of tags to filter tests'
    )

    # Output options
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output including passing assertions'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    # Connection options
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Timeout in seconds (default: 30)'
    )
    parser.add_argument(
        '--no-verify-ssl',
        action='store_true',
        help='Disable SSL verification for REST endpoints'
    )

    # Debug options
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Setup logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Disable colors if requested or not a TTY
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Create appropriate client
    try:
        if args.endpoint:
            client = ZMQScanClient(
                broker_url=args.endpoint,
                timeout=args.timeout * 1000  # Convert to ms
            )
        else:
            client = RESTScanClient(
                base_url=args.rest,
                timeout=args.timeout,
                verify_ssl=not args.no_verify_ssl
            )
    except ImportError as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return 1

    # Single file scan mode
    if args.scan:
        return scan_single_file(client, args.scan, output_json=args.json)

    # Test suite mode
    if not os.path.isdir(args.tests):
        print(f"{Colors.RED}Error: Test directory not found: {args.tests}{Colors.RESET}")
        return 1

    # Load test cases
    test_cases = load_test_cases(args.tests)

    if not test_cases:
        print(f"{Colors.YELLOW}No test cases found in {args.tests}{Colors.RESET}")
        return 0

    # Parse tags filter
    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(',')]

    # Run tests
    runner = TestRunner(client)

    if not args.json:
        print(f"{Colors.BOLD}Laika Assure{Colors.RESET}")
        print(f"Endpoint: {args.endpoint or args.rest}")
        print(f"Test directory: {args.tests}")
        print(f"Test cases found: {len(test_cases)}")
        if tags:
            print(f"Filtering by tags: {tags}")
        print()
        print("Running tests...")

    results = runner.run_tests(test_cases, tags=tags)

    # Output results
    if args.json:
        print_json_results(results)
    else:
        print_result_summary(results, verbose=args.verbose)

    # Return exit code based on results
    failed = sum(1 for r in results if not r.passed)
    return 1 if failed > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
