from celery import shared_task
from django.db.models import Count, Q
from django.core.mail import send_mail
from .models import ListeningProgress, Review
from audiobooks.models import Audiobook

@shared_task
def update_audiobook_statistics(audiobook_id):
    """Update cached statistics for an audiobook"""
    try:
        audiobook = Audiobook.objects.get(id=audiobook_id)   # 1. Get the audiobook by ID
        
        # Update play count
        play_count = ListeningProgress.objects.filter(       # 2. Count listening progress entries for the audiobook
            audiobook=audiobook
        ).count()
        
        audiobook.play_count = play_count                    # 3. Update the audiobook's play_count field
        audiobook.save(update_fields=['play_count'])         # 4. Save the audiobook instance
        
        return f"Updated statistics for {audiobook.title}"
    except Audiobook.DoesNotExist:
        return f"Audiobook {audiobook_id} not found"

@shared_task
def generate_recommendations(user_id):
    """Generate audiobook recommendations based on user's listening history"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        
        # Get user's favorite genres from listening history
        user_genres = ListeningProgress.objects.filter(
            user=user,
            is_completed=True
        ).values_list('audiobook__genres', flat=True)
        
        # Find popular audiobooks in those genres that user hasn't listened to
        recommendations = Audiobook.objects.filter(
            genres__in=user_genres
        ).exclude(
            listeningprogress__user=user
        ).annotate(
            popularity=Count('listeningprogress')
        ).order_by('-popularity', '-average_rating')[:10]
        
        return f"Generated {recommendations.count()} recommendations for {user.username}"
    except User.DoesNotExist:
        return f"User {user_id} not found"

@shared_task
def send_completion_notification(user_id, audiobook_id):
    """Send notification when user completes an audiobook"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        audiobook = Audiobook.objects.get(id=audiobook_id)
        
        # In production, you'd send an actual email or push notification
        # For now, we'll just log it
        print(f"Notification: {user.username} completed {audiobook.title}")
        
        # Trigger recommendation generation
        generate_recommendations.delay(user_id)
        
        return f"Sent completion notification to {user.username}"
    except (User.DoesNotExist, Audiobook.DoesNotExist):
        return "User or audiobook not found"

@shared_task
def cleanup_old_bookmarks(days=90):
    """Remove bookmarks older than specified days"""
    from django.utils import timezone
    from datetime import timedelta
    from .models import Bookmark
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count = Bookmark.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    return f"Deleted {deleted_count} old bookmarks"