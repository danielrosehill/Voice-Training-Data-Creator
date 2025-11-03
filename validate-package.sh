#!/bin/bash
# Validation script for the Voice Training Data Creator .deb package
# Run this AFTER installing the package to verify everything works

set -e

PACKAGE_NAME="voice-training-data-creator"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Voice Training Data Creator - Package Validation"
echo "========================================="
echo ""

# Function to print test results
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILURES++))
}

test_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

FAILURES=0

# Test 1: Check if package is installed
echo "1. Checking package installation..."
if dpkg -l | grep -q "$PACKAGE_NAME"; then
    VERSION=$(dpkg -l | grep "$PACKAGE_NAME" | awk '{print $3}')
    test_pass "Package installed (version $VERSION)"
else
    test_fail "Package not installed"
    echo ""
    echo "Please install the package first:"
    echo "  sudo dpkg -i voice-training-data-creator_*.deb"
    echo "  sudo apt-get install -f"
    exit 1
fi

# Test 2: Check executable
echo "2. Checking executable..."
if [ -f "/usr/bin/$PACKAGE_NAME" ]; then
    test_pass "Executable exists at /usr/bin/$PACKAGE_NAME"
    if [ -x "/usr/bin/$PACKAGE_NAME" ]; then
        test_pass "Executable has correct permissions"
    else
        test_fail "Executable not executable"
    fi
else
    test_fail "Executable not found"
fi

# Test 3: Check application files
echo "3. Checking application files..."
if [ -d "/usr/lib/$PACKAGE_NAME" ]; then
    test_pass "Application directory exists"

    if [ -f "/usr/lib/$PACKAGE_NAME/requirements.txt" ]; then
        test_pass "requirements.txt found"
    else
        test_fail "requirements.txt missing"
    fi

    if [ -d "/usr/lib/$PACKAGE_NAME/src" ]; then
        test_pass "Source directory found"
    else
        test_fail "Source directory missing"
    fi
else
    test_fail "Application directory not found"
fi

# Test 4: Check virtual environment
echo "4. Checking virtual environment..."
if [ -d "/usr/lib/$PACKAGE_NAME/venv" ]; then
    test_pass "Virtual environment exists"

    if [ -f "/usr/lib/$PACKAGE_NAME/venv/bin/python" ]; then
        test_pass "Python executable in venv"

        # Check Python version
        PYTHON_VERSION=$(/usr/lib/$PACKAGE_NAME/venv/bin/python --version 2>&1 | awk '{print $2}')
        test_pass "Python version: $PYTHON_VERSION"
    else
        test_fail "Python not found in venv"
    fi
else
    test_warn "Virtual environment not created (run postinst manually or reinstall)"
fi

# Test 5: Check dependencies
echo "5. Checking Python dependencies..."
if [ -f "/usr/lib/$PACKAGE_NAME/venv/bin/pip" ]; then
    DEPS=("PyQt6" "sounddevice" "soundfile" "numpy" "openai" "keyring")
    for dep in "${DEPS[@]}"; do
        if /usr/lib/$PACKAGE_NAME/venv/bin/pip show "$dep" &>/dev/null; then
            test_pass "$dep installed"
        else
            test_fail "$dep not installed"
        fi
    done
else
    test_warn "pip not found in venv"
fi

# Test 6: Check desktop integration
echo "6. Checking desktop integration..."
if [ -f "/usr/share/applications/$PACKAGE_NAME.desktop" ]; then
    test_pass "Desktop entry exists"
else
    test_fail "Desktop entry missing"
fi

if [ -f "/usr/share/icons/hicolor/256x256/apps/$PACKAGE_NAME.png" ]; then
    test_pass "Application icon exists"
else
    test_warn "Application icon missing (non-critical)"
fi

# Test 7: Check documentation
echo "7. Checking documentation..."
if [ -f "/usr/share/doc/$PACKAGE_NAME/copyright" ]; then
    test_pass "Copyright file exists"
else
    test_warn "Copyright file missing"
fi

# Test 8: Check user configuration directory
echo "8. Checking user configuration..."
CONFIG_DIR="$HOME/.config/VoiceTrainingDataCreator"
if [ -d "$CONFIG_DIR" ]; then
    test_pass "Config directory exists: $CONFIG_DIR"

    if [ -f "$CONFIG_DIR/config.json" ]; then
        test_pass "Config file exists"
    else
        test_warn "Config file not created yet (will be created on first run)"
    fi
else
    test_warn "Config directory not created yet (will be created on first run)"
fi

# Test 9: Check system dependencies
echo "9. Checking system dependencies..."
SYS_DEPS=("python3" "python3-pip" "python3-venv" "libportaudio2")
for dep in "${SYS_DEPS[@]}"; do
    if dpkg -l | grep -q "^ii.*$dep"; then
        test_pass "$dep installed"
    else
        test_fail "$dep not installed"
    fi
done

# Test 10: Test executable can be found in PATH
echo "10. Checking PATH..."
if which $PACKAGE_NAME &>/dev/null; then
    test_pass "Executable in PATH"
else
    test_fail "Executable not in PATH"
fi

# Summary
echo ""
echo "========================================="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All critical tests passed!${NC}"
    echo ""
    echo "The package is properly installed and ready to use."
    echo ""
    echo "To launch the application:"
    echo "  $PACKAGE_NAME"
    echo ""
    echo "Or find it in your application menu under Sound/Audio."
else
    echo -e "${RED}$FAILURES test(s) failed${NC}"
    echo ""
    echo "Please check the errors above and reinstall if necessary:"
    echo "  sudo apt-get remove $PACKAGE_NAME"
    echo "  sudo dpkg -i voice-training-data-creator_*.deb"
    echo "  sudo apt-get install -f"
fi
echo "========================================="

exit $FAILURES
