#!/bin/bash
set -e

# Voice Training Data Creator - Debian Package Builder
# This script creates a .deb package for Ubuntu/Debian systems

PACKAGE_NAME="voice-training-data-creator"
BUILD_DIR="debian"
# Read version from control file
VERSION=$(grep "^Version:" "$BUILD_DIR/DEBIAN/control" | awk '{print $2}')
DEB_FILE="${PACKAGE_NAME}_${VERSION}_all.deb"

echo "========================================="
echo "Building Voice Training Data Creator"
echo "Version: $VERSION"
echo "========================================="

# Clean up any previous build
echo "Cleaning up previous build..."
rm -f *.deb

# Create directory structure if it doesn't exist
echo "Setting up build directory structure..."
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/$PACKAGE_NAME"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/usr/share/doc/$PACKAGE_NAME"

# Copy application files
echo "Copying application files..."
rsync -av --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='debian' --exclude='*.deb' \
    --exclude='.claude' --exclude='build-deb.sh' \
    src/ "$BUILD_DIR/usr/lib/$PACKAGE_NAME/src/"

# Copy requirements.txt
cp requirements.txt "$BUILD_DIR/usr/lib/$PACKAGE_NAME/"

# Copy README and other docs
cp README.md "$BUILD_DIR/usr/lib/$PACKAGE_NAME/"
if [ -f "CLAUDE.md" ]; then
    cp CLAUDE.md "$BUILD_DIR/usr/lib/$PACKAGE_NAME/"
fi

# Set correct permissions
echo "Setting file permissions..."
find "$BUILD_DIR" -type f -exec chmod 644 {} \;
find "$BUILD_DIR" -type d -exec chmod 755 {} \;
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"
chmod 755 "$BUILD_DIR/usr/bin/$PACKAGE_NAME"

# Build the package
echo "Building .deb package..."
dpkg-deb --build "$BUILD_DIR" "$DEB_FILE"

# Get package size
PACKAGE_SIZE=$(du -sh "$DEB_FILE" | cut -f1)

echo "========================================="
echo "Build completed successfully!"
echo "Package: $DEB_FILE"
echo "Size: $PACKAGE_SIZE"
echo "========================================="
echo ""
echo "To install, run:"
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt-get install -f  # Install dependencies if needed"
echo ""
echo "To test:"
echo "  voice-training-data-creator"
echo ""
echo "To uninstall:"
echo "  sudo apt-get remove $PACKAGE_NAME"
echo "========================================="

# Validate the package
echo ""
echo "Package information:"
dpkg-deb --info "$DEB_FILE"

echo ""
echo "Package contents:"
dpkg-deb --contents "$DEB_FILE" | head -20
echo "... (use 'dpkg-deb --contents $DEB_FILE' to see all files)"
