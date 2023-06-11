makemigrations:
	@cd models && alembic revision --autogenerate

migrate:
	@cd models && alembic upgrade head

dump:
	pip freeze > requirements.txt

run:
	uvicorn config.main:app --reload

set_pythonpath:
	export PYTHONPATH="$PWD"