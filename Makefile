all: test build

build-linux:
	docker run --rm -e "PLATFORMS=linux" -v $(shell pwd):/src --entrypoint='/bin/sh' fydeinc/pyinstaller -c 'pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry install && /entrypoint.sh --onefile --noconsole --name annotation-tool /src/main.py'

build-windows:
	docker run --rm -e "PLATFORMS=windows" -v $(shell pwd):/src --entrypoint='/bin/sh' fydeinc/pyinstaller -c '/usr/win64/bin/python -m pip install --upgrade pip && /usr/win64/bin/python -m pip install poetry && /usr/win64/bin/python -m poetry config virtualenvs.create false && /usr/win64/bin/python -m poetry install && /entrypoint.sh --onefile --noconsole --name annotation-tool /src/main.py'

test:
	poetry run flake8 src main.py --count --statistics
	poetry run black --check src main.py
	poetry run isort --check --settings-path pyproject.toml src main.py

format:
	poetry run black src main.py
	poetry run isort --settings-path pyproject.toml src main.py

clean:
	rm -rf build dist __pycache__ __local__storage__