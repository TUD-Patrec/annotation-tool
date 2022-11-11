<div align="center">

![PyPI](https://img.shields.io/pypi/v/annotation-tool)
![PyPI - Downloads](https://img.shields.io/pypi/dm/annotation-tool)
![PyPI - License](https://img.shields.io/pypi/l/annotation-tool?color=brightgreen)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/annotation-tool)

</div>

# Installation

All stable versions can be installed from [PyPI] by using [pip] or your favorite package manager

    pip install annotation-tool

You can get pre-published versions from the [TestPyPI] repository by running

    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ annotation-tool

After installation the annotation tool can be run as simple as

    annotation-tool

# Development

**Requirements:**
- Python 3.8 or higher
- [poetry] 1.2 or higher
- [make]

For installing the development environment run

```bash
make setup
```

We are using [commitizen] to automate the version bumping and changelog generation. In order for this to work properly, contributors need to adhere to the [conventional commit](https://www.conventionalcommits.org/en/v1.0.0/) styling. This will be enforced using [pre-commit] hooks. To easier write commit messages that adhere to this style, we recommend to use `cz commit` (will be installed by [poetry] alongside the other development dependencies). Run `cz example` to see the format of an example commit message.

[commitizen]: https://commitizen-tools.github.io/commitizen/
[make]: https://www.gnu.org/software/make/
[pip]: https://pypi.org/project/pip/
[poetry]: https://python-poetry.org/
[pre-commit]: https://pre-commit.com/
[pypi]: https://pypi.org/
[testpypi]: https://test.pypi.org/project/annotation-tool/
