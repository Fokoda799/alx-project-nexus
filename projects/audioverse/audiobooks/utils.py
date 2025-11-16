from django.core.cache import cache
from django.conf import settings

def get_cached_audiobooks(key, queryset, timeout=settings.CACHE_TTL):
    """Cache audiobook querysets"""
    cached_data = cache.get(key)
    if cached_data is not None:
        return cached_data
    
    # Evaluate queryset
    data = list(queryset)
    cache.set(key, data, timeout)
    return data

def invalidate_audiobook_cache(audiobook_id):
    """Invalidate cached data when audiobook is updated"""
    cache_keys = [
        f'audiobook_{audiobook_id}',
        'audiobooks_popular',
        'audiobooks_top_rated',
        'audiobooks_recent'
    ]
    cache.delete_many(cache_keys)