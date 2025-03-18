# Contributing Guide

## Development Setup

TBD

## Publishing to PyPI

### Prerequisites
1. Create accounts on [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/)
2. Install required tools:
```bash
python -m pip install --upgrade pip
python -m pip install build twine
```

### Building and Publishing
1. Update version in `pyproject.toml`
2. Build the package:
```bash
python -m build
```

3. Test on TestPyPI first:
```bash
python -m twine upload --repository testpypi dist/*
```

4. Test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ your-package-name
```

5. If tests pass, upload to PyPI:
```bash
python -m twine upload dist/*
```

### Setting up PyPI Credentials
Create a `~/.pypirc` file:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = your-pypi-token

[testpypi]
username = __token__
password = your-testpypi-token
```

**Note:** Never commit PyPI tokens to version control!