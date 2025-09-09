#!/bin/bash

# OLIS Pre-Modification Check Script
# Run this script BEFORE making changes to verify critical features work
# Based on CRITICAL_FEATURES.md safeguards

echo "🔍 OLIS Pre-Modification Safety Check"
echo "======================================"
echo "This script verifies critical features work before you make changes."
echo "If any critical features are broken, fix them first before proceeding."
echo ""

# Function to print colored output
print_status() {
    case $1 in
        "SUCCESS") echo -e "\033[32m✅ $2\033[0m" ;;
        "WARNING") echo -e "\033[33m⚠️  $2\033[0m" ;;
        "ERROR") echo -e "\033[31m❌ $2\033[0m" ;;
        "INFO") echo -e "\033[34mℹ️  $2\033[0m" ;;
    esac
}

# Check if server is running
print_status "INFO" "Checking if OLIS server is running..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    print_status "SUCCESS" "Server is running at http://localhost:8001"
else
    print_status "ERROR" "Server is not running!"
    print_status "INFO" "Please start the server first:"
    echo "   cd backend && python -m uvicorn api:app --reload --port 8001"
    echo ""
    print_status "ERROR" "Cannot proceed with pre-modification check without server"
    exit 1
fi

echo ""

# Check if virtual environment is activated and test dependencies are installed
print_status "INFO" "Checking test environment..."

# Check if we're in virtual environment
if [[ "$VIRTUAL_ENV" == *"olis-legislature"* ]]; then
    print_status "SUCCESS" "Virtual environment is activated"
else
    print_status "WARNING" "Virtual environment not activated - attempting to activate..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_status "SUCCESS" "Virtual environment activated"
    else
        print_status "ERROR" "Virtual environment not found!"
        print_status "INFO" "Please create and activate virtual environment:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r tests/requirements.txt"
        exit 1
    fi
fi

# Check if test dependencies are installed
if python -c "import httpx, pytest" 2>/dev/null; then
    print_status "SUCCESS" "Test dependencies are installed"
else
    print_status "WARNING" "Installing test dependencies..."
    pip install -r tests/requirements.txt
    if [ $? -eq 0 ]; then
        print_status "SUCCESS" "Test dependencies installed successfully"
    else
        print_status "ERROR" "Failed to install test dependencies"
        exit 1
    fi
fi

echo ""
echo "🧪 Running Critical Features Smoke Test..."
echo "----------------------------------------"

# Run the smoke test
if python tests/smoke_test.py; then
    echo ""
    print_status "SUCCESS" "All critical features are working!"
    print_status "INFO" "Safe to proceed with modifications"
    echo ""
    print_status "INFO" "NEXT STEPS:"
    echo "1. Make your changes"
    echo "2. Run this script again: ./pre-modification-check.sh"
    echo "3. If tests still pass, your changes are safe"
    echo ""
    exit 0
else
    echo ""
    print_status "ERROR" "Critical features are broken!"
    print_status "WARNING" "DO NOT PROCEED with modifications until issues are fixed"
    echo ""
    print_status "INFO" "TROUBLESHOOTING:"
    echo "1. Review the test output above"
    echo "2. Check CRITICAL_FEATURES.md for common issues"
    echo "3. Fix any broken functionality"
    echo "4. Run this script again to verify fixes"
    echo ""
    exit 1
fi