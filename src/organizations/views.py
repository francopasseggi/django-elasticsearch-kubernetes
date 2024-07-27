from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from organizations.serializers import (
    OrganizationCreateSerializer,
)
from organizations.service import create_organization, create_processing_job

from .serializers import (
    FileUploadResponseSerializer,
    FileUploadSerializer,
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
def upload_csv(request):
    serializer = FileUploadSerializer(data=request.data)
    if serializer.is_valid():
        result = create_processing_job(serializer.validated_data["file"])
        response_serializer = FileUploadResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
