from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from organizations.serializers import (
    OrganizationCreateSerializer,
)
from organizations.service import create_organization


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
