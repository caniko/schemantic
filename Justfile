install:
    poetry install -E toml -E yaml

format:
	black .
	isort .
	ruff check . --fix
	@echo "Formatting complete 🎉"

tcheck:
	poetry run pyright schemantic