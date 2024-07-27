from organizations.models import Country, Industry, Organization, ProcessingJob
from organizations.tasks import process_csv


def create_organization(data):
    country, _ = Country.objects.get_or_create(name=data["country"])
    industry, _ = Industry.objects.get_or_create(type=data["industry"])

    return Organization.objects.create(
        organization_id=data["organization_id"],
        name=data["name"],
        website=data["website"],
        country=country,
        description=data["description"],
        founded=data["founded"],
        industry=industry,
        number_of_employees=data["number_of_employees"],
    )


def create_processing_job(file):
    processing_job = ProcessingJob.objects.create(file=file)
    process_csv.delay(processing_job.id)
    return {
        "file": processing_job.file.url,
        "processing_status": processing_job.status,
    }
