# SQLAlchemy-Utils Release Process

This document outlines the complete process for releasing new versions of SQLAlchemy-Utils.

## Release Workflow Overview

SQLAlchemy-Utils uses a two-branch release workflow:

- **`master`** - Main branch
- **`releases`** - Release branch

## Prerequisites

1. **PyPI Access** - Ensure you have maintainer access to the SQLAlchemy-Utils PyPI project
2. **API Token** - Have your PyPI API token ready for upload
3. **Clean Working Directory** - Ensure no uncommitted changes

## Step-by-Step Release Process

### 1. Prepare the Release on Master

```bash
# Ensure you're on master and up to date
git checkout master
git pull origin master

# Update version in pyproject.toml
# Edit pyproject.toml and change version = "X.Y.Z"

# Commit the version bump
git add pyproject.toml
git commit -m "Bump version to X.Y.Z"
```

### 2. Switch to Releases Branch

```bash
# Switch to releases branch
git checkout releases
git pull origin releases

# Merge master changes
git merge master --no-ff -m "Merge branch 'master' into releases"
```

### 3. Update Release Information

```bash
# Update CHANGES.rst
# - Change "Unreleased changes" to "X.Y.Z (YYYY-MM-DD)"
# - Add release date

# Update version in sqlalchemy_utils/__init__.py
# Change __version__ = 'X.Y.Z'

# Commit release changes
git add CHANGES.rst sqlalchemy_utils/__init__.py
git commit -m "Release X.Y.Z

- Brief summary of major changes
- Key feature additions or removals
- Important bug fixes"
```

### 4. Create Git Tag

```bash
# Create and push the release tag
git tag X.Y.Z
```

### 5. Push Changes to GitHub

```bash
# Push both branches and the tag
git push origin releases
git push origin master
git push origin X.Y.Z
```

### 6. Build and Publish to PyPI

```bash
# Create virtual environment and install build tools
python3 -m venv .venv
source .venv/bin/activate
pip install build twine

# Build the distribution packages
python -m build

# Upload to PyPI (you'll be prompted for API token)
python -m twine upload dist/*
```

### 7. Merge Releases Back to Master

```bash
# Switch back to master and merge releases to keep in sync
git checkout master
git merge releases --no-ff -m "Merge releases branch back to master"
git push origin master
```

## Version Numbering

SQLAlchemy-Utils follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** - Breaking changes, dropped Python/SQLAlchemy support
- **MINOR** - New features, significant improvements
- **PATCH** - Bug fixes, small improvements

## Release Checklist

Before releasing, ensure:

- [ ] All tests pass on CI
- [ ] Documentation builds successfully
- [ ] Version numbers updated in both `pyproject.toml` and `__init__.py`
- [ ] CHANGES.rst updated with release notes and date
- [ ] Git tag created and pushed
- [ ] PyPI upload successful
- [ ] Both master and releases branches are in sync

## Post-Release

1. **Verify PyPI** - Check that the new version is available on PyPI
2. **Update Documentation** - Ensure Read the Docs builds the new version
3. **GitHub Release** - Create a GitHub release from the tag with release notes

## Troubleshooting

### Build Failures
- Ensure all dependencies are properly specified in `pyproject.toml`
- Check that MANIFEST.in includes all necessary files

### PyPI Upload Issues
- Verify your API token has the correct permissions
- Ensure version number hasn't been used before
- Check package metadata in `pyproject.toml` is valid

### Branch Conflicts
- Use `git status` and `git diff` to understand conflicts
- The releases branch should always contain the latest release state
- Master should contain the development state for the next release

## Files Involved in Releases

- `pyproject.toml` - Project metadata and version (master branch)
- `sqlalchemy_utils/__init__.py` - Version string (releases branch)  
- `CHANGES.rst` - Release notes and changelog (releases branch)
- `MANIFEST.in` - Files to include in distribution
- `.github/workflows/` - CI configuration
- `tox.ini` - Test configuration

## Branch Differences

| File | Master Branch | Releases Branch |
|------|---------------|-----------------|
| CI Config | Modern (ruff, Python 3.9-3.13) | Legacy compatible |
| Linting | ruff | flake8 + isort |
| Version Source | pyproject.toml | __init__.py |
| Purpose | Development | Release management |

This dual-branch approach allows maintaining modern development practices on master while ensuring stable, tested releases through the releases branch.