.PHONY: pre-commit install all test format clean build-linux build-windows

setup: install pre-commit

install:
	@echo "Installing dependencies..."
	poetry install

pre-commit: install
	@echo "Setting up pre-commit..."
	poetry run pre-commit install -t commit-msg -t pre-commit

bump:
	@echo "Bumping version..."
	poetry run cz bump

bump-alpha:
	@echo "Bumping alpha pre-release version"
	poetry run cz bump --prerelease alpha

bump-beta:
	@echo "Bumping beta pre-release version"
	poetry run cz bump --prerelease beta

test: test-black test-flake8 test-isort
	@echo "All tests passed successfully!"

test-black:
	@echo "Checking format with black..."
	poetry run black --check annotation_tool main.py

test-flake8:
	@echo "Checking format with flake8..."
	poetry run flake8 annotation_tool main.py --count --statistics

test-isort:
	@echo "Checking format with isort..."
	poetry run isort --check --settings-path pyproject.toml annotation_tool main.py

format:
	@echo "Formatting with black and isort..."
	poetry run black annotation_tool main.py
	poetry run isort --settings-path pyproject.toml annotation_tool main.py

clean:
	rm -rf build dist __pycache__ *.spec

build-linux:
	docker run --rm -e "PLATFORMS=linux" -v $(CURDIR):/src --entrypoint="/bin/sh" fydeinc/pyinstaller -c "pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry install --without=dev --with=build && /entrypoint.sh --onefile --name annotation-tool /src/main.py"

build-windows:
	docker run --rm -e "PLATFORMS=windows" -v $(CURDIR):/src --entrypoint="/bin/sh" fydeinc/pyinstaller -c "/usr/win64/bin/python -m pip install --upgrade pip && /usr/win64/bin/python -m pip install poetry && /usr/win64/bin/python -m poetry config virtualenvs.create false && /usr/win64/bin/python -m poetry install --without=dev --with=build && /entrypoint.sh --onefile --name annotation-tool /src/main.py"

