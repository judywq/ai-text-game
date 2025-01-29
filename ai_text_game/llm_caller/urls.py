from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ActiveModelsView
from .views import APIRequestViewSet
from .views import GameScenarioViewSet
from .views import GameStoryViewSet

router = DefaultRouter()
router.register(r"requests", APIRequestViewSet, basename="api-request")
router.register(r"game-scenarios", GameScenarioViewSet, basename="game-scenario")
router.register(r"game-stories", GameStoryViewSet, basename="game-story")

urlpatterns = [
    path("", include(router.urls)),
    path("llm-models/", ActiveModelsView.as_view(), name="active-models"),
]
