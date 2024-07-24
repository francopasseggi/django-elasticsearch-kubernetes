# Define variables
ENV_FILE = .env

# Load environment variables from the .env file
include $(ENV_FILE)
export $(shell sed 's/=.*//' $(ENV_FILE))

# Define the tasks
.PHONY: runserver migrate setup

setup:
	@echo "Setting up environment..."

migrate: setup
	python src/manage.py migrate

makemigrations: setup
	python src/manage.py makemigrations

runserver: setup
	python src/manage.py runserver 0.0.0.0:8000


test: setup
	pytest

requirements: setup
	pip freeze > requirements.txt

format: setup
	python -m ruff format .

check: setup
	python -m ruff check .