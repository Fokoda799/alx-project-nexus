from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  email = models.EmailField(unique=True)
  profile_avatar = models.URLField(blank=True, null=True)
  bio = models.TextField(blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    db_table = 'users'
    ordering = ['-created_at']
  
  def __str__(self):
    return self.username