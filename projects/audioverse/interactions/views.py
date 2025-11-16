from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import F
from .models import ListeningProgress, Review, Bookmark
from .tasks import update_audiobook_statistics, send_completion_notification
from .serializers import (
    ListeningProgressSerializer,
    ReviewSerializer,
    BookmarkSerializer
)
from audiobooks.models import Audiobook

class ListeningProgressViewSet(viewsets.ModelViewSet):
    serializer_class = ListeningProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ListeningProgress.objects.filter(
            user=self.request.user
        ).select_related('audiobook')

    @action(detail=False, methods=['get'])
    def continue_listening(self, request):
        """Get audiobooks the user is currently listening to"""
        progress = self.get_queryset().filter(
            is_completed=False
        ).order_by('-last_listened_at')[:10]
        serializer = self.get_serializer(progress, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get user's favorite audiobooks"""
        favorites = self.get_queryset().filter(is_favorite=True)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed audiobooks"""
        completed = self.get_queryset().filter(is_completed=True)
        serializer = self.get_serializer(completed, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status of an audiobook"""
        progress = self.get_object()
        progress.is_favorite = not progress.is_favorite
        progress.save()
        serializer = self.get_serializer(progress)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark audiobook as completed"""
        progress = self.get_object()
        progress.is_completed = True
        progress.save()

        send_completion_notification.delay(
            str(request.user.id),
            str(progress.audiobook.id)
        )
        update_audiobook_statistics.delay(str(progress.audiobook.id))
        
        serializer = self.get_serializer(progress)
        return Response(serializer.data)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'audiobook')
        
        # Filter by audiobook if provided
        audiobook_id = self.request.query_params.get('audiobook')
        if audiobook_id:
            queryset = queryset.filter(audiobook_id=audiobook_id)
        
        # Filter by user if provided
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Create review and update audiobook ratings"""
        user = self.request.user
        audiobook = serializer.validated_data['audiobook']

        if Review.objects.filter(user=user, audiobook=audiobook).exists():
            raise ValidationError({"detail": "You already reviewed this audiobook."})
        
        review = serializer.save()
        self._update_audiobook_rating(review.audiobook)

    def perform_update(self, serializer):
        """Update review and recalculate ratings"""
        review = serializer.save()
        self._update_audiobook_rating(review.audiobook)

    def perform_destroy(self, instance):
        """Delete review and recalculate ratings"""
        audiobook = instance.audiobook
        instance.delete()
        self._update_audiobook_rating(audiobook)

    def _update_audiobook_rating(self, audiobook):
        """Recalculate audiobook's average rating"""
        from django.db.models import Avg, Count
        stats = Review.objects.filter(audiobook=audiobook).aggregate(
            avg_rating=Avg('rating'),
            total=Count('id')
        )
        audiobook.average_rating = stats['avg_rating'] or 0.00
        audiobook.total_ratings = stats['total']
        audiobook.total_reviews = stats['total']
        audiobook.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_helpful(self, request, pk=None):
        """Increment helpful count for a review"""
        review = self.get_object()
        review.helpful_count = F('helpful_count') + 1
        review.save()
        review.refresh_from_db()
        serializer = self.get_serializer(review)
        return Response(serializer.data)

class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Bookmark.objects.filter(user=self.request.user).select_related('audiobook')
        
        # Filter by audiobook if provided
        audiobook_id = self.request.query_params.get('audiobook')
        if audiobook_id:
            queryset = queryset.filter(audiobook_id=audiobook_id)
        
        return queryset.order_by('audiobook', 'timestamp_seconds')