<div align="center">

![PyPI - Version](https://img.shields.io/pypi/v/annotation-tool)
![PyPI - Downloads](https://img.shields.io/pypi/dm/annotation-tool)
![PyPI - License](https://img.shields.io/pypi/l/annotation-tool?color=brightgreen)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/annotation-tool)

</div>

# Installation

All stable versions can be installed from [PyPI] by using [pip] or your favorite package manager

    pip install annotation-tool

You can get pre-published versions from [TestPyPI] or this repository

**Test PyPI:**

    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ annotation-tool

**From Source:**

    pip install git+https://github.com/TUD-Patrec/annotation-tool@master

After installation the annotation tool can be run as simple as

    annotation-tool

# Development

**Requirements:**
- Python 3.8 or higher
- [poetry] 1.2 or higher
- [make]
- [docker] (if you want to build the binaries)

For installing the development environment run

```bash
make setup
```

[docker]: https://www.docker.com/
[make]: https://www.gnu.org/software/make/
[pip]: https://pypi.org/project/pip/
[poetry]: https://python-poetry.org/
[pypi]: https://pypi.org/
[testpypi]: https://test.pypi.org/project/annotation-tool/
