from unittest.mock import MagicMock, patch

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.urls import reverse
from elasticsearch_dsl import Search
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient, APIRequestFactory

from organizations.documents import OrganizationDocument
from organizations.models import Country, Industry, Organization, ProcessingJob
from organizations.paginators import ElasticsearchCursorPagination
from organizations.services import build_organization_search_query, create_organization
from organizations.tasks import (
    CacheManager,
    ChunkProcessor,
    FileProcessor,
    handle_error,
    handle_results,
    index_chunk,
    process_csv,
)


@pytest.mark.django_db
def test_create_organization():
    data = {
        "organization_id": "org123",
        "name": "Test Org",
        "website": "http://testorg.com",
        "country": "USA",
        "description": "A test organization",
        "founded": 2000,
        "industry": "Technology",
        "number_of_employees": 100,
    }

    organization = create_organization(data)

    assert isinstance(organization, Organization)
    assert organization.organization_id == "org123"
    assert organization.name == "Test Org"
    assert organization.country.name == "USA"
    assert organization.industry.type == "Technology"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_process_csv():
    with patch("organizations.services.process_csv") as mock:
        yield mock


@pytest.fixture
def mock_es():
    with (
        patch("django_elasticsearch_dsl.signals.CelerySignalProcessor.handle_save") as mock_save,
        patch("elasticsearch_dsl.Search.execute") as mock_execute,
        patch("organizations.documents.OrganizationDocument.get") as mock_get,
    ):
        yield {"save": mock_save, "execute": mock_execute, "get": mock_get}


@pytest.mark.django_db
def test_upload_csv(api_client, mock_process_csv):
    url = reverse("upload-csv")
    file_content = b"Index,Organization Id,Name,Website,Country,Description,Founded,Industry,Number of employees\n1,org123,Test Org,http://testorg.com,USA,A test organization,2000,Technology,100"
    file = SimpleUploadedFile("test.csv", file_content, content_type="text/csv")

    response = api_client.post(url, {"file": file}, format="multipart")

    assert response.status_code == status.HTTP_201_CREATED
    assert "file" in response.data
    assert "processing_status" in response.data
    assert response.data["processing_status"] == ProcessingJob.Status.PENDING
    mock_process_csv.delay.assert_called_once()


@pytest.mark.django_db
def test_build_organization_search_query():
    query_params = {
        "q": "test",
        "country": "USA",
        "industry": "Technology",
        "founded_min": 2000,
        "founded_max": 2020,
    }

    search_query = build_organization_search_query(query_params)

    assert isinstance(search_query, Search)
    assert "all_text" in str(search_query.to_dict()["query"])
    assert "country.keyword" in str(search_query.to_dict()["query"]["bool"])
    assert "industry.keyword" in str(search_query.to_dict()["query"]["bool"])
    assert "founded" in str(search_query.to_dict()["query"]["bool"])


@pytest.mark.django_db
def test_organization_retrieve(api_client, mock_es):
    organization = Organization.objects.create(
        organization_id="org123",
        name="Test Org",
        website="http://testorg.com",
        country=Country.objects.create(name="USA"),
        description="A test organization",
        founded=2000,
        industry=Industry.objects.create(type="Technology"),
        number_of_employees=100,
    )

    # Mock the Elasticsearch get response
    mock_es["get"].return_value = OrganizationDocument(
        meta={"id": organization.organization_id},
        organization_id=organization.organization_id,
        name=organization.name,
        website=organization.website,
        country=organization.country.name,
        description=organization.description,
        founded=organization.founded,
        industry=organization.industry.type,
        number_of_employees=organization.number_of_employees,
    )

    url = reverse("organization-get", kwargs={"organization_id": organization.organization_id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Test Org"
    assert response.data["organization_id"] == "org123"

    # Verify that the get method was called on the ES document
    mock_es["get"].assert_called_once_with(id=organization.organization_id)


@pytest.mark.django_db
def test_organization_model():
    country = Country.objects.create(name="USA")
    industry = Industry.objects.create(type="Technology")

    organization = Organization.objects.create(
        organization_id="org123",
        name="Test Org",
        website="http://testorg.com",
        country=country,
        description="A test organization",
        founded=2000,
        industry=industry,
        number_of_employees=100,
    )

    assert str(organization) == "Test Org"
    assert organization.country.name == "USA"
    assert organization.industry.type == "Technology"


@pytest.mark.django_db
def test_process_csv_error():
    with patch("organizations.tasks.ProcessingJob.objects.get") as mock_get:
        mock_get.side_effect = ProcessingJob.DoesNotExist

        process_csv(999)

        mock_get.assert_called_once_with(id=999)


@pytest.mark.django_db
def test_index_chunk_success():
    with patch("elasticsearch.helpers.bulk") as mock_bulk:
        mock_bulk.return_value = (2, [])

        result = index_chunk([1, 2])

        assert result == 0
        mock_bulk.assert_not_called()


@pytest.mark.django_db
def test_handle_results():
    processing_job = ProcessingJob.objects.create(file=None)

    handle_results([1, 2, 3], processing_job.id)

    processing_job.refresh_from_db()
    assert processing_job.status == ProcessingJob.Status.SUCCESS


@pytest.mark.django_db
def test_handle_error():
    processing_job = ProcessingJob.objects.create(file=None)

    exc = Exception("Test exception")
    handle_error(MagicMock(id="task_id"), exc, None, processing_job.id)

    processing_job.refresh_from_db()
    assert processing_job.status == ProcessingJob.Status.ERROR
    assert processing_job.error_message == "Test exception"


@pytest.mark.django_db
def test_chunk_processor_process_chunk():
    chunk = [
        "Index,Organization Id,Name,Website,Country,Description,Founded,Industry,Number of employees",
        "1,abc123,Acme Inc.,https://acme.com,United States,A fictional company,1900,Manufacturing,1000",
    ]

    with patch("organizations.tasks.Organization.objects.bulk_create") as mock_bulk_create:
        organizations = [Organization(organization_id="abc123")]
        mock_bulk_create.return_value = organizations

        result = ChunkProcessor.process_chunk(chunk)

        assert result == [org.id for org in organizations]
        mock_bulk_create.assert_called_once()


@pytest.mark.django_db
def test_chunk_processor_get_or_create():
    with patch("organizations.tasks.CacheManager.get_or_create") as mock_get_or_create:
        mock_country = Country(name="United States")
        mock_get_or_create.return_value = mock_country

        country = ChunkProcessor.get_or_create_country("United States")

        assert country == mock_country
        mock_get_or_create.assert_called_once_with(
            Country, "country_United States", name="United States"
        )

    with patch("organizations.tasks.CacheManager.get_or_create") as mock_get_or_create:
        mock_industry = Industry(type="Manufacturing")
        mock_get_or_create.return_value = mock_industry

        industry = ChunkProcessor.get_or_create_industry("Manufacturing")

        assert industry == mock_industry
        mock_get_or_create.assert_called_once_with(
            Industry, "industry_Manufacturing", type="Manufacturing"
        )


def test_file_processor_get_chunks():
    csv_content = b"header1,header2\nvalue1,value2\nvalue3,value4"
    file = ContentFile(csv_content, name="test.csv")

    file_processor = FileProcessor(file, chunk_size=1)
    chunks = list(file_processor.get_chunks())

    assert len(chunks) == 3


def test_cache_manager_get_or_create():
    with (
        patch("organizations.tasks.cache.get") as mock_get,
        patch("organizations.tasks.cache.set") as mock_set,
        patch("organizations.models.Country.objects.get_or_create") as mock_get_or_create,
    ):
        mock_get.return_value = None
        mock_country = Country(name="United States")
        mock_get_or_create.return_value = (mock_country, True)

        country = CacheManager.get_or_create(Country, "country_United States", name="United States")

        assert country == mock_country
        mock_get.assert_called_once_with("country_United States")
        mock_set.assert_called_once_with("country_United States", mock_country, timeout=3600)
        mock_get_or_create.assert_called_once_with(name="United States")


@pytest.fixture
def pagination():
    return ElasticsearchCursorPagination()


@pytest.fixture
def mock_queryset():
    mock = MagicMock()
    mock.__getitem__.return_value = mock
    return mock


@pytest.fixture
def request_factory():
    return APIRequestFactory()


def create_mock_hit(id, sort):
    return MagicMock(meta=MagicMock(sort=sort), id=id)


def test_paginate_queryset_no_cursor(pagination, mock_queryset, request_factory):
    request = request_factory.get("/")
    request.query_params = QueryDict("")

    mock_queryset.__iter__.return_value = [create_mock_hit(i, [i]) for i in range(11)]

    result = pagination.paginate_queryset(mock_queryset, request)

    assert len(result) == 10
    assert pagination.cursor is None
    assert not mock_queryset.extra.called


def test_get_paginated_response(pagination, request_factory):
    pagination.base_url = "http://testserver/"
    pagination.request_query_params = QueryDict("page_size=10", mutable=True)
    pagination.page = [create_mock_hit(i, [i]) for i in range(11)]

    data = [{"id": i} for i in range(10)]
    response = pagination.get_paginated_response(data)

    assert response.data["results"] == data
    assert response.data["next"] is not None
    assert "cursor=" in response.data["next"]


def test_get_next_link_no_next_page(pagination):
    pagination.page = [create_mock_hit(i, [i]) for i in range(5)]
    pagination.page_size = 10

    assert pagination.get_next_link() is None


def test_encode_decode_cursor(pagination):
    cursor = [10, "test"]
    encoded = pagination.encode_cursor(cursor)
    decoded = pagination.decode_cursor(encoded)

    assert decoded == cursor


def test_decode_invalid_cursor(pagination):
    with pytest.raises(NotFound, match="Invalid cursor"):
        pagination.decode_cursor("invalid_cursor")


def test_paginate_queryset_custom_page_size(pagination, mock_queryset, request_factory):
    request = request_factory.get("/?page_size=5")
    request.query_params = QueryDict("page_size=5")

    mock_queryset.__iter__.return_value = [create_mock_hit(i, [i]) for i in range(6)]

    result = pagination.paginate_queryset(mock_queryset, request)

    assert len(result) == 5
    assert pagination.page_size == 5


def test_paginate_queryset_max_page_size(pagination, mock_queryset, request_factory):
    request = request_factory.get("/?page_size=200")
    request.query_params = QueryDict("page_size=200")

    mock_queryset.__iter__.return_value = [create_mock_hit(i, [i]) for i in range(101)]

    result = pagination.paginate_queryset(mock_queryset, request)

    assert len(result) == 100  # max_page_size


def test_paginate_queryset_invalid_page_size(pagination, mock_queryset, request_factory):
    request = request_factory.get("/?page_size=invalid")
    request.query_params = QueryDict("page_size=invalid")

    mock_queryset.__iter__.return_value = [create_mock_hit(i, [i]) for i in range(11)]

    result = pagination.paginate_queryset(mock_queryset, request)

    assert len(result) == 10  # default page_size
    assert pagination.page_size == 10  # default page_size
