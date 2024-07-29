from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from elasticsearch.exceptions import NotFoundError as ElasticsearchNotFoundError
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from organizations.paginators import ElasticsearchCursorPagination
from organizations.serializers import (
    FileUploadResponseSerializer,
    FileUploadSerializer,
    OrganizationCreateSerializer,
    OrganizationListRequestQueryParamsSerializer,
)
from organizations.services import (
    build_organization_search_query,
    create_organization,
    create_processing_job,
    get_organization,
)


@extend_schema(
    request=OrganizationCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=OrganizationCreateSerializer,
            description="Organization successfully created",
        ),
        400: OpenApiResponse(description="Bad request. Validation errors in the provided data."),
    },
    description="Create a new organization.",
)
@api_view(["POST"])
def create_organization_view(request):
    serializer = OrganizationCreateSerializer(data=request.data)
    if serializer.is_valid():
        create_organization(serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {"file": {"type": "string", "format": "binary"}},
        }
    },
    responses={
        201: OpenApiResponse(
            response=FileUploadResponseSerializer,
            description="File successfully uploaded and processing started.",
        ),
        400: OpenApiResponse(description="Bad request. Validation errors in the uploaded data."),
    },
)
@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_csv_view(request):
    serializer = FileUploadSerializer(data=request.data)
    if serializer.is_valid():
        result = create_processing_job(serializer.validated_data["file"])
        response_serializer = FileUploadResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    parameters=[
        OpenApiParameter(name="q", description="Search query", type=str, required=False),
        OpenApiParameter(
            name="country",
            description="Filter by exact country name (case sensitive)",
            type=str,
            required=False,
        ),
        OpenApiParameter(
            name="industry",
            description="Filter by exact industry type (case sensitive)",
            type=str,
            required=False,
        ),
        OpenApiParameter(
            name="founded_min",
            description="Filter by minimum founding year",
            type=int,
            required=False,
        ),
        OpenApiParameter(
            name="founded_max",
            description="Filter by maximum founding year",
            type=int,
            required=False,
        ),
        OpenApiParameter(
            name="cursor", description="Cursor for pagination", type=str, required=False
        ),
        OpenApiParameter(
            name="page_size",
            description="Page size for pagination",
            type={"type": "string", "minimum": 1, "maximum": 100},
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=OrganizationCreateSerializer(many=True),
            description="Search results",
        ),
        400: OpenApiResponse(description="Bad request. Validation errors in the query parameters."),
        404: OpenApiResponse(description="Index not found"),
    },
    description="List and search organizations with optional filters and pagination.",
)
@api_view(["GET"])
def search_organization_view(request):
    try:
        # Validate and build the search query
        OrganizationListRequestQueryParamsSerializer(data=request.query_params).is_valid(
            raise_exception=True
        )

        search_query = build_organization_search_query(request.query_params)
        paginator = ElasticsearchCursorPagination()

        page = paginator.paginate_queryset(search_query, request)

        serializer = OrganizationCreateSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    except ElasticsearchNotFoundError as e:
        return Response({"detail": e.error}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="organization_id",
            description="Organization ID",
            type=str,
            location=OpenApiParameter.PATH,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=OrganizationCreateSerializer,
            description="Organization details",
        ),
        404: OpenApiResponse(description="Organization not found"),
    },
    description="Retrieve details of a specific organization.",
)
@api_view(["GET"])
def get_organization_view(request, organization_id):
    try:
        organization = get_organization(organization_id)
        serializer = OrganizationCreateSerializer(organization)
        return Response(serializer.data)
    except ElasticsearchNotFoundError as e:
        return Response({"detail": e.error}, status=status.HTTP_404_NOT_FOUND)
