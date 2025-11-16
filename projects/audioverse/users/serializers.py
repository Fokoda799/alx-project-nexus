from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'profile_avatar', 'bio']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_avatar', 'bio', 'created_at']
        read_only_fields = ['id', 'created_at']

class UserProfileSerializer(serializers.ModelSerializer):
    """Detailed user profile with statistics"""
    total_audiobooks_started = serializers.SerializerMethodField()
    total_audiobooks_completed = serializers.SerializerMethodField()
    total_favorites = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'profile_avatar', 'bio', 
            'created_at', 'total_audiobooks_started', 'total_audiobooks_completed',
            'total_favorites', 'total_reviews'
        ]
        read_only_fields = ['id', 'created_at']

    def get_total_audiobooks_started(self, obj):
        return obj.listeningprogress_set.count()

    def get_total_audiobooks_completed(self, obj):
        return obj.listeningprogress_set.filter(is_completed=True).count()

    def get_total_favorites(self, obj):
        return obj.listeningprogress_set.filter(is_favorite=True).count()

    def get_total_reviews(self, obj):
        return obj.review_set.count()