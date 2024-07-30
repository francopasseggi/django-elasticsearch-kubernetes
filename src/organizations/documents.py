from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer

from organizations.models import Organization

# Define a custom analyzer for the all_text field
all_text_analyzer = analyzer(
    "all_text_analyzer",
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
)


@registry.register_document
class OrganizationDocument(Document):
    organization_id = fields.KeywordField()
    name = fields.TextField(
        fields={
            "keyword": fields.KeywordField(),
            "text": fields.TextField(analyzer="standard"),
        },
        copy_to="all_text",
    )
    website = fields.KeywordField(copy_to="all_text")
    country = fields.TextField(
        fields={
            "keyword": fields.KeywordField(),
            "text": fields.TextField(analyzer="all_text_analyzer"),
        },
        copy_to="all_text",
    )
    description = fields.TextField(
        fields={
            "text": fields.TextField(analyzer="all_text_analyzer"),
        },
        copy_to="all_text",
    )
    founded = fields.IntegerField(copy_to="all_text")
    industry = fields.TextField(
        fields={
            "keyword": fields.KeywordField(),
            "text": fields.TextField(analyzer="all_text_analyzer"),
        },
        copy_to="all_text",
    )
    number_of_employees = fields.IntegerField(copy_to="all_text")

    all_text = fields.TextField(analyzer=all_text_analyzer)

    class Index:
        name = "organizations"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {"all_text_analyzer": all_text_analyzer.get_analysis_definition()}
            },
        }

    class Django:
        model = Organization
        fields = [
            "id",
        ]

    def prepare_country(self, instance):
        return instance.country.name

    def prepare_industry(self, instance):
        return instance.industry.type

    @classmethod
    def generate_id(cls, object_instance):
        return object_instance.organization_id
