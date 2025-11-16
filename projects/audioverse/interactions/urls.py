from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListeningProgressViewSet, ReviewViewSet, BookmarkViewSet

router = DefaultRouter()
router.register(r'progress', ListeningProgressViewSet, basename='progress')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')

urlpatterns = [
    path('', include(router.urls)),
]