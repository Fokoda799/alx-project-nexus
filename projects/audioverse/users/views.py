from rest_framework import viewsets, status, permissions, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    UserProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordUpdateSerializer
)
from .tasks import send_verification_email, send_welcome_email, send_password_reset_email

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'profile':
            return UserProfileSerializer
        elif self.action == 'update_password':
            return PasswordUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Register a new user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email (background task) - convert UUID to string
        send_verification_email.delay(str(user.id))
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        """Get or update current user's profile"""
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)
        else:
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_password(self, request):
        """Update current user's password"""
        serializer = PasswordUpdateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password updated successfully.'
        }, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Logout user by blacklisting the refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Invalid token or token already blacklisted.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyEmailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        """Verify user's email using token"""
        try:
            # Decode the token (format: base64_uid-token)
            uid = force_str(urlsafe_base64_decode(token.split(':')[0]))
            user = User.objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token.split(':')[1]):
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    
                    # Send welcome email (background task)
                    send_welcome_email.delay(str(user.id))
                    
                    return Response({
                        'message': 'Email verified successfully. Welcome!'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'message': 'Email already verified.'
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid or expired verification link.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid verification link.'
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Request password reset email"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            # Send password reset email (background task) - convert UUID to string
            send_password_reset_email.delay(str(user.id))
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return Response({
            'message': 'If the email exists, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        """Confirm password reset with token"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Decode the token
            uid = force_str(urlsafe_base64_decode(token.split(':')[0]))
            user = User.objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token.split(':')[1]):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                return Response({
                    'message': 'Password reset successfully.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid or expired reset link.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid reset link.'
            }, status=status.HTTP_400_BAD_REQUEST)