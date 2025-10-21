#!/bin/bash
# CI/CD Test Runner for Mail-Mind
# Optimized for resource-constrained test machines

set -e  # Exit on error

echo "================================================================="
echo "Mail-Mind CI/CD Test Suite"
echo "================================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python 3 found"

# Check dependencies
echo ""
echo "Checking dependencies..."
python3 -c "import ollama" 2>/dev/null && echo -e "${GREEN}✓${NC} ollama library installed" || {
    echo -e "${YELLOW}⚠${NC} ollama library not found, installing..."
    pip install -q ollama
}

python3 -c "import pytest" 2>/dev/null && echo -e "${GREEN}✓${NC} pytest installed" || {
    echo -e "${YELLOW}⚠${NC} pytest not found, installing..."
    pip install -q pytest
}

# Test Suite
echo ""
echo "================================================================="
echo "Running Test Suite (Resource-Constrained Mode)"
echo "================================================================="
echo ""

FAILED=0

# Level 1: Unit Tests
echo "[1/3] Running Unit Tests (mock objects)..."
if python3 mock_ollama_test.py > /tmp/test1.log 2>&1; then
    echo -e "${GREEN}✓${NC} Unit tests passed"
else
    echo -e "${RED}✗${NC} Unit tests failed"
    cat /tmp/test1.log
    FAILED=$((FAILED + 1))
fi

# Level 2: Scenario Tests
echo ""
echo "[2/3] Running Scenario Tests..."
if python3 test_inference_scenarios.py > /tmp/test2.log 2>&1; then
    echo -e "${GREEN}✓${NC} Scenario tests passed"
else
    echo -e "${RED}✗${NC} Scenario tests failed"
    cat /tmp/test2.log
    FAILED=$((FAILED + 1))
fi

# Level 3: Integration Tests with Mock API
echo ""
echo "[3/3] Running Integration Tests (mock API)..."
if timeout 30 python3 test_with_mock_api.py > /tmp/test3.log 2>&1; then
    echo -e "${GREEN}✓${NC} Integration tests passed"
else
    echo -e "${RED}✗${NC} Integration tests failed"
    cat /tmp/test3.log
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "================================================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC} (3/3)"
    echo "================================================================="
    echo ""
    echo "Test Summary:"
    echo "  • Unit Tests: ✓ Passed"
    echo "  • Scenario Tests: ✓ Passed"
    echo "  • Integration Tests: ✓ Passed"
    echo ""
    echo "Note: These tests run without requiring Ollama or model inference,"
    echo "making them perfect for CI/CD and resource-constrained environments."
    echo ""
    exit 0
else
    echo -e "${RED}✗ TESTS FAILED${NC} ($FAILED/3)"
    echo "================================================================="
    exit 1
fi
