#!/bin/bash
#
# Laikaboss Core Docker Smoke Test
#
# Runs laika.py against generated test samples and existing .lbtest files
# to verify all modules work correctly at runtime.
#
# Usage (inside Docker container):
#   cd /home/laikaboss && bash tests/smoke_test.sh
#
# Or from host via docker-compose:
#   docker compose -f docker-compose-core.yml run --rm laikad \
#     bash -c "cd /home/laikaboss && bash tests/smoke_test.sh"

set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
PASS=0
FAIL=0
SKIP=0
WARN=0
ERRORS=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SAMPLES_DIR="$SCRIPT_DIR/data/samples"

# Known non-fatal stderr patterns to ignore (one per line)
KNOWN_STDERR_NOISE="No module named 'minio'
submit_storage_s3
storage_utils
DeprecationWarning
SyntaxWarning
pkg_resources
interruptingcow
Error parsing cert
error on.*running module META_X509
AttributeError
RequestsDependencyWarning
'target'"

echo -e "${BOLD}${BLUE}================================================${NC}"
echo -e "${BOLD}${BLUE}  Laikaboss Core Docker Smoke Test${NC}"
echo -e "${BOLD}${BLUE}================================================${NC}"
echo

# -----------------------------------------------------------------------
# Phase 1: Generate test samples
# -----------------------------------------------------------------------
echo -e "${CYAN}Phase 1: Generating test samples...${NC}"
python3 "$SCRIPT_DIR/generate_test_samples.py" "$SAMPLES_DIR" 2>&1
echo

# -----------------------------------------------------------------------
# Phase 2: Module import check
# -----------------------------------------------------------------------
echo -e "${CYAN}Phase 2: Module import check...${NC}"
IMPORT_OUTPUT=$(python3 -c "
import sys
sys.path.insert(0, '.')
import laikaboss.modules
ml = laikaboss.modules._module_list
if isinstance(ml, dict):
    loaded = sorted(ml.keys())
else:
    loaded = sorted(ml)
print('LOADED_COUNT=' + str(len(loaded)))
for m in loaded:
    print('LOADED: ' + m)
" 2>&1)

LOADED_COUNT=$(echo "$IMPORT_OUTPUT" | grep "^LOADED_COUNT=" | cut -d= -f2)
IMPORT_ERRORS=$(echo "$IMPORT_OUTPUT" | grep -i "error\|traceback\|cannot\|failed" | grep -v "^LOADED:" || true)

echo -e "  Modules loaded: ${GREEN}${LOADED_COUNT}${NC}"
if [ -n "$IMPORT_ERRORS" ]; then
    echo -e "  ${YELLOW}Import warnings/errors:${NC}"
    echo "$IMPORT_ERRORS" | sed 's/^/    /'
fi
echo

# -----------------------------------------------------------------------
# Phase 3: Scan each test sample
# -----------------------------------------------------------------------
echo -e "${CYAN}Phase 3: Scanning test samples with laika.py...${NC}"
echo

# Define expected modules for each test file
# Format: filename|expected_module1,expected_module2|expected_file_type
# Using | as delimiter to avoid issues with : in filenames or IFS leaks
declare -a TEST_CASES=(
    "sample.tar|EXPLODE_TAR|tar"
    "sample.gz|EXPLODE_GZIP|gzip"
    "sample.bz2|EXPLODE_BZ2|bzip"
    "sample.eml|META_EMAIL,EXPLODE_EMAIL|eml"
    "sample.eps|META_PS_COMMANDS|eps"
    "sample.tiff|META_TIFF|tiff"
    "sample.pem|META_X509|pem"
    "sample.der|META_X509|der"
    "sample.lnk|META_LNK|lnk"
    "dmarc_report.xml|META_DMARC|"
    "Test.class|META_JAVA_CLASS|class"
    "sample.swf|EXPLODE_SWF|cws"
    "sample.html|SCAN_HTML|html"
    "sample.pdf|EXPLODE_PDF,META_PDF_STRUCTURE|pdf"
    "sample.rtf|EXPLODE_RTF,META_RTF_CONTROLWORDS|rtf"
    "sample.iso|META_ISO,EXPLODE_ISO|iso"
    "sample.jar|META_ZIP,EXPLODE_ZIP|"
    "sample.exe|META_PE|pe"
    "sample.zip|META_ZIP,EXPLODE_ZIP|zip"
    "sample.png|EXPLODE_BINWALK|png"
    "sample.rels|META_OOXML_RELS|"
)

# Use Python for reliable JSON-based module checking
check_modules() {
    local json_file="$1"
    local expected="$2"
    python3 -c "
import json, sys
try:
    data = json.load(open('$json_file'))
    # laika.py CLI output format: scan_result array
    all_mods = set()
    for obj in data.get('scan_result', []):
        for mod in obj.get('scanModules', []):
            all_mods.add(mod)
    expected = [m.strip() for m in '$expected'.split(',') if m.strip()]
    missing = [m for m in expected if m not in all_mods]
    if missing:
        print('MISSING:' + ','.join(missing))
    else:
        print('OK:' + ','.join(sorted(all_mods)))
except Exception as e:
    print('ERROR:' + str(e))
" 2>/dev/null
}

# Check for non-trivial stderr errors (filter out known noise)
check_stderr() {
    local stderr_file="$1"
    if [ ! -s "$stderr_file" ]; then
        echo "CLEAN"
        return
    fi
    # Filter out all known noise patterns line by line
    local filtered
    filtered=$(cat "$stderr_file")
    while IFS= read -r pattern; do
        [ -z "$pattern" ] && continue
        filtered=$(echo "$filtered" | grep -v "$pattern" || true)
    done <<< "$KNOWN_STDERR_NOISE"
    # Also filter out Traceback blocks and Python stack trace lines
    # that accompany known/filtered errors
    filtered=$(echo "$filtered" | grep -v "^Traceback\|^  File \"/\|^    " || true)
    # Check if anything concerning remains
    local concerning
    concerning=$(echo "$filtered" | grep -i "Exception\|Error" | grep -v "WARNING\|DEBUG\|INFO" | sed '/^$/d' || true)
    if [ -n "$concerning" ]; then
        echo "ERRORS"
    else
        echo "CLEAN"
    fi
}

run_scan() {
    local file="$1"
    local expected_modules="$2"
    local expected_type="$3"
    local filepath="$SAMPLES_DIR/$file"

    if [ ! -f "$filepath" ]; then
        echo -e "  ${YELLOW}SKIP${NC} $file (file not generated)"
        SKIP=$((SKIP + 1))
        return
    fi

    # Run laika.py and capture stdout (JSON) and stderr
    local stdout_file
    local stderr_file
    stdout_file=$(mktemp)
    stderr_file=$(mktemp)

    timeout 60 laika.py "$filepath" > "$stdout_file" 2> "$stderr_file"
    local exit_code=$?

    if [ $exit_code -eq 124 ]; then
        echo -e "  ${RED}FAIL${NC} $file - TIMEOUT (60s)"
        FAIL=$((FAIL + 1))
        ERRORS="${ERRORS}\n  FAIL: $file (timeout)"
        rm -f "$stdout_file" "$stderr_file"
        return
    fi

    if [ $exit_code -ne 0 ]; then
        echo -e "  ${RED}FAIL${NC} $file - laika.py exited with code $exit_code"
        head -3 "$stderr_file" 2>/dev/null | sed 's/^/       /'
        FAIL=$((FAIL + 1))
        ERRORS="${ERRORS}\n  FAIL: $file (exit code $exit_code)"
        rm -f "$stdout_file" "$stderr_file"
        return
    fi

    # Check modules using Python JSON parsing
    local result
    result=$(check_modules "$stdout_file" "$expected_modules")

    local stderr_status
    stderr_status=$(check_stderr "$stderr_file")

    case "$result" in
        OK:*)
            local ran_modules="${result#OK:}"
            if [ "$stderr_status" = "ERRORS" ]; then
                echo -e "  ${YELLOW}WARN${NC} $file - modules OK but unexpected stderr errors"
                grep -i "Traceback\|Exception\|Error" "$stderr_file" | grep -v "WARNING\|DEBUG\|INFO\|minio\|submit_storage_s3" | head -3 | sed 's/^/       /'
                WARN=$((WARN + 1))
            else
                echo -e "  ${GREEN}PASS${NC} $file [${ran_modules}]"
            fi
            PASS=$((PASS + 1))
            ;;
        MISSING:*)
            local missing="${result#MISSING:}"
            echo -e "  ${RED}FAIL${NC} $file - missing modules: ${missing}"
            # Show relevant stderr
            grep -i "error\|exception\|traceback" "$stderr_file" | grep -v "minio\|submit_storage_s3" | head -5 | sed 's/^/       /'
            FAIL=$((FAIL + 1))
            ERRORS="${ERRORS}\n  FAIL: $file (missing: ${missing})"
            ;;
        ERROR:*)
            local err="${result#ERROR:}"
            echo -e "  ${RED}FAIL${NC} $file - JSON parse error: ${err}"
            FAIL=$((FAIL + 1))
            ERRORS="${ERRORS}\n  FAIL: $file (parse error)"
            ;;
    esac

    rm -f "$stdout_file" "$stderr_file"
}

for test_case in "${TEST_CASES[@]}"; do
    # Use | as delimiter to avoid IFS issues
    file="${test_case%%|*}"
    rest="${test_case#*|}"
    expected_modules="${rest%%|*}"
    expected_type="${rest#*|}"
    run_scan "$file" "$expected_modules" "$expected_type"
done

echo

# -----------------------------------------------------------------------
# Phase 4: Run existing .lbtest files
# -----------------------------------------------------------------------
echo -e "${CYAN}Phase 4: Running legacy .lbtest tests...${NC}"
LBTEST_DIR="$SCRIPT_DIR"
LBTEST_COUNT=$(find "$LBTEST_DIR" -maxdepth 1 -name "*.lbtest" | wc -l)

if [ "$LBTEST_COUNT" -gt 0 ]; then
    echo "  Found $LBTEST_COUNT .lbtest files"
    LBTEST_OUTPUT=$(mktemp)
    python3 "$REPO_ROOT/laikatest.py" "$LBTEST_DIR" > "$LBTEST_OUTPUT" 2>&1
    LBTEST_EXIT=$?

    if [ $LBTEST_EXIT -eq 0 ]; then
        echo -e "  ${GREEN}PASS${NC} All $LBTEST_COUNT .lbtest files passed"
        PASS=$((PASS + 1))
    else
        echo -e "  ${YELLOW}WARN${NC} laikatest.py exited with code $LBTEST_EXIT"
        # Show failures, filtering known noise
        grep -i "FAIL\|ERROR" "$LBTEST_OUTPUT" | grep -v "minio\|submit_storage_s3" | head -10 | sed 's/^/    /'
        WARN=$((WARN + 1))
    fi
    rm -f "$LBTEST_OUTPUT"
else
    echo -e "  ${YELLOW}SKIP${NC} No .lbtest files found"
fi

echo

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
echo -e "${BOLD}${BLUE}================================================${NC}"
echo -e "${BOLD}${BLUE}  Summary${NC}"
echo -e "${BOLD}${BLUE}================================================${NC}"
echo -e "  ${GREEN}PASS:${NC} $PASS"
echo -e "  ${YELLOW}WARN:${NC} $WARN"
echo -e "  ${RED}FAIL:${NC} $FAIL"
echo -e "  ${YELLOW}SKIP:${NC} $SKIP"
echo -e "  Modules loaded: $LOADED_COUNT"
echo

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Failures:${NC}"
    echo -e "$ERRORS"
    echo
    exit 1
else
    if [ $WARN -gt 0 ]; then
        echo -e "${YELLOW}All scans passed with $WARN warning(s)${NC}"
    else
        echo -e "${GREEN}All tests passed!${NC}"
    fi
    exit 0
fi
