<div align="center">

![](https://img.shields.io/badge/license-MIT-green)

</div>

# Installation

All stable versions can be installed from [PyPI](https://pypi.org/) by using [pip](https://pypi.org/project/pip/) or your favorite package manager

    pip install annotation-tool

You can get pre-published versions from the [TestPyPI](https://test.pypi.org/project/annotation-tool/) repository by running

    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ annotation-tool

After installation the annotation tool can be run as simple as

    annotation-tool

# Development

For installing the requirements you can use [poetry](https://python-poetry.org/). After you installed poetry just run

    poetry install

Building the executable requires [docker](https://www.docker.com/). After you installed docker on your system you can run one of

    make build-linux
    make build-windows

to build the executables for linux or windows.
