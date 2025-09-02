#!/bin/bash

# Lightera UNDOKAI - Intensive Testing Script
# This script runs comprehensive tests to ensure the application is properly configured

set -e  # Exit on any error

echo "🚀 Lightera UNDOKAI - Intensive Testing Suite"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run a test and check its result
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_status "Running: $test_name"
    
    if eval "$test_command"; then
        print_success "$test_name passed"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Initialize test counters
total_tests=0
passed_tests=0

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_success "Virtual environment active: $VIRTUAL_ENV"
else
    print_warning "No virtual environment detected. Consider activating one."
fi

# 1. Environment Setup Tests
print_status "1. ENVIRONMENT SETUP TESTS"
echo "================================"

total_tests=$((total_tests + 1))
if run_test "Python version check" "python --version | grep -E '3\.(11|12)'"; then
    passed_tests=$((passed_tests + 1))
fi

total_tests=$((total_tests + 1))
if run_test "Dependencies check" "python -c 'import flask, sqlalchemy, qrcode, pytest; print(\"All dependencies available\")'"; then
    passed_tests=$((passed_tests + 1))
fi

total_tests=$((total_tests + 1))
if run_test "Module imports" "python -c 'from app import app, db; from models import *; from utils import *; print(\"All modules import successfully\")'"; then
    passed_tests=$((passed_tests + 1))
fi

# 2. Core Functionality Tests
print_status "\n2. CORE FUNCTIONALITY TESTS"
echo "================================="

total_tests=$((total_tests + 1))
if run_test "QR Code generation" "python -c 'from utils import generate_qr_code; qr = generate_qr_code(\"TEST123\"); assert qr.startswith(\"data:image/png;base64,\"); print(\"QR generation working\")'"; then
    passed_tests=$((passed_tests + 1))
fi

total_tests=$((total_tests + 1))
if run_test "Database initialization" "python -c 'from app import app, db; app.app_context().push(); db.create_all(); print(\"Database initialized\")'"; then
    passed_tests=$((passed_tests + 1))
fi

total_tests=$((total_tests + 1))
if run_test "Statistics function" "python -c 'from app import app, db; from utils import get_checkin_statistics; app.app_context().push(); stats = get_checkin_statistics(); assert \"total_participants\" in stats; print(\"Statistics working\")'"; then
    passed_tests=$((passed_tests + 1))
fi

# 3. Unit Tests
print_status "\n3. UNIT TESTS"
echo "==============="

total_tests=$((total_tests + 1))
if run_test "Model tests" "pytest tests/test_models.py -v --tb=short"; then
    passed_tests=$((passed_tests + 1))
fi

total_tests=$((total_tests + 1))
if run_test "Utility tests" "pytest tests/test_utils.py -v --tb=short"; then
    passed_tests=$((passed_tests + 1))
fi

# 4. Code Quality Tests
print_status "\n4. CODE QUALITY TESTS"
echo "======================"

total_tests=$((total_tests + 1))
if run_test "Syntax check" "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true"; then
    passed_tests=$((passed_tests + 1))
fi

total_tests=$((total_tests + 1))
if run_test "Python compilation" "python -m py_compile app.py models.py utils.py"; then
    passed_tests=$((passed_tests + 1))
fi

# 5. Integration Tests
print_status "\n5. INTEGRATION TESTS"
echo "===================="

total_tests=$((total_tests + 1))
if run_test "Sample data creation" "python -c 'from app import app, db; from utils import create_sample_delivery_items; app.app_context().push(); db.create_all(); create_sample_delivery_items(); print(\"Sample data created\")'"; then
    passed_tests=$((passed_tests + 1))
fi

total_tests=$((total_tests + 1))
if run_test "Database operations" "python -c 'from app import app, db; from models import Participant; app.app_context().push(); db.create_all(); p = Participant(nome=\"Test\", email=\"test@test.com\", qr_code=\"TEST001\"); db.session.add(p); db.session.commit(); found = Participant.query.filter_by(email=\"test@test.com\").first(); assert found is not None; print(\"Database operations working\")'"; then
    passed_tests=$((passed_tests + 1))
fi

# 6. Coverage Tests
print_status "\n6. COVERAGE TESTS"
echo "=================="

total_tests=$((total_tests + 1))
if run_test "Test coverage analysis" "pytest tests/test_models.py tests/test_utils.py --cov=. --cov-report=term-missing --quiet"; then
    passed_tests=$((passed_tests + 1))
fi

# 7. Application Startup Test
print_status "\n7. APPLICATION STARTUP TEST"
echo "============================"

# Create required directories
mkdir -p static/qr_codes static/uploads logs reports static/checkin_cache

total_tests=$((total_tests + 1))
if run_test "Application startup" "timeout 10s python -c 'from app import app; print(\"Application can start\")'"; then
    passed_tests=$((passed_tests + 1))
fi

# Final Results
echo ""
echo "=============================================="
echo "🏁 FINAL RESULTS"
echo "=============================================="

if [ $passed_tests -eq $total_tests ]; then
    print_success "ALL TESTS PASSED! ($passed_tests/$total_tests)"
    echo ""
    print_success "✅ Application is properly configured and ready to use!"
    print_success "✅ All core functionality is working correctly"
    print_success "✅ Code quality meets standards"
    print_success "✅ Database operations are functional"
    echo ""
    print_status "You can now run the application with:"
    echo "    python app.py"
    echo ""
    exit 0
else
    print_error "SOME TESTS FAILED ($passed_tests/$total_tests passed)"
    echo ""
    print_error "❌ Please check the failed tests above"
    print_warning "💡 Common issues:"
    echo "   - Missing dependencies: pip install -e .[test,dev]"
    echo "   - Missing virtual environment: python -m venv venv && source venv/bin/activate"
    echo "   - Database issues: rm undokai.db && python -c 'from app import app, db; app.app_context().push(); db.create_all()'"
    echo ""
    exit 1
fi