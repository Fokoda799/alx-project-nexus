from django.core.management.base import BaseCommand
from django.core.cache import cache
from audiobooks.models import Audiobook
from audiobooks.serializers import AudiobookListSerializer

class Command(BaseCommand):
    help = 'Warm up the cache with popular data'

    def handle(self, *args, **options):
        self.stdout.write('Warming cache...')
        
        # Cache popular audiobooks
        popular = Audiobook.objects.order_by('-play_count')[:20]
        serializer = AudiobookListSerializer(popular, many=True)
        cache.set('audiobooks_popular', serializer.data, 3600)
        self.stdout.write(self.style.SUCCESS(f'Cached {len(popular)} popular audiobooks'))
        
        # Cache top rated
        top_rated = Audiobook.objects.filter(
            total_ratings__gte=5
        ).order_by('-average_rating')[:20]
        serializer = AudiobookListSerializer(top_rated, many=True)
        cache.set('audiobooks_top_rated', serializer.data, 3600)
        self.stdout.write(self.style.SUCCESS(f'Cached {len(top_rated)} top rated audiobooks'))
        
        # Cache recent
        recent = Audiobook.objects.order_by('-created_at')[:20]
        serializer = AudiobookListSerializer(recent, many=True)
        cache.set('audiobooks_recent', serializer.data, 3600)
        self.stdout.write(self.style.SUCCESS(f'Cached {len(recent)} recent audiobooks'))
        
        self.stdout.write(self.style.SUCCESS('Cache warming complete!'))