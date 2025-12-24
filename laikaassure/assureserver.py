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
Laika Assure Server - Web UI for Test Case Creation

A simple Flask application that provides a web interface for:
- Scanning files and viewing results
- Creating test cases from scan results
- Managing test case collections
- Running test suites

Usage:
    # Start server with ZMQ backend
    assureserver.py --endpoint tcp://localhost:5558

    # Start server with REST backend
    assureserver.py --rest http://localhost:5000

    # Specify port and test case directory
    assureserver.py --endpoint tcp://localhost:5558 --port 8080 --testcases ./mytests
"""

import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory

# Add parent directory to path for imports when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from laikaassure.assurelib import (
    TestCase,
    TestRunner,
    ZMQScanClient,
    RESTScanClient,
    load_test_cases,
    create_test_case_from_scan,
    get_value_at_path,
    Assertion,
    AssertionType,
)

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Global configuration (set by command line args)
config = {
    'client': None,
    'testcases_dir': None,
    'samples_dir': None,
}


@app.route('/')
def index():
    """Main page with scan interface."""
    return render_template('index.html')


@app.route('/tests')
def tests_page():
    """Test case management page."""
    return render_template('tests.html')


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """
    Scan an uploaded file and return the result.

    Accepts multipart form data with a 'file' field.
    Returns JSON scan result.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save to temp file
    temp_dir = tempfile.mkdtemp()
    try:
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)

        # Scan the file
        client = config['client']
        if client is None:
            return jsonify({'error': 'Scanner not configured'}), 500

        result = client.scan(temp_path, filename=file.filename)

        # Add convenience fields for UI
        result['_ui'] = {
            'disposition': get_value_at_path(result, 'disposition'),
            'disposition_matches': get_value_at_path(result, 'disposition_matches'),
            'flags': get_value_at_path(result, 'flags'),
            'modules': get_value_at_path(result, 'modules'),
            'file_count': get_value_at_path(result, 'file_count'),
        }

        return jsonify(result)

    except Exception as e:
        logging.exception("Scan error")
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route('/api/testcase', methods=['POST'])
def api_create_testcase():
    """
    Create a test case from a scan result.

    Expects JSON body with:
    - name: Test case name
    - description: Optional description
    - tags: Optional list of tags
    - file: Base64 encoded file content or filename from previous upload
    - filename: Original filename
    - scan_result: The scan result to base assertions on
    - assertions: List of assertion configurations
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required = ['name', 'filename', 'scan_result']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        # Parse assertions from request
        assertions = []
        for assertion_data in data.get('assertions', []):
            assertion_type = AssertionType(assertion_data.get('type', 'equals'))
            assertions.append(Assertion(
                path=assertion_data['path'],
                assertion_type=assertion_type,
                expected=assertion_data.get('expected'),
                message=assertion_data.get('message')
            ))

        # If no explicit assertions, create defaults from scan result
        if not assertions:
            # Create test case with default captures
            test_case = create_test_case_from_scan(
                name=data['name'],
                sample_path=data['filename'],
                scan_result=data['scan_result'],
                description=data.get('description', ''),
                tags=data.get('tags', []),
                capture_disposition=data.get('capture_disposition', True),
                capture_flags=data.get('capture_flags', True),
                capture_modules=data.get('capture_modules', False),
            )
        else:
            test_case = TestCase(
                name=data['name'],
                sample_path=data['filename'],
                description=data.get('description', ''),
                assertions=assertions,
                tags=data.get('tags', [])
            )

        # Save the sample file if provided as base64
        if 'file_content' in data:
            import base64
            samples_dir = config['samples_dir']
            os.makedirs(samples_dir, exist_ok=True)

            sample_path = os.path.join(samples_dir, data['filename'])

            # Handle filename collision
            if os.path.exists(sample_path):
                base, ext = os.path.splitext(data['filename'])
                sample_path = os.path.join(samples_dir, f"{base}_{uuid.uuid4().hex[:8]}{ext}")

            with open(sample_path, 'wb') as f:
                f.write(base64.b64decode(data['file_content']))

            test_case.sample_path = sample_path

        # Save test case YAML
        testcases_dir = config['testcases_dir']
        os.makedirs(testcases_dir, exist_ok=True)

        # Generate safe filename
        safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in data['name'])
        yaml_path = os.path.join(testcases_dir, f"{safe_name}.yaml")

        # Handle filename collision
        if os.path.exists(yaml_path):
            yaml_path = os.path.join(testcases_dir, f"{safe_name}_{uuid.uuid4().hex[:8]}.yaml")

        with open(yaml_path, 'w') as f:
            f.write(test_case.to_yaml())

        return jsonify({
            'success': True,
            'path': yaml_path,
            'yaml': test_case.to_yaml()
        })

    except Exception as e:
        logging.exception("Error creating test case")
        return jsonify({'error': str(e)}), 500


@app.route('/api/testcases', methods=['GET'])
def api_list_testcases():
    """List all test cases."""
    try:
        testcases_dir = config['testcases_dir']
        if not os.path.exists(testcases_dir):
            return jsonify({'test_cases': []})

        test_cases = load_test_cases(testcases_dir)

        return jsonify({
            'test_cases': [
                {
                    'name': tc.name,
                    'description': tc.description,
                    'sample': os.path.basename(tc.sample_path),
                    'tags': tc.tags,
                    'enabled': tc.enabled,
                    'assertion_count': len(tc.assertions),
                }
                for tc in test_cases
            ]
        })

    except Exception as e:
        logging.exception("Error listing test cases")
        return jsonify({'error': str(e)}), 500


@app.route('/api/testcases/run', methods=['POST'])
def api_run_testcases():
    """Run test cases and return results."""
    data = request.get_json() or {}
    tags = data.get('tags')

    try:
        testcases_dir = config['testcases_dir']
        if not os.path.exists(testcases_dir):
            return jsonify({'error': 'No test cases directory'}), 404

        test_cases = load_test_cases(testcases_dir)

        if not test_cases:
            return jsonify({'error': 'No test cases found'}), 404

        runner = TestRunner(config['client'])
        results = runner.run_tests(test_cases, tags=tags)

        return jsonify({
            'summary': {
                'total': len(results),
                'passed': sum(1 for r in results if r.passed),
                'failed': sum(1 for r in results if not r.passed),
            },
            'results': [
                {
                    'name': r.test_case.name,
                    'passed': r.passed,
                    'duration_ms': r.duration_ms,
                    'error': r.error,
                    'assertions': [
                        {
                            'path': ar.assertion.path,
                            'passed': ar.passed,
                            'message': ar.message,
                            'actual': ar.actual_value,
                            'expected': ar.assertion.expected,
                        }
                        for ar in r.assertion_results
                    ]
                }
                for r in results
            ]
        })

    except Exception as e:
        logging.exception("Error running test cases")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'client_type': type(config['client']).__name__ if config['client'] else None,
        'testcases_dir': config['testcases_dir'],
    })


def main():
    parser = argparse.ArgumentParser(
        description='Laika Assure Server - Web UI for test case creation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    # Server options
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5080,
        help='Port to listen on (default: 5080)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )

    # Storage options
    parser.add_argument(
        '--testcases', '-t',
        default='./testcases',
        help='Directory for test case YAML files (default: ./testcases)'
    )
    parser.add_argument(
        '--samples', '-s',
        help='Directory for sample files (default: <testcases>/samples)'
    )

    # Connection options
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Scan timeout in seconds (default: 30)'
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
        help='Enable debug mode'
    )

    args = parser.parse_args()

    # Setup logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Create appropriate client
    try:
        if args.endpoint:
            config['client'] = ZMQScanClient(
                broker_url=args.endpoint,
                timeout=args.timeout * 1000
            )
            print(f"Using ZMQ endpoint: {args.endpoint}")
        else:
            config['client'] = RESTScanClient(
                base_url=args.rest,
                timeout=args.timeout,
                verify_ssl=not args.no_verify_ssl
            )
            print(f"Using REST endpoint: {args.rest}")
    except ImportError as e:
        print(f"Error: {e}")
        return 1

    # Setup directories
    config['testcases_dir'] = os.path.abspath(args.testcases)
    config['samples_dir'] = os.path.abspath(args.samples) if args.samples else os.path.join(config['testcases_dir'], 'samples')

    os.makedirs(config['testcases_dir'], exist_ok=True)
    os.makedirs(config['samples_dir'], exist_ok=True)

    print(f"Test cases directory: {config['testcases_dir']}")
    print(f"Samples directory: {config['samples_dir']}")
    print(f"Starting server on http://{args.host}:{args.port}")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
