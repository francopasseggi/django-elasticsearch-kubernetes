import pytest

from organizations.models import Organization
from organizations.services import create_organization


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
