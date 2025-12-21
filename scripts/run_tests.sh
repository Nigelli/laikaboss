#!/bin/bash
#
# Laikaboss Test Runner
#
# Convenience script for running tests locally.
# This script provides easy access to different test configurations.
#
# Usage:
#   ./scripts/run_tests.sh [command]
#
# Commands:
#   unit        - Run unit tests only (fast, no external deps)
#   integration - Run integration tests (may need Redis/MinIO)
#   legacy      - Run legacy .lbtest files via laikatest.py
#   all         - Run all tests
#   coverage    - Run all tests with HTML coverage report
#   quick       - Run fast tests only (unit + basic checks)
#   watch       - Run tests in watch mode (requires pytest-watch)
#   help        - Show this help message
#
# Examples:
#   ./scripts/run_tests.sh unit
#   ./scripts/run_tests.sh coverage
#   ./scripts/run_tests.sh all

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Print colored message
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if pytest is installed
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        error "pytest is not installed. Install with: pip install pytest pytest-cov pytest-timeout"
        exit 1
    fi
}

# Run unit tests
run_unit_tests() {
    info "Running unit tests..."
    check_pytest
    pytest tests/unit/ -v \
        --timeout=60 \
        -m "unit or not integration" \
        "$@"
    success "Unit tests completed!"
}

# Run integration tests
run_integration_tests() {
    info "Running integration tests..."
    check_pytest
    pytest tests/integration/ -v \
        --timeout=300 \
        -m "integration or module" \
        "$@"
    success "Integration tests completed!"
}

# Run legacy .lbtest tests
run_legacy_tests() {
    info "Running legacy .lbtest tests..."
    if [ -f "laikatest.py" ]; then
        python laikatest.py tests/
        success "Legacy tests completed!"
    else
        error "laikatest.py not found"
        exit 1
    fi
}

# Run all tests
run_all_tests() {
    info "Running all tests..."
    check_pytest
    pytest tests/ -v \
        --timeout=300 \
        --cov=laikaboss \
        --cov-report=term \
        "$@"
    success "All tests completed!"
}

# Run tests with coverage report
run_coverage() {
    info "Running tests with coverage..."
    check_pytest
    pytest tests/ -v \
        --cov=laikaboss \
        --cov-report=html \
        --cov-report=term \
        --cov-report=xml \
        "$@"
    success "Coverage report generated!"
    info "HTML report: htmlcov/index.html"
    info "XML report: coverage.xml"
}

# Run quick tests
run_quick_tests() {
    info "Running quick tests..."
    check_pytest
    pytest tests/unit/ -v \
        --timeout=30 \
        -m "not slow" \
        -x \
        "$@"
    success "Quick tests completed!"
}

# Run tests in watch mode
run_watch_mode() {
    info "Running tests in watch mode..."
    if ! command -v ptw &> /dev/null; then
        warn "pytest-watch not installed. Installing..."
        pip install pytest-watch
    fi
    ptw tests/ -- -v --timeout=60
}

# Show help
show_help() {
    cat << EOF
Laikaboss Test Runner

Usage: $(basename "$0") [command] [pytest-options]

Commands:
  unit        Run unit tests only (fast, no external dependencies)
  integration Run integration tests (may require Redis/MinIO)
  legacy      Run legacy .lbtest files via laikatest.py
  all         Run all tests with basic coverage
  coverage    Run all tests with detailed coverage reports
  quick       Run fast tests only (skips slow tests, stops on first failure)
  watch       Run tests in watch mode (auto-rerun on file changes)
  help        Show this help message

Examples:
  $(basename "$0") unit                    # Run unit tests
  $(basename "$0") unit -k "test_scan"     # Run unit tests matching pattern
  $(basename "$0") coverage                # Generate coverage report
  $(basename "$0") all -x                  # Run all, stop on first failure
  $(basename "$0") integration -v          # Run integration tests verbosely

Environment Variables:
  REDIS_HOST     Redis host for integration tests (default: localhost)
  REDIS_PORT     Redis port for integration tests (default: 6379)
  MINIO_ENDPOINT MinIO endpoint for S3 tests (default: localhost:9000)

EOF
}

# Main command dispatcher
main() {
    local command="${1:-all}"
    shift 2>/dev/null || true

    case "$command" in
        unit)
            run_unit_tests "$@"
            ;;
        integration)
            run_integration_tests "$@"
            ;;
        legacy)
            run_legacy_tests "$@"
            ;;
        all)
            run_all_tests "$@"
            ;;
        coverage)
            run_coverage "$@"
            ;;
        quick)
            run_quick_tests "$@"
            ;;
        watch)
            run_watch_mode "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
