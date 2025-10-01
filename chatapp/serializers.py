from rest_framework import serializers

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import authenticate


class UserRegistrationSerailizer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    
    class Meta:
        model = User
        fields = ['username','email','password1','password2']
        
    def validate(self,data):
        if data['password1']!= data['password2']:
            raise serializers.ValidationError({'password2':'Passwords do not match'})
        validate_password(data['password1'])
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email= validated_data['email'],
            password = validated_data['password1']
        )
        return user
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    
    def validate(self,data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                data['access'] = str(refresh.access_token)
                data['refresh'] = str(refresh)
            else:
                raise serializers.ValidationError('Incorrect username and/or password.')
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return data
    
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, data):
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            raise serializers.ValidationError("Refresh token is required.")
        return data

    def save(self, **kwargs):
        refresh_token_str = self.validated_data['refresh_token']
        try:
            refresh_token = RefreshToken(refresh_token_str)
            refresh_token.blacklist()  # Corrected method call
        except (TokenError, InvalidToken) as e:
            raise serializers.ValidationError(f"Invalid or expired token: {e}") # More specific error message
        return {} 