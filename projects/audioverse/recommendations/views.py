from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Recommendation, RecommendationBatch
from .serializers import RecommendationSerializer, RecommendationBatchSerializer
from .tasks import generate_recommendations


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and managing user recommendations
    
    Endpoints:
    - GET /recommendations/ - List all recommendations for current user
    - GET /recommendations/{id}/ - Get specific recommendation
    - POST /recommendations/generate/ - Trigger recommendation generation
    - POST /recommendations/{id}/mark_viewed/ - Mark as viewed
    - POST /recommendations/{id}/dismiss/ - Dismiss recommendation
    - GET /recommendations/batches/ - Get recommendation batch history
    """
    
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get recommendations for current user only"""
        user = self.request.user
        queryset = Recommendation.objects.filter(user=user)
        
        # Filter options
        include_dismissed = self.request.query_params.get('include_dismissed', 'false').lower() == 'true'
        reason = self.request.query_params.get('reason')
        
        if not include_dismissed:
            queryset = queryset.filter(is_dismissed=False)
        
        if reason:
            queryset = queryset.filter(reason=reason)
        
        return queryset.select_related('audiobook')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Trigger recommendation generation for current user"""
        user = request.user
        
        # Check if there's already a pending/processing batch
        existing_batch = RecommendationBatch.objects.filter(
            user=user,
            status__in=['pending', 'processing']
        ).first()
        
        if existing_batch:
            return Response({
                'message': 'Recommendation generation already in progress',
                'batch': RecommendationBatchSerializer(existing_batch).data
            }, status=status.HTTP_200_OK)
        
        # Create new batch
        batch = RecommendationBatch.objects.create(
            user=user,
            status='pending'
        )
        
        # Queue the task
        generate_recommendations.delay(str(user.id), str(batch.id))
        
        return Response({
            'message': 'Recommendation generation started',
            'batch': RecommendationBatchSerializer(batch).data
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Mark a recommendation as viewed"""
        recommendation = self.get_object()
        recommendation.is_viewed = True
        recommendation.save()
        
        return Response({
            'message': 'Recommendation marked as viewed',
            'recommendation': RecommendationSerializer(recommendation).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss a recommendation"""
        recommendation = self.get_object()
        recommendation.is_dismissed = True
        recommendation.save()
        
        return Response({
            'message': 'Recommendation dismissed',
            'recommendation': RecommendationSerializer(recommendation).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def batches(self, request):
        """Get recommendation batch history"""
        user = request.user
        batches = RecommendationBatch.objects.filter(user=user)[:10]
        serializer = RecommendationBatchSerializer(batches, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get recommendation statistics"""
        user = request.user
        
        total = Recommendation.objects.filter(user=user).count()
        viewed = Recommendation.objects.filter(user=user, is_viewed=True).count()
        dismissed = Recommendation.objects.filter(user=user, is_dismissed=False).count()
        active = Recommendation.objects.filter(user=user, is_dismissed=False, is_viewed=False).count()
        
        # Latest batch
        latest_batch = RecommendationBatch.objects.filter(user=user).first()
        
        return Response({
            'total_recommendations': total,
            'viewed_count': viewed,
            'dismissed_count': dismissed,
            'active_count': active,
            'latest_batch': RecommendationBatchSerializer(latest_batch).data if latest_batch else None
        })