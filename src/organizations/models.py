from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Industry(models.Model):
    type = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.type


class Organization(models.Model):
    organization_id = models.CharField(unique=True, db_index=True, max_length=30)
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    founded = models.PositiveIntegerField()
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    number_of_employees = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class ProcessingJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        SUCCESS = "SUCCESS"
        ERROR = "ERROR"

    file = models.FileField(upload_to="uploads/")
    status = models.CharField(choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.file.name
