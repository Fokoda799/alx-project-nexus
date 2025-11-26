from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from audiobooks.models import Audiobook
import uuid

class ListeningProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    audiobook = models.ForeignKey(Audiobook, on_delete=models.CASCADE)
    current_position_seconds = models.PositiveIntegerField(default=0)
    is_favorite = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    last_listened_at = models.DateTimeField(auto_now=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'listening_progress'
        unique_together = ['user', 'audiobook']
        ordering = ['-last_listened_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.audiobook.title}"
    
    @property
    def progress_percentage(self):
        """Calculate listening progress as percentage"""
        if self.audiobook.duration_seconds == 0:
            return 0
        return (self.current_position_seconds / self.audiobook.duration_seconds) * 100

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    audiobook = models.ForeignKey(Audiobook, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review_text = models.TextField(blank=True)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        unique_together = ['user', 'audiobook']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.audiobook.title} ({self.rating}★)"

class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    audiobook = models.ForeignKey(Audiobook, on_delete=models.CASCADE)
    timestamp_seconds = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookmarks'
        ordering = ['audiobook', 'timestamp_seconds']
    
    def __str__(self):
        return f"{self.user.username} - {self.audiobook.title} @ {self.timestamp_seconds}s"


from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()
