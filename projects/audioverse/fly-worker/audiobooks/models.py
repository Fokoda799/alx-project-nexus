from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Author(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    bio = models.TextField(blank=True)
    photo = models.URLField(blank=True, null=True)
    social_links = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'authors'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Narrator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    bio = models.TextField(blank=True)
    photo = models.URLField(blank=True, null=True)
    social_links = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'narrators'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Genre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'genres'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Audiobook(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500, db_index=True)
    description = models.TextField()
    cover_image = models.URLField()
    audio_file = models.URLField()
    duration_seconds = models.PositiveIntegerField()
    release_date = models.DateField(blank=True, null=True)
    language = models.CharField(max_length=50)
    publisher = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    
    # Relationships
    authors = models.ManyToManyField(Author, related_name='audiobooks')
    narrators = models.ManyToManyField(Narrator, related_name='audiobooks')
    genres = models.ManyToManyField(Genre, related_name='audiobooks')
    
    # Cached aggregations
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)]
    )
    total_ratings = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    play_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'audiobooks'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def duration_formatted(self):
        """Return duration in HH:MM:SS format"""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"