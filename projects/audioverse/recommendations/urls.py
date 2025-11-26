from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecommendationViewSet

router = DefaultRouter()
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')

urlpatterns = [
    path('', include(router.urls)),
]

# This will create the following endpoints:
# GET    /recommendations/                     - List all recommendations
# GET    /recommendations/{id}/                - Get specific recommendation
# POST   /recommendations/generate/            - Generate new recommendations
# POST   /recommendations/{id}/mark_viewed/    - Mark as viewed
# POST   /recommendations/{id}/dismiss/        - Dismiss recommendation
# GET    /recommendations/batches/             - Get batch history
# GET    /recommendations/stats/               - Get statistics