from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from organizations.views import (
    create_organization_view,
    get_organization_view,
    search_organization_view,
    upload_csv_view,
)

urlpatterns = [
    # This is to intereact with the API just by clicking on the link provided
    path("", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Normal docs path
    path("api/docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("organizations/", create_organization_view, name="organization-create"),
    path("organizations/upload-csv/", upload_csv_view, name="upload-csv"),
    path("organizations/search/", search_organization_view, name="organization-search"),
    path(
        "organizations/<str:organization_id>/",
        get_organization_view,
        name="organization-get",
    ),
]
