.PHONY: pre-commit install all test-all format clean build-linux build-windows

setup: install pre-commit

install:
	@echo "Installing depenencies..."
	poetry install

pre-commit: install
	@echo "Setting up pre-commit..."
	poetry run pre-commit install
	poetry run pre-commit autoupdate

bump:
	@echo "Bumping version..."
	poetry run cz bump

bump-alpha:
	@echo "Bumping alpha pre-release version"
	poetry run cz bump --prerelease alpha

bump-beta:
	@echo "Bumping beta pre-release version"
	poetry run cz bump --prerelease beta

test-all: test-black test-flake8 test-isort

test-black:
	@echo "Checking format with black..."
	poetry run black --check src main.py

test-flake8:
	@echo "Checking format with flake8..."
	poetry run flake8 src main.py --count --statistics

test-isort:
	@echo "Checking format with isort..."
	poetry run isort --check --settings-path pyproject.toml src main.py

format:
	@echo "Formatting with black and isort..."
	poetry run black src main.py
	poetry run isort --settings-path pyproject.toml src main.py

clean:
	rm -rf build dist __pycache__ __local__storage__

build-linux:
	docker run --rm -e "PLATFORMS=linux" -v $(shell pwd):/src --entrypoint='/bin/sh' fydeinc/pyinstaller -c 'pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry install && /entrypoint.sh --onefile --noconsole --name annotation-tool /src/main.py'

build-windows:
	docker run --rm -e "PLATFORMS=windows" -v $(shell pwd):/src --entrypoint='/bin/sh' fydeinc/pyinstaller -c '/usr/win64/bin/python -m pip install --upgrade pip && /usr/win64/bin/python -m pip install poetry && /usr/win64/bin/python -m poetry config virtualenvs.create false && /usr/win64/bin/python -m poetry install && /entrypoint.sh --onefile --noconsole --name annotation-tool /src/main.py'

