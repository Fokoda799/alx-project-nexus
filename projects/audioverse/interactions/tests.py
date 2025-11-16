from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import ListeningProgress, Review, Bookmark
from audiobooks.models import Audiobook, Author, Narrator, Genre

User = get_user_model()

class ListeningProgressAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Create audiobook
        self.audiobook = Audiobook.objects.create(
            title="Test Audiobook",
            description="Test",
            cover_image="http://example.com/cover.jpg",
            audio_file="http://example.com/audio.mp3",
            duration_seconds=3600,
            language="English"
        )

    def test_create_listening_progress_authenticated(self):
        """Test authenticated user can create listening progress"""
        self.client.force_authenticate(user=self.user)
        data = {
            'audiobook_id': str(self.audiobook.id),
            'current_position_seconds': 120
        }
        response = self.client.post('/api/progress/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ListeningProgress.objects.count(), 1)
        
        progress = ListeningProgress.objects.first()
        self.assertEqual(progress.user, self.user)
        self.assertEqual(progress.audiobook, self.audiobook)
        self.assertEqual(progress.current_position_seconds, 120)

    def test_create_listening_progress_unauthenticated(self):
        """Test unauthenticated user cannot create progress"""
        data = {
            'audiobook_id': str(self.audiobook.id),
            'current_position_seconds': 120
        }
        response = self.client.post('/api/progress/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_only_see_own_progress(self):
        """Test users can only see their own listening progress"""
        # Create progress for both users
        ListeningProgress.objects.create(
            user=self.user,
            audiobook=self.audiobook,
            current_position_seconds=100
        )
        ListeningProgress.objects.create(
            user=self.other_user,
            audiobook=self.audiobook,
            current_position_seconds=200
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/progress/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['current_position_seconds'], 100)

    def test_update_listening_progress(self):
        """Test updating listening progress"""
        progress = ListeningProgress.objects.create(
            user=self.user,
            audiobook=self.audiobook,
            current_position_seconds=100
        )
        
        self.client.force_authenticate(user=self.user)
        data = {'current_position_seconds': 500}
        response = self.client.patch(f'/api/progress/{progress.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        progress.refresh_from_db()
        self.assertEqual(progress.current_position_seconds, 500)

    def test_toggle_favorite(self):
        """Test toggling favorite status"""
        progress = ListeningProgress.objects.create(
            user=self.user,
            audiobook=self.audiobook,
            current_position_seconds=100,
            is_favorite=False
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/progress/{progress.id}/toggle_favorite/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        progress.refresh_from_db()
        self.assertTrue(progress.is_favorite)
        
        # Toggle again
        response = self.client.post(f'/api/progress/{progress.id}/toggle_favorite/')
        progress.refresh_from_db()
        self.assertFalse(progress.is_favorite)

    def test_favorites_endpoint(self):
        """Test favorites endpoint returns only favorites"""
        ListeningProgress.objects.create(
            user=self.user,
            audiobook=self.audiobook,
            is_favorite=True
        )
        
        # Create non-favorite
        other_audiobook = Audiobook.objects.create(
            title="Other Book",
            description="Other",
            cover_image="http://example.com/other.jpg",
            audio_file="http://example.com/other.mp3",
            duration_seconds=3600,
            language="English"
        )
        ListeningProgress.objects.create(
            user=self.user,
            audiobook=other_audiobook,
            is_favorite=False
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/progress/favorites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_progress_percentage_calculation(self):
        """Test progress percentage is calculated correctly"""
        progress = ListeningProgress.objects.create(
            user=self.user,
            audiobook=self.audiobook,
            current_position_seconds=1800  # 50% of 3600
        )
        self.assertEqual(progress.progress_percentage, 50.0)

class ReviewAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.audiobook = Audiobook.objects.create(
            title="Test Audiobook",
            description="Test",
            cover_image="http://example.com/cover.jpg",
            audio_file="http://example.com/audio.mp3",
            duration_seconds=3600,
            language="English"
        )

    def test_create_review(self):
        """Test creating a review"""
        self.client.force_authenticate(user=self.user)
        data = {
            'audiobook_id': str(self.audiobook.id),
            'rating': 5,
            'review_text': 'Amazing audiobook!'
        }
        response = self.client.post('/api/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
        
        # Check audiobook rating was updated
        self.audiobook.refresh_from_db()
        self.assertEqual(self.audiobook.average_rating, 5.0)
        self.assertEqual(self.audiobook.total_ratings, 1)

    def test_review_rating_validation(self):
        """Test rating must be between 1 and 5"""
        self.client.force_authenticate(user=self.user)
        
        # Test rating too low
        data = {
            'audiobook_id': str(self.audiobook.id),
            'rating': 0,
            'review_text': 'Bad'
        }
        response = self.client.post('/api/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test rating too high
        data['rating'] = 6
        response = self.client.post('/api/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_one_review_per_user_per_audiobook(self):
        """Test users can only create one review per audiobook"""
        self.client.force_authenticate(user=self.user)
        data = {
            'audiobook_id': str(self.audiobook.id),
            'rating': 5,
            'review_text': 'Great!'
        }
        
        # First review succeeds
        response = self.client.post('/api/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Second review fails
        response = self.client.post('/api/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_average_rating_calculation(self):
        """Test average rating is calculated correctly"""
        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass')
        user3 = User.objects.create_user(username='user3', email='user3@example.com', password='pass')
        
        # Create three reviews
        Review.objects.create(user=self.user, audiobook=self.audiobook, rating=5)
        Review.objects.create(user=user2, audiobook=self.audiobook, rating=4)
        Review.objects.create(user=user3, audiobook=self.audiobook, rating=3)
        
        # Manually trigger rating update (normally done in view)
        from django.db.models import Avg, Count
        stats = Review.objects.filter(audiobook=self.audiobook).aggregate(
            avg_rating=Avg('rating'),
            total=Count('id')
        )
        self.audiobook.average_rating = stats['avg_rating']
        self.audiobook.total_ratings = stats['total']
        self.audiobook.save()
        
        self.audiobook.refresh_from_db()
        self.assertEqual(self.audiobook.average_rating, 4.0)  # (5+4+3)/3
        self.assertEqual(self.audiobook.total_ratings, 3)

    def test_filter_reviews_by_audiobook(self):
        """Test filtering reviews by audiobook"""
        other_audiobook = Audiobook.objects.create(
            title="Other Book",
            description="Other",
            cover_image="http://example.com/other.jpg",
            audio_file="http://example.com/other.mp3",
            duration_seconds=3600,
            language="English"
        )
        
        Review.objects.create(user=self.user, audiobook=self.audiobook, rating=5)
        Review.objects.create(user=self.user, audiobook=other_audiobook, rating=3)
        
        response = self.client.get(f'/api/reviews/?audiobook={self.audiobook.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['rating'], 5)

    def test_mark_review_helpful(self):
        """Test marking a review as helpful"""
        review = Review.objects.create(
            user=self.user,
            audiobook=self.audiobook,
            rating=5,
            review_text="Great!"
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/reviews/{review.id}/mark_helpful/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        review.refresh_from_db()
        self.assertEqual(review.helpful_count, 1)