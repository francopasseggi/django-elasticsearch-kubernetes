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

worker: setup
	cd src && celery -A core worker -l info

shell: setup
	python src/manage.py shell_plus

index: setup
	python src/manage.py search_index --create

k8s_migrate:
	kubectl exec $$(kubectl get pod -l app=app -o jsonpath="{.items[0].metadata.name}") -- python /app/src/manage.py migrate

k8s_index:
	kubectl exec $$(kubectl get pod -l app=app -o jsonpath="{.items[0].metadata.name}") -- python /app/src/manage.py search_index --rebuild -f
