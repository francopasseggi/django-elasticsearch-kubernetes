# CSV Processor Project

## Overview

This project is a robust CSV processing system built with Django, Celery, and Elasticsearch. It's designed to handle large CSV files efficiently, process chunks in parallel, and provide fast search capabilities.

## Key Features

### 1. Documented API

We use `drf-spectacular` to automatically generate OpenAPI documentation. You can access the API documentation at:

- Swagger UI: `/api/docs/`

### 2. ElasticMQ Durable Queue

We use ElasticMQ as a durable message queue, which acts as a drop-in replacement for Amazon SQS. This ensures:

- Message persistence across restarts
- Improved reliability in distributed systems

### 3. Idempotent, Rate-Limitable Celery Tasks

Our Celery tasks are designed to be:

- Idempotent: Safe to execute multiple times without side effects
- Rate-limitable: Can control task execution rate to manage system load
- Parallelizable: Can be executed concurrently for improved performance
- Resilient: Can recover from worker restarts and continue execution

#### Task Execution Control

You can rate-limit task execution to distribute database load over a longer time interval. This can be configured in the Celery settings.

### 4. PostgreSQL to Elasticsearch Sync

We use Celery tasks to synchronize data between PostgreSQL and Elasticsearch. This ensures:

- Data consistency across systems
- Efficient, asynchronous updates
- Scalability for large datasets

### 5. S3-like Service for Local Development

We use MinIO as an S3-compatible object storage. This allows:

- Permanent storage of uploaded files
- Access to files by different worker pods for processing
- Simulation of S3 behavior in local development

### 6. Pytest Unit Testing

We use pytest for unit testing. The tests are integrated with VSCode when using dev containers with Docker Compose.

To run the tests:

```bash
pytest
```

### 7. Cursor-based Pagination with Elasticsearch Backend

We implement cursor-based pagination for efficient navigation through large result sets. This is particularly useful when working with Elasticsearch, as it provides consistent ordering and performance for deep pagination scenarios.

### 8. Stateful Processing Jobs

We use a `ProcessingJob` model to keep track of the state of each CSV processing job. This could allows us to:

- Monitor the progress of long-running jobs
- Recover from failures
- Provide status updates to users

### 9. Development Environment


#### Kubernetes Setup for Local Development

We also provide Kubernetes manifests for local development. This allows you to test the application in an environment closer to production.

Follow these steps to set up the Kubernetes environment:

1. App Configuration

   Create an `app-config.yaml` file inside the `k8s/config` directory:

   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: app-config
   data:
     # Django settings
     DJANGO_SECRET_KEY: "your-secret-key-here"
     DJANGO_DEBUG: "True"
     DJANGO_ALLOWED_HOSTS: "localhost,127.0.0.1,0.0.0.0"

     # Database settings
     DB_NAME: "sublime"
     DB_USER: "postgres"
     DB_PASSWORD: "postgres"
     DB_HOST: "db"
     DB_PORT: "5432"

     # Redis settings
     REDIS_URL: "redis://redis:6379/0"

     # Celery settings
     CELERY_BROKER_URL: "sqs://elasticmq:9324"

     # MinIO settings
     MINIO_STORAGE_ENDPOINT: "minio:9000"
     MINIO_STORAGE_USE_HTTPS: "False"
     MINIO_STORAGE_MEDIA_BUCKET_NAME: "media"
     MINIO_STORAGE_MEDIA_BACKUP_BUCKET: "Recycle Bin"
     MINIO_STORAGE_MEDIA_BACKUP_FORMA: "=%c/"
     MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET: "True"
     MINIO_STORAGE_STATIC_BUCKET_NAME: "static"
     MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET: "True"

     # AWS settings
     AWS_REGION: "us-east-1"
     AWS_ACCESS_KEY_ID: "ROOTNAME"
     AWS_SECRET_ACCESS_KEY: "ROOTPASSWORD"
     AWS_SESSION_TOKEN: "your_session_token"
     AWS_S3_ENDPOINT_URL: "http://minio:9000"

     # Elasticsearch settings
     ELASTICSEARCH_URL: "http://elasticsearch:9200"
   ```

2. Start Local Kubernetes

   ```bash
   # Install kubectl
   brew install kubectl

   # Install Minikube
   brew install minikube

   # Start Minikube
   minikube start --cpus 8 --memory 8192

   # Verify the cluster is running
   kubectl get nodes

   # Point your shell to minikube's docker-daemon
   eval $(minikube docker-env)

   # Build the app image
   cd /path/to/project && docker build -t sublime:latest .

   # Apply Kubernetes configuration
   kubectl apply -f k8s -R

   # Verify deployments
   kubectl get deployments
   kubectl get pods
   kubectl get services
   ```

3. Initialize the Application

   Once the Elasticsearch and database services are ready, run the migrations and create the index:

   ```bash
   # Run migrations
   kubectl exec $(kubectl get pod -l app=app -o jsonpath="{.items[0].metadata.name}") -- python /app/src/manage.py migrate

   # Create Elasticsearch index
   kubectl exec $(kubectl get pod -l app=app -o jsonpath="{.items[0].metadata.name}") -- python /app/src/manage.py search_index --create
   ```

4. Access the API

   To access the API, run:

   ```bash
   minikube service app
   ```

   This will provide you with a URL to access the application.
   
#### Docker Compose for Instant Development

We provide a `docker-compose.yml` file for quick setup of the development environment. This includes all necessary services:

- Django application
- PostgreSQL database
- Elasticsearch
- Redis (for caching)
- ElasticMQ (as SQS replacement)
- Celery workers
- MinIO (S3-compatible object storage)

To set up and start the development environment:

1. Install Prerequisites:
   - Docker with Docker Compose
   - Visual Studio Code
   - VSCode extensions: "Dev Containers" and "Docker"

2. Create a `.env` file in the root directory of the project with the following content:

   ```
   DJANGO_SECRET_KEY=django-insecure-y@p!u7a&a-avbrb22gsy2w-d+$b8qcawg!l&tut*=*$t!@x9-
   DJANGO_DEBUG=true
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

   DB_NAME=sublime
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=db
   DB_PORT=5432

   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=ROOTNAME
   AWS_SECRET_ACCESS_KEY=ROOTPASSWORD
   AWS_SESSION_TOKEN=your_session_token
   AWS_S3_ENDPOINT_URL=http://minio:9000

   MINIO_STORAGE_ENDPOINT=minio:9000
   MINIO_STORAGE_USE_HTTPS=False
   MINIO_STORAGE_MEDIA_BUCKET_NAME=media
   MINIO_STORAGE_MEDIA_BACKUP_BUCKET=Recycle Bin
   MINIO_STORAGE_MEDIA_BACKUP_FORMAT=%c/
   MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET=True
   MINIO_STORAGE_STATIC_BUCKET_NAME=static
   MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET=True

   REDIS_URL=redis://redis:6379
   ELASTICSEARCH_HOSTS=http://elasticsearch:9200
   ```

3. Open the project in Visual Studio Code.

4. Press `Cmd + Shift + P` (on macOS) or `Ctrl + Shift + P` (on Windows/Linux) to open the command palette.

5. Type "Dev Containers: Open Folder in Container" and select it.

6. Wait for the containers to be built and started. This may take a few minutes the first time.

7. Once the Dev Container is ready, open a new terminal in VS Code.

8. Run the following commands to set up the database and Elasticsearch index:

   ```bash
   make migrate
   make index
   ```

9. The application should now be running. You can access:
   - The API documentation at `http://0.0.0.0:8000/api/docs/`

10. You can now use the OpenAPI interactive mode in the API documentation or use curl to make requests to the API.


