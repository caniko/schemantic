install:
    poetry install -E toml -E yaml

format:
	black .
	isort .
	ruff check . --fix
	@echo "Formatting complete 🎉"

tcheck:
	mypy -p schemantic

test:
    poetry run pytest tests