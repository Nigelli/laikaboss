#!/usr/bin/env python3
"""
Script to remove Python 2 future library compatibility imports from Python 3 code.

This script removes:
- from __future__ import ... (all variants)
- from future import standard_library
- standard_library.install_aliases()
- from builtins import ... (str, bytes, object, int, etc.)
- from past.utils import old_div
"""

import re
import sys
from pathlib import Path


def remove_future_imports(file_path):
    """Remove future library imports from a Python file."""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        original_content = content

    # Track what we removed for reporting
    removed_lines = []

    # Split into lines for processing
    lines = content.split('\n')
    new_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        # Skip if previous line told us to
        if skip_next:
            skip_next = False
            continue

        # Check if this line should be removed
        should_remove = False

        # Pattern 1: from __future__ import ...
        if re.match(r'^\s*from\s+__future__\s+import\s+', line):
            should_remove = True
            removed_lines.append(line.strip())

        # Pattern 2: from future import standard_library
        elif re.match(r'^\s*from\s+future\s+import\s+standard_library', line):
            should_remove = True
            removed_lines.append(line.strip())
            # Check if next line is standard_library.install_aliases()
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if re.match(r'^\s*standard_library\.install_aliases\(\)', next_line):
                    skip_next = True
                    removed_lines.append(next_line.strip())

        # Pattern 3: from builtins import ...
        elif re.match(r'^\s*from\s+builtins\s+import\s+', line):
            should_remove = True
            removed_lines.append(line.strip())

        # Pattern 4: from past.utils import old_div (or other past imports)
        elif re.match(r'^\s*from\s+past\.', line):
            should_remove = True
            removed_lines.append(line.strip())

        # Keep the line if it's not a future import
        if not should_remove:
            new_lines.append(line)
        # If removing, check if we need to preserve blank lines for readability
        # (don't create double blank lines)
        else:
            # If previous line was blank and next line will be blank, skip this blank
            pass

    # Rejoin lines
    new_content = '\n'.join(new_lines)

    # Clean up any double blank lines at the start of file (after removing imports)
    new_content = re.sub(r'^\n\n+', '\n', new_content)

    # Only write if content changed
    if new_content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True, removed_lines
    else:
        return False, []


def find_old_div_usage(file_path):
    """Find usage of old_div() function that needs to be replaced."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find old_div(a, b) patterns
    pattern = r'old_div\s*\([^)]+\)'
    matches = re.findall(pattern, content)
    return matches


def main():
    """Main function to process all Python files."""

    # Find all Python files with future imports
    root = Path('/home/user/laikaboss')

    # Files to process (from grep results)
    python_files = [
        'laikaboss/util.py',
        'laikaboss/test.py',
        'laikarest/storage/storage_helper.py',
        'laikarest/routes/info.py',
        'laikaboss/xyz.py',
        'laikaboss/postgres_adapter.py',
        'laikaboss/modules/meta_tiff.py',
        'rediscloudscan.py',
        'laikatest.py',
        'laikamilter.py',
        'laikaboss/storage_utils.py',
        'laikaboss/modules/meta_httpformget.py',
        'laikaboss/modules/explode_rtf.py',
        'laikaboss/extras/extra_util.py',
        'laikaboss/clientLib.py',
        'laikaboss/extras/dictParser.py',
        'laikaboss/lbconfigparser.py',
        'laikaboss/modules/scan_html.py',
        'laikaboss/modules/submit_storage_s3.py',
        'laikaboss/objectmodel.py',
        'laikad.py',
        'cloudscan.py',
        'laika.py',
        'laikaboss/config.py',
        'laikaboss/dispatch.py',
        'laikaboss/extras/macho_util.py',
        'laikaboss/extras/text_util.py',
        'laikaboss/extras/tiff_util.py',
        'laikaboss/modules/dispositioner.py',
        'laikaboss/modules/explode_gzip.py',
        'laikaboss/modules/explode_hexascii.py',
        'laikaboss/modules/explode_iso.py',
        'laikaboss/modules/explode_macro.py',
        'laikaboss/modules/explode_multipartform.py',
        'laikaboss/modules/explode_ole.py',
        'laikaboss/modules/explode_pdf_text.py',
        'laikaboss/modules/explode_pdf.py',
        'laikaboss/modules/explode_pkcs7.py',
        'laikaboss/modules/explode_plist.py',
        'laikaboss/modules/explode_qr_code.py',
        'laikaboss/modules/explode_rar2.py',
        'laikaboss/modules/explode_swf.py',
        'laikaboss/modules/explode_tar.py',
        'laikaboss/modules/explode_tnef.py',
        'laikaboss/modules/explode_zip.py',
        'laikaboss/modules/log_fluent.py',
        'laikaboss/modules/meta_cryptocurrency.py',
        'laikaboss/modules/meta_email.py',
        'laikaboss/modules/meta_httpformpost.py',
        'laikaboss/modules/meta_iso.py',
        'laikaboss/modules/meta_lnk.py',
        'laikaboss/modules/meta_ole.py',
        'laikaboss/modules/meta_pe.py',
        'laikaboss/modules/meta_zip.py',
        'laikaboss/redis_cache.py',
        'laikaboss/redisClientLib.py',
        'laikaboss/si_module.py',
        'laikacollector.py',
        'laikaconf.py',
        'laikadq.py',
        'laikamail.py',
        'laikaq-cli.py',
        'laikarest/authentication/auth.py',
        'laikarest/routes/__init__.py',
        'laikarest/routes/storage.py',
        'laikarest/utils.py',
        'submitstoraged.py',
    ]

    modified_count = 0
    old_div_files = []

    print("=" * 80)
    print("Removing future library imports from Python 3 codebase")
    print("=" * 80)
    print()

    for rel_path in python_files:
        file_path = root / rel_path

        if not file_path.exists():
            print(f"⚠️  SKIP: {rel_path} (file not found)")
            continue

        # Check for old_div usage before removing
        old_div_matches = find_old_div_usage(file_path)
        if old_div_matches:
            old_div_files.append((rel_path, old_div_matches))

        # Remove future imports
        modified, removed = remove_future_imports(file_path)

        if modified:
            modified_count += 1
            print(f"✓ {rel_path}")
            for line in removed:
                print(f"    - {line}")
        else:
            print(f"  {rel_path} (no changes)")

    print()
    print("=" * 80)
    print(f"Summary: Modified {modified_count} of {len(python_files)} files")
    print("=" * 80)

    if old_div_files:
        print()
        print("⚠️  WARNING: The following files use old_div() and need manual review:")
        print()
        for rel_path, matches in old_div_files:
            print(f"  {rel_path}:")
            for match in matches:
                print(f"    - {match}")
        print()
        print("These will need to be replaced with standard Python 3 division (/).")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
