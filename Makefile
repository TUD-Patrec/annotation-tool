all: test build

build:
	docker run --rm -e "PLATFORMS=linux,windows" -v $(shell pwd):/src --entrypoint='/bin/sh' fydeinc/pyinstaller -c 'pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry export --without-hashes -o requirements.txt && /entrypoint.sh --onefile /src/main.py && rm requirements.txt'

build-linux:
		docker run --rm -e "PLATFORMS=linux" -v $(shell pwd):/src --entrypoint='/bin/sh' fydeinc/pyinstaller -c 'pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry export --without-hashes -o requirements.txt && /entrypoint.sh --onefile /src/main.py && rm requirements.txt'

build-windows:
		docker run --rm -e "PLATFORMS=windows" -v $(shell pwd):/src --entrypoint='/bin/sh' fydeinc/pyinstaller -c 'pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry export --without-hashes -o requirements.txt && /entrypoint.sh --onefile /src/main.py && rm requirements.txt'

test:
	poetry run flake8 . --count --statistics
	poetry run black --check .
	poetry run isort --check --settings-path pyproject.toml --recursive .

clean:
	rm -rf build dist __pycache__ __local__storage__
