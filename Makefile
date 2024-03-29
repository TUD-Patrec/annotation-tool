.PHONY: install all test format clean build-linux build-windows

setup: install

install:
	@echo "Installing dependencies..."
	poetry install

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
	find annotation_tool -type d -name '__pycache__' -print -prune -exec rm -r {} \;

build-linux:
	docker run --rm -e "PLATFORMS=linux" -v $(CURDIR):/src --entrypoint="/bin/sh" fydeinc/pyinstaller -c "pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry install --without=dev --with=build && /entrypoint.sh --onefile --name annotation-tool /src/main.py"

build-windows:
	docker run --rm -e "PLATFORMS=windows" -v $(CURDIR):/src --entrypoint="/bin/sh" fydeinc/pyinstaller -c "/usr/win64/bin/python -m pip install --upgrade pip && /usr/win64/bin/python -m pip install poetry && /usr/win64/bin/python -m poetry config virtualenvs.create false && /usr/win64/bin/python -m poetry install --without=dev --with=build && /entrypoint.sh --onefile --name annotation-tool /src/main.py"

build-mac-intel:
	pyinstaller --onedir --windowed --icon=icons/sara.icns --target-architecture x86_64 --name SARA main.py
	pkgbuild --install-location /Applications --component dist/SARA.app dist/SARA-x86_64.pkg

build-mac-arm:
	pyinstaller --onedir --windowed --icon=icons/sara.icns --target-architecture arm64 --name SARA main.py
	pkgbuild --install-location /Applications --component dist/SARA.app dist/SARA-arm64.pkg

