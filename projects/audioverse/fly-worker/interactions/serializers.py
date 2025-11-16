from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import ListeningProgress, Review, Bookmark
from audiobooks.serializers import AudiobookListSerializer
from audiobooks.models import Audiobook

class ListeningProgressSerializer(serializers.ModelSerializer):
    audiobook = AudiobookListSerializer(read_only=True)
    audiobook_id = serializers.PrimaryKeyRelatedField(
        queryset=Audiobook.objects.all(),
        write_only=True,
        source='audiobook'
    )
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = ListeningProgress
        fields = [
            'id', 'audiobook', 'audiobook_id', 'current_position_seconds',
            'is_favorite', 'is_completed', 'progress_percentage',
            'last_listened_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_listened_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Automatically set the user from the request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    audiobook = AudiobookListSerializer(read_only=True)
    audiobook_id = serializers.PrimaryKeyRelatedField(
        queryset=Audiobook.objects.all(),
        write_only=True,
        source='audiobook'
    )

    def validate(self, atrrs):
        user = self.context['request'].user
        audiobook = atrrs.get('audiobook')

        if Review.objects.filter(user=user, audiobook=audiobook).exists():
            raise ValidationError("You have already reviewed this audiobook.")

        return atrrs

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'audiobook', 'audiobook_id', 'rating',
            'review_text', 'helpful_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'helpful_count', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

class BookmarkSerializer(serializers.ModelSerializer):
    audiobook = AudiobookListSerializer(read_only=True)
    audiobook_id = serializers.PrimaryKeyRelatedField(
        queryset=Audiobook.objects.all(),
        write_only=True,
        source='audiobook'
    )

    class Meta:
        model = Bookmark
        fields = [
            'id', 'audiobook', 'audiobook_id', 'timestamp_seconds',
            'note', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)