# Installation

For installing the requirements you can use [poetry](https://python-poetry.org/). After you installed poetry just run

    poetry install

If you do not want to install the development requirements run

    poetry install --no-dev

Building the executable requires [docker](https://www.docker.com/). After you installed docker on your system you can run one of

    make build-linux
    make build-windows

to build the executables for linux or windows.
