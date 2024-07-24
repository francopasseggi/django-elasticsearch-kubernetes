from rest_framework import serializers


class OrganizationCreateSerializer(serializers.Serializer):
    organization_id = serializers.CharField()
    name = serializers.CharField()
    website = serializers.URLField()
    country = serializers.CharField()
    description = serializers.CharField()
    founded = serializers.IntegerField()
    industry = serializers.CharField()
    number_of_employees = serializers.IntegerField()
