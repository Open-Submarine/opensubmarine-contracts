# Contributing Guidelines

There are many ways to contribute to OpenZeppelin Contracts.

## Troubleshooting

You can help other users in the community to solve their smart contract issues in the [OpenSubmarine Discord Channel].

[OpenSubmarine Discord Channel]: https://discord.com/channels/1055863853633785857/1331392190282465280

## Opening an issue

You can [open an issue] to suggest a feature or report a minor bug. For serious bugs please do not open an issue, instead refer to our security policy for appropriate steps.

If you believe your issue may be due to user error and not a problem in the library, consider instead posting a question on the [OpenSubmarine Discord Channel].

Before opening an issue, be sure to search through the existing open and closed issues, and consider posting a comment in one of those instead.

When requesting a new feature, include as many details as you can, especially around the use cases that motivate it. Features are prioritized according to the impact they may have on the ecosystem, so we appreciate information showing that the impact could be high.


[open an issue]: https://github.com/Open-Submarine/opensubmarine-contracts/issues/new/choose

## Submitting a pull request

If you would like to contribute code or documentation you may do so by forking the repository and submitting a pull request.

Any non-trivial code contribution must be first discussed with the maintainers in an issue (see [Opening an issue](#opening-an-issue)). Only very minor changes are accepted without prior discussion.

Make sure to read and follow the [engineering guidelines](./GUIDELINES.md). Run linter and tests to make sure your pull request is good before submitting it.

Changelog entries should be added to each pull request.

When opening the pull request you will be presented with a template and a series of instructions. Read through it carefully and follow all the steps. Expect a review and feedback from the maintainers afterwards.

If you're looking for a good place to start, look for issues labelled ["good first issue"](https://github.com/Open-Submarine/opensubmarine-contracts/labels/good%20first%20issue)!

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