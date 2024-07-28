import csv
from collections.abc import Generator
from typing import Any

from celery import chord, group, shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.core.files import File
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections

from organizations.documents import OrganizationDocument
from organizations.models import Country, Industry, Organization, ProcessingJob

logger = get_task_logger(__name__)


class CSVReadingError(Exception):
    pass


class IndexingError(Exception):
    pass


CHUNK_SIZE = 500


@shared_task(name="process_csv", acks_late=True)
def process_csv(job_id: int) -> None:
    try:
        processing_job = ProcessingJob.objects.get(id=job_id)
        file_processor = FileProcessor(processing_job.file)
        chunk_processor = ChunkProcessor()

        chains = [
            chunk_processor.process_chunk.s(chunk) | index_chunk.s()
            for chunk in file_processor.get_chunks()
        ]

        chord(group(*chains))(handle_results.s(job_id).on_error(handle_error.s(job_id)))

    except ProcessingJob.DoesNotExist:
        logger.error(f"Processing job {job_id} not found")
    except Exception as e:
        handle_processing_error(job_id, e)


def handle_processing_error(job_id: int, error: Exception) -> None:
    logger.error(f"Error processing job {job_id}: {str(error)}")
    processing_job = ProcessingJob.objects.get(id=job_id)
    processing_job.status = ProcessingJob.Status.ERROR
    processing_job.error_message = str(error)
    processing_job.save()
    raise error


class FileProcessor:
    def __init__(self, file: File, chunk_size: int = CHUNK_SIZE):
        self.file = file
        self.chunk_size = chunk_size

    def get_chunks(self) -> Generator[list[str], None, None]:
        chunk = []
        for row in self.file:
            chunk.append(row.decode("utf-8"))
            if len(chunk) >= self.chunk_size:
                yield chunk
                chunk = []

        if chunk:
            yield chunk

        self.file.close()


class ChunkProcessor:
    @staticmethod
    @shared_task(
        bind=True,
        max_retries=3,
        default_retry_delay=30,
        acks_late=True,
        name="process_chunk",
    )
    def process_chunk(self, chunk: list[str]) -> list[int]:
        try:
            organizations = Organization.objects.bulk_create(
                ChunkProcessor.get_organizations_from_chunk(chunk),
                unique_fields=["organization_id"],
                update_conflicts=True,
                update_fields=[
                    "name",
                    "website",
                    "country_id",
                    "description",
                    "founded",
                    "industry_id",
                    "number_of_employees",
                ],
            )
            return [org.id for org in organizations]
        except Exception as exc:
            logger.exception("Failed to save organizations")
            raise self.retry(exc=exc)

    @staticmethod
    def get_organizations_from_chunk(chunk: list[str]) -> list[Organization]:
        csv_reader = csv.reader(chunk)
        return [
            ChunkProcessor.get_organization_from_row(row)
            for row in csv_reader
            if len(row) == 9 and row[0] != "Index"
        ]

    @staticmethod
    def get_organization_from_row(row: list[str]) -> Organization:
        return Organization(
            organization_id=row[1],
            name=row[2],
            website=row[3],
            country=ChunkProcessor.get_or_create_country(row[4]),
            description=row[5],
            founded=row[6],
            industry=ChunkProcessor.get_or_create_industry(row[7]),
            number_of_employees=row[8],
        )

    @staticmethod
    def get_or_create_country(country_name: str) -> Country:
        return CacheManager.get_or_create(Country, f"country_{country_name}", name=country_name)

    @staticmethod
    def get_or_create_industry(industry_type: str) -> Industry:
        return CacheManager.get_or_create(Industry, f"industry_{industry_type}", type=industry_type)


class CacheManager:
    @staticmethod
    def get_or_create(model, cache_key: str, **kwargs) -> Any:
        item = cache.get(cache_key)
        if not item:
            item, _ = model.objects.get_or_create(**kwargs)
            cache.set(cache_key, item, timeout=3600)
        return item


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
    name="index_organizations",
)
def index_chunk(self, organization_ids: list[int]) -> int:
    try:
        client = connections.get_connection()
        organizations = Organization.objects.filter(id__in=organization_ids)

        actions = [
            {
                "_index": OrganizationDocument._index._name,
                "_id": org.organization_id,
                "_source": {
                    "id": org.id,
                    "organization_id": org.organization_id,
                    "name": org.name,
                    "website": org.website,
                    "country": org.country.name,
                    "description": org.description,
                    "founded": org.founded,
                    "industry": org.industry.type,
                    "number_of_employees": org.number_of_employees,
                },
                "doc_as_upsert": True,
            }
            for org in organizations
        ]
        _, failed = bulk(client, actions)

        if failed:
            logger.error(f"Failed to index organizations: {failed}")
            raise IndexingError(f"Indexing failed for {len(failed)} organizations")

        return organizations.count()

    except Exception as exc:
        logger.exception("Error during organization indexing")
        raise self.retry(exc=exc)


@shared_task(bind=True, acks_late=True)
def handle_results(self, results, job_id: int) -> None:
    processing_job = ProcessingJob.objects.get(id=job_id)
    processing_job.status = ProcessingJob.Status.SUCCESS
    processing_job.save()
    logger.info(f"Processing job {job_id} completed successfully")


@shared_task
def handle_error(request, exc, traceback, job_id):
    logger.error(f"Task {request.id!r} raised error: {exc!r}")
    processing_job = ProcessingJob.objects.get(id=job_id)
    processing_job.status = ProcessingJob.Status.ERROR
    processing_job.error_message = str(exc)
    processing_job.save()
