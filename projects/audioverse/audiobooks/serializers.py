from rest_framework import serializers
from .models import Author, Narrator, Genre, Audiobook
import logging

logger = logging.getLogger("audiobook_serializer")

class AuthorSerializer(serializers.ModelSerializer):
    audiobooks_count = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'photo', 'social_links', 'audiobooks_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_audiobooks_count(self, obj):
        return obj.audiobooks.count()

class NarratorSerializer(serializers.ModelSerializer):
    audiobooks_count = serializers.SerializerMethodField()

    class Meta:
        model = Narrator
        fields = ['id', 'name', 'bio', 'photo', 'social_links', 'audiobooks_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_audiobooks_count(self, obj):
        return obj.audiobooks.count()

class GenreSerializer(serializers.ModelSerializer):
    audiobooks_count = serializers.SerializerMethodField()

    class Meta:
        model = Genre
        fields = ['id', 'name', 'description', 'audiobooks_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_audiobooks_count(self, obj):
        return obj.audiobooks.count()

class AudiobookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    authors = serializers.StringRelatedField(many=True)
    narrators = serializers.StringRelatedField(many=True)
    genres = serializers.StringRelatedField(many=True)
    duration_formatted = serializers.ReadOnlyField()

    class Meta:
        model = Audiobook
        fields = [
            'id', 'title', 'cover_image', 'authors', 'narrators', 
            'genres', 'duration_seconds', 'duration_formatted', 
            'average_rating', 'total_ratings', 'language'
        ]

class AudiobookDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with full related objects"""
    authors = AuthorSerializer(many=True, read_only=True)
    narrators = NarratorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    
    # Write fields for creating/updating
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Author.objects.all(), 
        write_only=True, 
        source='authors'
    )
    narrator_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Narrator.objects.all(), 
        write_only=True, 
        source='narrators'
    )
    genre_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Genre.objects.all(), 
        write_only=True, 
        source='genres'
    )

    class Meta:
        model = Audiobook
        fields = [
            'id', 'title', 'description', 'cover_image', 'audio_file',
            'duration_seconds', 'duration_formatted', 'release_date',
            'language', 'publisher', 'isbn', 'authors', 'narrators', 'genres',
            'average_rating', 'total_ratings', 'total_reviews', 'play_count',
            'created_at', 'updated_at',
            # Write-only fields
            'author_ids', 'narrator_ids', 'genre_ids'
        ]
        read_only_fields = [
            'id', 'average_rating', 'total_ratings', 'total_reviews', 
            'play_count', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        logger.debug("🔵 [SERIALIZER.CREATE] validated_data: %s", validated_data)

        authors = validated_data.pop("authors", [])
        narrators = validated_data.pop("narrators", [])
        genres = validated_data.pop("genres", [])

        audiobook = Audiobook.objects.create(**validated_data)
        logger.debug("🟢 [SERIALIZER.CREATE] Audiobook created with id=%s", audiobook.id)

        audiobook.authors.set(authors)
        audiobook.narrators.set(narrators)
        audiobook.genres.set(genres)

        logger.debug("🟣 [SERIALIZER.CREATE] M2M linked => authors=%s narrators=%s genres=%s",
                     [a.id for a in authors],
                     [n.id for n in narrators],
                     [g.id for g in genres])

        return audiobook

    def to_representation(self, instance):
        logger.debug("🟡 [SERIALIZER.REPR] Representing Audiobook id=%s", instance.id)
        return super().to_representation(instance)