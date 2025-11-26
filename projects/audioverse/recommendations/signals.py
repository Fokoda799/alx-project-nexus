from django.db.models.signals import post_save
from django.dispatch import receiver
from interactions.models import ListeningProgress
from .tasks import generate_recommendations


@receiver(post_save, sender=ListeningProgress)
def trigger_recommendations_on_completion(sender, instance, created, **kwargs):
    """
    Auto-generate recommendations when user completes an audiobook
    or marks one as favorite
    """
    
    # Only trigger if audiobook is completed or marked as favorite
    if instance.is_completed or instance.is_favorite:
        # Queue recommendation generation (debounced - only if no recent generation)
        from .models import RecommendationBatch
        from django.utils import timezone
        from datetime import timedelta
        
        # Check if recommendations were generated recently (within last hour)
        recent_batch = RecommendationBatch.objects.filter(
            user=instance.user,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).exists()
        
        if not recent_batch:
            generate_recommendations.delay(str(instance.user.id))