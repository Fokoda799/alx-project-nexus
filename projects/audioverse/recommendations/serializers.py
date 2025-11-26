from rest_framework import serializers
from .models import Recommendation, RecommendationBatch
from audiobooks.serializers import AudiobookDetailSerializer


class RecommendationSerializer(serializers.ModelSerializer):
    audiobook = AudiobookDetailSerializer(read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'audiobook', 'score', 'reason', 'reason_display',
            'is_viewed', 'is_dismissed', 'created_at'
        ]
        read_only_fields = ['id', 'score', 'reason', 'created_at']


class RecommendationBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationBatch
        fields = [
            'id', 'total_generated', 'status', 'error_message',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'total_generated', 'status', 'error_message', 'created_at', 'completed_at']