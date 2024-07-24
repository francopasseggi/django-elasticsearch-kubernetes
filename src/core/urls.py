from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from organizations.views import create_organization_view

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("organizations/", create_organization_view, name="organization-create"),
]
