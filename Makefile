makemigrations:
	@cd models && alembic revision --autogenerate

migrate:
	@cd models && alembic upgrade head

dump:
	pip freeze > requirements.txt
