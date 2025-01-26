from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ActiveModelsView
from .views import APIRequestViewSet

router = DefaultRouter()
router.register(r"requests", APIRequestViewSet, basename="api-request")

urlpatterns = [
    path("", include(router.urls)),
    path("llm-models/", ActiveModelsView.as_view(), name="active-models"),
]
