from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, NarratorViewSet, GenreViewSet, AudiobookViewSet

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'narrators', NarratorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'audiobooks', AudiobookViewSet)

urlpatterns = [
    path('', include(router.urls)),
]