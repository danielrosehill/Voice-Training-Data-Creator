# Release Process

This repository uses GitHub Actions to automatically build and release Debian packages.

## Automatic Release via Tag

1. **Update version in `debian/DEBIAN/control`**:
   ```bash
   # Edit the Version field
   nano debian/DEBIAN/control
   ```

2. **Commit and push the version change**:
   ```bash
   git add debian/DEBIAN/control
   git commit -m "Bump version to 1.0.14"
   git push
   ```

3. **Create and push a tag**:
   ```bash
   git tag v1.0.14
   git push origin v1.0.14
   ```

4. **GitHub Actions will automatically**:
   - Build the `.deb` package
   - Create a GitHub release
   - Upload the package as a release asset
   - Generate release notes

## Manual Release via Workflow Dispatch

You can also trigger a release manually from the GitHub Actions tab:

1. Go to **Actions** → **Build and Release**
2. Click **Run workflow**
3. Enter the version number (e.g., `1.0.14`)
4. Click **Run workflow**

This will:
- Update the version in `debian/DEBIAN/control`
- Build the package
- Create a tag and release
- Upload the `.deb` file

## What Gets Released

Each release includes:
- **Debian package** (`.deb` file) - ready to install on Ubuntu/Debian
- **Release notes** - installation instructions and changelog reference
- **Build artifact** - 30-day retention for debugging

## Version Numbering

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Current version format: `1.0.x`
