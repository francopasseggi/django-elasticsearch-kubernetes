from rest_framework import serializers

from organizations.models import ProcessingJob


class OrganizationCreateSerializer(serializers.Serializer):
    organization_id = serializers.CharField()
    name = serializers.CharField()
    website = serializers.URLField()
    country = serializers.CharField()
    description = serializers.CharField()
    founded = serializers.IntegerField()
    industry = serializers.CharField()
    number_of_employees = serializers.IntegerField()


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = ["file"]


class FileUploadResponseSerializer(serializers.Serializer):
    file = serializers.CharField()
    processing_status = serializers.CharField()


class OrganizationListResponseSerializer(serializers.Serializer):
    next = serializers.URLField()
    results = OrganizationCreateSerializer(many=True)


class OrganizationListRequestQueryParamsSerializer(serializers.Serializer):
    q = serializers.CharField(required=False)
    organization_id = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    industry = serializers.CharField(required=False)
    founded_min = serializers.IntegerField(required=False)
    founded_max = serializers.IntegerField(required=False)
    cursor = serializers.CharField(required=False)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)
