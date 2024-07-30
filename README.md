### Create k8s/config/app-config.yaml file with this data:

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


