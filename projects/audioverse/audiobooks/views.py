from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Author, Narrator, Genre, Audiobook
from django.core.cache import cache
from django.conf import settings
from .utils import get_cached_audiobooks, invalidate_audiobook_cache
from interactions.tasks import test_task
from .serializers import (
    AuthorSerializer, 
    NarratorSerializer, 
    GenreSerializer,
    AudiobookListSerializer,
    AudiobookDetailSerializer
)

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def audiobooks(self, request, pk=None):
        """Get all audiobooks by this author"""
        author = self.get_object()
        audiobooks = author.audiobooks.all()
        serializer = AudiobookListSerializer(audiobooks, many=True)
        return Response(serializer.data)

class NarratorViewSet(viewsets.ModelViewSet):
    queryset = Narrator.objects.all()
    serializer_class = NarratorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def audiobooks(self, request, pk=None):
        """Get all audiobooks narrated by this narrator"""
        narrator = self.get_object()
        audiobooks = narrator.audiobooks.all()
        serializer = AudiobookListSerializer(audiobooks, many=True)
        return Response(serializer.data)

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def audiobooks(self, request, pk=None):
        """Get all audiobooks in this genre"""
        genre = self.get_object()
        audiobooks = genre.audiobooks.all()
        serializer = AudiobookListSerializer(audiobooks, many=True)
        return Response(serializer.data)

class AudiobookViewSet(viewsets.ModelViewSet):
    queryset = Audiobook.objects.select_related().prefetch_related(
        'authors', 'narrators', 'genres'
    ).all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['language', 'genres', 'authors', 'narrators']
    search_fields = ['title', 'description', 'authors__name', 'isbn']
    ordering_fields = ['title', 'release_date', 'average_rating', 'play_count', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AudiobookListSerializer
        return AudiobookDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        """Retrieve audiobook with caching"""
        test_task.delay()  # Example of calling the test task
        audiobook_id = kwargs.get('pk')
        cache_key = f'audiobook_{audiobook_id}'
        
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Cache for 15 minutes
        cache.set(cache_key, serializer.data, settings.CACHE_TTL    )
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Create audiobook and invalidate cache"""
        audiobook = serializer.save()
        # Invalidate list caches
        cache.delete_many(['audiobooks_popular', 'audiobooks_top_rated', 'audiobooks_recent'])

    def perform_update(self, serializer):
        """Update audiobook and invalidate cache"""
        audiobook = serializer.save()
        invalidate_audiobook_cache(audiobook.id)

    def perform_destroy(self, instance):
        """Delete audiobook and invalidate cache"""
        audiobook_id = instance.id
        instance.delete()
        invalidate_audiobook_cache(audiobook_id)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular audiobooks by play count"""
        cache_key = 'audiobooks_popular'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)

        audiobooks = self.get_queryset().order_by('-play_count')[:20]
        serializer = AudiobookListSerializer(audiobooks, many=True)

        cache.set(cache_key, serializer.data, settings.CACHE_TTL)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get highest rated audiobooks"""
        cache_key = 'audiobooks_top_rated'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
            
        audiobooks = self.get_queryset().filter(
            total_ratings__gte=5
        ).order_by('-average_rating')[:20]
        serializer = AudiobookListSerializer(audiobooks, many=True)
        cache.set(cache_key, serializer.data, settings.CACHE_TTL)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently added audiobooks"""
        cache_key = "audiobooks_recent"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
             
        audiobooks = self.get_queryset().order_by('-created_at')[:20]
        serializer = AudiobookListSerializer(audiobooks, many=True)
        cache.set(cache_key, serializer.data, settings.CACHE_TTL)
        return Response(serializer.data)