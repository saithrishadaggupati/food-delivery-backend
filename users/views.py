from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, UserProfileSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    # Anyone can sign up — customer, restaurant owner, delivery agent
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Account created successfully!',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):

    from .models import User

    email = request.data.get('email')

    password = request.data.get('password')

    try:
        username = User.objects.get(email=email).username
    except User.DoesNotExist:
        return Response({'error': 'Wrong username or password'}, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': f'Welcome back {user.username}!',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        })
    return Response({'error': 'Wrong username or password'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    # Only logged in users can see their profile
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)