from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Author, Narrator, Genre, Audiobook
from decimal import Decimal

User = get_user_model()

class AudiobookModelTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="Test Author", bio="Test bio")
        self.narrator = Narrator.objects.create(name="Test Narrator")
        self.genre = Genre.objects.create(name="Fiction")
        
        self.audiobook = Audiobook.objects.create(
            title="Test Audiobook",
            description="Test description",
            cover_image="http://example.com/cover.jpg",
            audio_file="http://example.com/audio.mp3",
            duration_seconds=3600,
            language="English"
        )
        self.audiobook.authors.add(self.author)
        self.audiobook.narrators.add(self.narrator)
        self.audiobook.genres.add(self.genre)

    def test_audiobook_creation(self):
        """Test that audiobook is created correctly"""
        self.assertEqual(self.audiobook.title, "Test Audiobook")
        self.assertEqual(self.audiobook.duration_seconds, 3600)
        self.assertEqual(self.audiobook.authors.count(), 1)
        self.assertEqual(self.audiobook.genres.count(), 1)

    def test_duration_formatted_property(self):
        """Test duration formatting"""
        self.assertEqual(self.audiobook.duration_formatted, "01:00:00")

    def test_audiobook_str(self):
        """Test string representation"""
        self.assertEqual(str(self.audiobook), "Test Audiobook")

class AudiobookAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create test data
        self.author = Author.objects.create(name="Test Author")
        self.narrator = Narrator.objects.create(name="Test Narrator")
        self.genre = Genre.objects.create(name="Fiction")
        
        self.audiobook = Audiobook.objects.create(
            title="Test Audiobook",
            description="Test description",
            cover_image="http://example.com/cover.jpg",
            audio_file="http://example.com/audio.mp3",
            duration_seconds=3600,
            language="English"
        )
        self.audiobook.authors.add(self.author)
        self.audiobook.narrators.add(self.narrator)
        self.audiobook.genres.add(self.genre)

    def test_list_audiobooks_unauthenticated(self):
        """Test that unauthenticated users can list audiobooks"""
        response = self.client.get('/api/audiobooks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_audiobook_detail(self):
        """Test retrieving a single audiobook"""
        response = self.client.get(f'/api/audiobooks/{self.audiobook.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Audiobook')
        self.assertIn('authors', response.data)
        self.assertEqual(len(response.data['authors']), 1)

    def test_search_audiobooks(self):
        """Test searching audiobooks by title"""
        response = self.client.get('/api/audiobooks/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_audiobooks_by_genre(self):
        """Test filtering audiobooks by genre"""
        response = self.client.get(f'/api/audiobooks/?genres={self.genre.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_audiobook_requires_admin(self):
        """Test that only admins can create audiobooks"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Audiobook',
            'description': 'New description',
            'cover_image': 'http://example.com/new.jpg',
            'audio_file': 'http://example.com/new.mp3',
            'duration_seconds': 7200,
            'language': 'English',
            'author_ids': [str(self.author.id)],
            'narrator_ids': [str(self.narrator.id)],
            'genre_ids': [str(self.genre.id)]
        }
        response = self.client.post('/api/audiobooks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_audiobook(self):
        """Test that admins can create audiobooks"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'title': 'New Audiobook',
            'description': 'New description',
            'cover_image': 'http://example.com/new.jpg',
            'audio_file': 'http://example.com/new.mp3',
            'duration_seconds': 7200,
            'language': 'English',
            'author_ids': [str(self.author.id)],
            'narrator_ids': [str(self.narrator.id)],
            'genre_ids': [str(self.genre.id)]
        }
        response = self.client.post('/api/audiobooks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Audiobook.objects.count(), 2)

    def test_popular_audiobooks_endpoint(self):
        """Test popular audiobooks endpoint"""
        # Create audiobook with higher play count
        popular = Audiobook.objects.create(
            title="Popular Book",
            description="Popular",
            cover_image="http://example.com/popular.jpg",
            audio_file="http://example.com/popular.mp3",
            duration_seconds=3600,
            language="English",
            play_count=100
        )
        
        response = self.client.get('/api/audiobooks/popular/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['title'], 'Popular Book')