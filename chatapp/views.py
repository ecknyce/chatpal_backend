from django.shortcuts import render
from django.db import IntegrityError
from django.http import JsonResponse
from .models import ChatRoom, Message
from django.contrib.auth.models import User
from .serializers import UserRegistrationSerailizer, LoginSerializer, LogoutSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
import json
import jwt
from django.conf import settings


# Create your views here.

#Create a new chatroom

def checkAuth(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', None)
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response({'error':'No valid authorization header'}, status=401)
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        user = User.objects.get(pk=user_id)
    except jwt.ExpiredSignatureError:
        user = None
    except jwt.InvalidTokenError:
        user = None
    
    return user

def getLastMessage(chatroom):
    latest_message = Message.objects.filter(chatroom=chatroom).order_by('-timestamp').first()
    return latest_message.timestamp


class RegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerailizer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"detail":"User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request':request})
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
@permission_classes([IsAuthenticated])   
class LogoutView(APIView):

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def create_private_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user1_id = data.get('user1_id')
        user2_username = data.get('user2_username')
        print(user1_id, user2_username)
        if not user1_id or not user2_username:
            return JsonResponse({'error': "Missing username"}, status=400)      
        try:
            user1 = User.objects.get(id=user1_id)
            user2 = User.objects.get(username=user2_username)
            if user1 == user2:
                return JsonResponse({'error': "Can't chat with your self"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error':f"'{user2_username}' does not exists!!!"}, status=404)
        
        try:
            new_chatroom = ChatRoom.create_private_chat(user1,user2)
            return JsonResponse({'message': 'Chatroom created successfully', 'chatroom_id': new_chatroom.id}, status=201)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=409)
    
    return JsonResponse({'error': 'Only Post requests are allowed'}, status=405)


@permission_classes([IsAuthenticated])
@api_view(["GET"])
def get_chatrooms(request):
    my_user = checkAuth(request)
    if my_user:
        chatroom_list = []
        chatrooms = my_user.chat_rooms.all()
        for chatroom in chatrooms:
            members = chatroom.members.all()
            chat_name = ""
            for member in members:
                if member.username != my_user.username:
                    chat_name = member.username
            chatroom_list.append({
                "id": chatroom.id,
                "chat_name": chat_name,
                "timeSorter":getLastMessage(chatroom)
            })
        return JsonResponse({"chats": chatroom_list}, status=200)
    else:
        return JsonResponse({"error":"You are not authorised"}, status=403)
    
    
@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(["POST"])
def change_username(request):
    my_user = checkAuth(request)
    if my_user:
        data = json.loads(request.body)
        newUsername = data.get("newUsername")
        my_user.username = newUsername
        my_user.save()
        return JsonResponse({'message':"Operation successfull"}, status=200)
    return JsonResponse({'error':'Operation failed'})


@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(["POST"])
def change_password(request):
    my_user = checkAuth(request)
    if my_user:
        data = json.loads(request.body)
        newPassword = data.get("newPassword")
        oldPassword = data.get("oldPassword")
        if my_user.check_password(oldPassword):
            my_user.set_password(newPassword)
            return JsonResponse({'message':'Password change operation completed'}, status=200)
        else:
            return JsonResponse({'error':'Wrong password'}, status=400)  
    return JsonResponse({'error':'An error occured make sure you are logged in'}, status=400)
        
        
