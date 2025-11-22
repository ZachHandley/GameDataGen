# Forgejo CI/CD Workflows

Automated workflows for building, testing, and releasing GameDataGen.

## Workflows

### 🧪 test.yml - Continuous Testing

**Triggers:**
- Push to `main` branch
- Push to `claude/**` branches
- Pull requests to `main`

**Jobs:**
- Run on Python 3.11 and 3.12
- Run `ruff` linting
- Run `ruff` formatting checks
- Run `mypy` type checking
- Run `pytest` tests

**Usage:**
Automatically runs on every push and PR. No manual action needed.

### 📦 release.yml - Build and Release

**Triggers:**
- Push tags matching `v*.*.*` (e.g., `v0.1.0`)
- Manual workflow dispatch

**Jobs:**
1. **Build** - Build Python wheel and source distribution
2. **Create Release** - Create GitHub/Forgejo release with notes
3. **Publish PyPI** - Publish to PyPI (if `PYPI_TOKEN` secret is set)

**Usage:**

Create a release by pushing a tag:
```bash
# Create and push a version tag
git tag v0.1.0
git push origin v0.1.0
```

Or manually trigger:
```bash
# Via Forgejo UI: Actions > Build and Release > Run Workflow
```

**Configuration:**
- Set `PYPI_TOKEN` secret in repository settings for PyPI publishing

### 🖥️ desktop-build.yml - Desktop Executables

**Triggers:**
- Push tags matching `v*.*.*`
- Manual workflow dispatch

**Jobs:**
1. **Build Windows** - Create Windows `.exe`
2. **Build macOS** - Create macOS app bundle
3. **Build Linux** - Create Linux executable
4. **Create Desktop Release** - Attach all builds to release

**Artifacts:**
- `GameDataGen-Desktop-Windows.zip`
- `GameDataGen-Desktop-macOS.tar.gz`
- `GameDataGen-Desktop-Linux.tar.gz`

**Usage:**
Automatically runs on version tags. Desktop builds are attached to the release.

## Setup

### Required Secrets

Configure in Forgejo repository settings (Settings > Secrets):

- `PYPI_TOKEN` - PyPI API token for publishing packages (optional)

### GitHub/Forgejo Compatibility

These workflows use standard GitHub Actions syntax and are compatible with:
- Forgejo (with Actions enabled)
- Gitea (with Actions enabled)
- GitHub (if you migrate the repo)

### Directory Structure

Forgejo looks for workflows in:
- `.forgejo/workflows/` (Forgejo-specific)
- `.gitea/workflows/` (Gitea compatibility)
- `.github/workflows/` (GitHub compatibility)

## Release Process

### Standard Release

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.1.0"
   git push
   ```
4. Create and push tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
5. Workflows automatically:
   - Build Python package
   - Build desktop executables
   - Create release with notes
   - Publish to PyPI (if configured)
   - Attach desktop builds

### Manual Release

1. Go to repository on Forgejo
2. Navigate to **Actions**
3. Select **Build and Release** workflow
4. Click **Run Workflow**
5. Enter version (e.g., `v0.1.0`)
6. Click **Run**

## Debugging Workflows

### View Logs

1. Go to repository **Actions** tab
2. Click on workflow run
3. Click on job to view logs

### Common Issues

**Issue:** `PYPI_TOKEN not configured`
- **Solution:** Add `PYPI_TOKEN` secret or remove PyPI publish job

**Issue:** Desktop build fails
- **Solution:** Check PyInstaller compatibility with dependencies

**Issue:** Tests fail
- **Solution:** Run tests locally: `uv run pytest tests/`

## Local Testing

Test workflows locally before pushing:

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest tests/ -v

# Run linting
uv run ruff check src/

# Run formatting check
uv run ruff format --check src/

# Run type checking
uv run mypy src/gamedatagen/

# Build package
uv build

# Build desktop app (requires PyInstaller)
uv pip install pyinstaller
uv run pyinstaller src/gamedatagen/desktop/app.py
```

## Matrix Builds

The test workflow runs on multiple Python versions:
- Python 3.11
- Python 3.12

Desktop builds run on multiple platforms:
- Windows (windows-latest)
- macOS (macos-latest)
- Linux (ubuntu-latest)

## Caching

Workflows cache:
- Python dependencies (via uv)
- Build artifacts (between jobs)

## Artifacts

Build artifacts are stored for 90 days (Forgejo default) and include:
- Python wheel and source dist
- Desktop executables for all platforms

## Further Reading

- [Forgejo Actions Documentation](https://forgejo.org/docs/latest/user/actions/)
- [GitHub Actions Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [UV Documentation](https://docs.astral.sh/uv/)
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
