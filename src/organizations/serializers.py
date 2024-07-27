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
