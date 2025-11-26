from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from django.utils import timezone
from audiobooks.models import Audiobook
from interactions.models import ListeningProgress
from .models import Recommendation, RecommendationBatch

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def generate_recommendations(self, user_id, batch_id=None):
    """Generate audiobook recommendations based on user's listening history"""
    
    try:
        user = User.objects.get(id=user_id)
        
        # Get or create batch
        if batch_id:
            batch = RecommendationBatch.objects.get(id=batch_id)
        else:
            batch = RecommendationBatch.objects.create(
                user=user,
                status='processing'
            )
        
        batch.status = 'processing'
        batch.save()
        
        # Clear old recommendations (optional - keep last 30 days)
        old_recommendations = Recommendation.objects.filter(
            user=user,
            created_at__lt=timezone.now() - timezone.timedelta(days=30)
        )
        old_recommendations.delete()
        
        recommendations_to_create = []
        
        # 1. Genre-based recommendations
        genre_recs = _generate_genre_based_recommendations(user)
        recommendations_to_create.extend(genre_recs)
        
        # 2. Author-based recommendations
        author_recs = _generate_author_based_recommendations(user)
        recommendations_to_create.extend(author_recs)
        
        # 3. Similar audiobooks (based on high-rated books)
        similar_recs = _generate_similar_recommendations(user)
        recommendations_to_create.extend(similar_recs)
        
        # 4. Popular in user's genres
        popular_recs = _generate_popular_recommendations(user)
        recommendations_to_create.extend(popular_recs)
        
        # Bulk create recommendations (ignore duplicates)
        created_count = 0
        for rec_data in recommendations_to_create:
            _, created = Recommendation.objects.get_or_create(
                user=user,
                audiobook=rec_data['audiobook'],
                defaults={
                    'score': rec_data['score'],
                    'reason': rec_data['reason']
                }
            )
            if created:
                created_count += 1
        
        # Update batch
        batch.total_generated = created_count
        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()
        
        return f"Generated {created_count} recommendations for {user.username}"
        
    except User.DoesNotExist:
        if batch_id:
            batch = RecommendationBatch.objects.get(id=batch_id)
            batch.status = 'failed'
            batch.error_message = f"User {user_id} not found"
            batch.save()
        return f"User {user_id} not found"
    
    except Exception as e:
        if batch_id:
            batch = RecommendationBatch.objects.get(id=batch_id)
            batch.status = 'failed'
            batch.error_message = str(e)
            batch.save()
        
        # Retry the task
        raise self.retry(exc=e, countdown=60)


def _generate_genre_based_recommendations(user, limit=15):
    """Generate recommendations based on user's favorite genres"""
    
    # Get user's top genres from completed/high-rated audiobooks
    user_genres = ListeningProgress.objects.filter(
        user=user,
        is_completed=True
    ).values_list('audiobook__genres', flat=True)
    
    if not user_genres:
        return []
    
    # Find audiobooks in those genres that user hasn't interacted with
    recommendations = Audiobook.objects.filter(
        genres__overlap=list(user_genres)
    ).exclude(
        listeningprogress__user=user
    ).annotate(
        popularity=Count('listeningprogress'),
        avg_rating=Avg('review__rating')
    ).order_by('-avg_rating', '-popularity')[:limit]
    
    return [
        {
            'audiobook': audiobook,
            'score': min((audiobook.avg_rating or 0) * 20 + audiobook.popularity * 2, 100),
            'reason': 'genre'
        }
        for audiobook in recommendations
    ]


def _generate_author_based_recommendations(user, limit=10):
    """Generate recommendations based on authors user likes"""
    
    # Get authors from user's favorite books (using authors field which is likely ArrayField)
    favorite_books = ListeningProgress.objects.filter(
        user=user,
        is_favorite=True
    ).select_related('audiobook')
    
    # Collect all unique authors from favorite books
    favorite_authors = set()
    for progress in favorite_books:
        if progress.audiobook.authors:
            favorite_authors.update(progress.audiobook.authors)
    
    if not favorite_authors:
        return []
    
    # Find other books by these authors (using overlap for ArrayField)
    recommendations = Audiobook.objects.filter(
        authors__overlap=list(favorite_authors)
    ).exclude(
        listeningprogress__user=user
    ).annotate(
        popularity=Count('listeningprogress')
    ).order_by('-average_rating', '-popularity')[:limit]
    
    return [
        {
            'audiobook': audiobook,
            'score': 85 + (audiobook.average_rating or 0) * 3,
            'reason': 'author'
        }
        for audiobook in recommendations
    ]


def _generate_similar_recommendations(user, limit=10):
    """Generate recommendations similar to user's high-rated books"""
    
    # Get audiobooks user rated highly
    high_rated_books = ListeningProgress.objects.filter(
        user=user,
        audiobook__reviews__rating__gte=4,
        audiobook__reviews__user=user
    ).values_list('audiobook__id', flat=True)
    
    if not high_rated_books:
        return []
    
    # Find similar audiobooks (same genre + similar rating range)
    similar_books = Audiobook.objects.filter(
        id__in=high_rated_books
    ).first()
    
    if not similar_books:
        return []
    
    recommendations = Audiobook.objects.filter(
        genres__overlap=similar_books.genres,
        average_rating__gte=4.0
    ).exclude(
        listeningprogress__user=user
    ).exclude(
        id=similar_books.id
    )[:limit]
    
    return [
        {
            'audiobook': audiobook,
            'score': 80 + (audiobook.average_rating or 0) * 4,
            'reason': 'similar'
        }
        for audiobook in recommendations
    ]


def _generate_popular_recommendations(user, limit=10):
    """Generate popular audiobooks in user's preferred genres"""
    
    user_genres = ListeningProgress.objects.filter(
        user=user
    ).values_list('audiobook__genres', flat=True)
    
    if not user_genres:
        # Fallback to overall popular books
        recommendations = Audiobook.objects.annotate(
            popularity=Count('listeningprogress')
        ).order_by('-popularity', '-average_rating')[:limit]
    else:
        recommendations = Audiobook.objects.filter(
            genres__overlap=list(user_genres)
        ).exclude(
            listeningprogress__user=user
        ).annotate(
            popularity=Count('listeningprogress')
        ).order_by('-popularity', '-average_rating')[:limit]
    
    return [
        {
            'audiobook': audiobook,
            'score': 70 + audiobook.popularity * 3,
            'reason': 'popular'
        }
        for audiobook in recommendations
    ]


@shared_task
def refresh_recommendations_for_all_users():
    """Periodic task to refresh recommendations for all active users"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get users who have listened to at least one audiobook
    active_users = User.objects.filter(
        listeningprogress__isnull=False
    ).distinct()
    
    for user in active_users:
        generate_recommendations.delay(str(user.id))
    
    return f"Queued recommendation generation for {active_users.count()} users"