from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Recommendation(models.Model):
    """Store personalized audiobook recommendations for users"""
    
    REASON_CHOICES = [
        ('genre', 'Based on your favorite genres'),
        ('author', 'Based on authors you like'),
        ('similar', 'Similar to books you enjoyed'),
        ('popular', 'Popular in your genres'),
        ('new', 'New releases you might like'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    audiobook = models.ForeignKey('audiobooks.Audiobook', on_delete=models.CASCADE)
    score = models.FloatField(default=0.0, help_text="Recommendation confidence score")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='genre')
    is_viewed = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendations'
        ordering = ['-score', '-created_at']
        unique_together = ['user', 'audiobook']  # Prevent duplicate recommendations
        indexes = [
            models.Index(fields=['user', '-score']),
            models.Index(fields=['user', 'is_dismissed']),
        ]
    
    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.audiobook.title}"


class RecommendationBatch(models.Model):
    """Track recommendation generation batches"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_batches')
    total_generated = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'recommendation_batches'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Batch for {self.user.username} - {self.status}"