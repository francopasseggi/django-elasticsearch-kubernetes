from elasticsearch_dsl import Q

from organizations.documents import OrganizationDocument
from organizations.models import Country, Industry, Organization, ProcessingJob
from organizations.tasks import process_csv


def create_organization(data):
    country, _ = Country.objects.get_or_create(name=data["country"])
    industry, _ = Industry.objects.get_or_create(type=data["industry"])

    Organization.objects.create(
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


def build_organization_search_query(query_params):
    s = OrganizationDocument.search()

    if query_params.get("q"):
        # Use the all_text field for full-text search with fuzziness
        s = s.query("match", all_text={"query": query_params["q"], "fuzziness": "AUTO"})
    else:
        s = s.query(Q("match_all"))

    filters = [
        ("country", "term", "country__keyword"),
        ("industry", "term", "industry__keyword"),
        ("founded_min", "range", "founded", "gte"),
        ("founded_max", "range", "founded", "lte"),
    ]

    for param, filter_type, field, *args in filters:
        if query_params.get(param):
            if filter_type == "term":
                s = s.filter("term", **{field: query_params[param]})
            elif filter_type == "range":
                s = s.filter("range", **{field: {args[0]: query_params[param]}})

    # Use unique organization_id field as a tiebreaker
    s = s.sort({"_score": {"order": "desc"}}, {"organization_id": {"order": "asc"}})

    return s


def get_organization(organization_id):
    return OrganizationDocument.get(id=organization_id)
