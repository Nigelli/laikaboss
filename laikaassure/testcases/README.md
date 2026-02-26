# Laika Assure Test Cases

This directory contains test case definitions for validating laikaboss scanning outcomes.

## Directory Structure

```
testcases/
├── samples/           # Sample files to scan (gitignored by default)
│   ├── email.eml
│   ├── document.pdf
│   └── ...
├── example_test.yaml  # Example test case definition
└── README.md          # This file
```

## Test Case Format

Test cases are defined in YAML files with the following structure:

```yaml
# Test case name (required)
name: suspicious_macro_email

# Sample file to scan (relative to this file or absolute path)
sample: samples/suspicious_macro.docm

# Description of what this test validates
description: "Word document with macro that should trigger VBA detection"

# Tags for filtering tests
tags:
  - email
  - critical
  - macros

# Whether this test is enabled (default: true)
enabled: true

# Assertions to validate against scan results
assertions:
  # Check disposition equals a specific value
  - path: disposition
    equals: Quarantine

  # Check that flags contain a specific value
  - path: flags
    contains: VBA_MACRO

  # Check that flags do NOT contain a value
  - path: flags
    not_contains: CLEAN

  # Check using regex pattern
  - path: metadata.SCAN_YARA.matches
    matches: "macro_.*"

  # Check that a field exists
  - path: metadata.EXPLODE_OLE
    exists: true

  # Check numeric comparisons
  - path: file_count
    greater_than: 1

  # Custom failure message
  - path: disposition
    equals: Quarantine
    message: "This document should be quarantined due to suspicious macros"
```

## Available Assertion Paths

### Convenience Paths

| Path | Description |
|------|-------------|
| `disposition` | Final disposition result (Accept, Quarantine, Reject) |
| `disposition_matches` | List of disposition rule matches |
| `flags` | Rolled up list of all flags from all objects |
| `modules` | List of modules run on root object |
| `all_modules` | List of all modules run on all objects |
| `file_count` | Number of objects in scan result |
| `content_types` | Content types of root object |
| `file_types` | File types of root object |

### Module Metadata Paths

Access specific module metadata using `metadata.MODULE_NAME.field`:

```yaml
- path: metadata.SCAN_YARA.matches
  contains: "suspicious_pattern"

- path: metadata.META_HASH.HASHES.md5
  equals: "d41d8cd98f00b204e9800998ecf8427e"

- path: metadata.DISPOSITIONER.Disposition.Result
  equals: "Quarantine"
```

### Root Object Paths

Access root object fields directly using `root.field`:

```yaml
- path: root.objectSize
  greater_than: 1000

- path: root.filename
  matches: ".*\\.exe$"
```

## Assertion Types

| Type | Description | Example |
|------|-------------|---------|
| `equals` | Exact match | `equals: Quarantine` |
| `contains` | Value is in list/string | `contains: MACRO` |
| `not_contains` | Value is NOT in list/string | `not_contains: CLEAN` |
| `matches` | Regex pattern match | `matches: "^suspicious_.*"` |
| `exists` | Field exists and is not null | `exists: true` |
| `not_exists` | Field does not exist | `not_exists: true` |
| `greater_than` | Numeric comparison | `greater_than: 100` |
| `less_than` | Numeric comparison | `less_than: 1000000` |

## Running Tests

### Using CLI

```bash
# Run all tests
assure.py --endpoint tcp://localhost:5558 --tests ./testcases/

# Run tests with specific tags
assure.py --endpoint tcp://localhost:5558 --tests ./testcases/ --tags critical

# Output as JSON (for CI)
assure.py --endpoint tcp://localhost:5558 --tests ./testcases/ --json
```

### Using Web UI

```bash
# Start the web server
assureserver.py --endpoint tcp://localhost:5558 --testcases ./testcases/

# Open http://localhost:5080 in browser
# Navigate to "Test Cases" page
# Click "Run All Tests"
```

## Creating Test Cases

### Via Web UI (Recommended)

1. Start the assure server
2. Go to the Scan page
3. Upload a file to scan
4. Review the results
5. Click "Save as Test Case"
6. Configure assertions and save

### Manually

1. Place sample file in `samples/` directory
2. Create a YAML file with test definition
3. Run tests to verify

## Best Practices

1. **Use descriptive names**: `phishing_email_with_url` not `test1`
2. **Add descriptions**: Explain what the test validates and why
3. **Use tags**: Categorize tests for selective running
4. **Keep samples minimal**: Use smallest file that triggers the behavior
5. **Test critical paths**: Focus on dispositions and flags that matter
6. **Version control YAML**: Keep test definitions in git, samples can be gitignored
