
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
from rest_framework_simplejwt.tokens import AccessToken
from asgiref.sync import sync_to_async
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user_from_token_key(token_key):
    try:
        access_token = AccessToken(token_key)
        user_id = access_token['user_id']
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()
    
@database_sync_to_async
def get_chatroom(room_name):
    return ChatRoom.objects.get(id=room_name)

@database_sync_to_async
def create_chatroom(user1,user2):
    new_chatroom = ChatRoom.objects.create_private_chat(user1,user2)
    return {
        'id': new_chatroom.id,
        'chat_name':user2.username,
        'timeSorter':new_chatroom.createdAt
    }
    
@database_sync_to_async
def get_messages(chatroom):
    messages = chatroom.chatroom_messages.all().order_by('timestamp')
    return [
        {
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'content': message.content,
            'timestamp': str(message.timestamp)
        }
        for message in messages
    ]
    
@database_sync_to_async
def create_message(chatroom, user, content):
    message = Message.objects.create(sender=user, content=content,chatroom=chatroom)
    return {
        'sender': user.username,
        'sender_id': user.id,
        'content': content,
        'timestamp': str(message.timestamp),
        'chat_id':chatroom.id
    }
    
    

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if not token:
            await self.close()
            return
        self.user = await get_user_from_token_key(token)
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        self.chatroom = await get_chatroom(self.room_name)
        chat_name = "chat_name"
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        
        await self.accept()
        
        messages = await get_messages(self.chatroom)
        
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'chat_name': chat_name,
            'messages': messages
        }))
        
    
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name,self.channel_name)
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        
        other_user = await sync_to_async(lambda: self.chatroom.members.exclude(id=self.user.id).get())()
        receiverUser = other_user.id
        new_message_data = await create_message(self.chatroom, self.user, message)
        await self.channel_layer.group_send(self.room_group_name,{
            "type": "chat_message",
            "message": new_message_data
        })
        trigger_payload = {
           'type':'trigger_message',
           'text':'You have a new message',
           'chat_id':new_message_data['chat_id'],
           'timeSorter':new_message_data['timestamp']
        }
        await self.channel_layer.group_send(f"user_{receiverUser}",trigger_payload)
        await self.channel_layer.group_send(f"user_{self.user.id}",trigger_payload)
        
    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({
            'type':'new_message',
            'message':message
        }))
        
        
class ChatroomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if not token:
            await self.close()
            return
        self.user = await get_user_from_token_key(token)
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.user_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)
        
    async def receive(self, text_data):
        pass
        
    
    async def new_chatroom(self, event):
        await self.send(text_data=json.dumps({
            "type":"new_chatroom",
            "chatroom": event["chatroom"]
        }))
        
    async def trigger_message(self,event):
        await self.send(text_data=json.dumps({
            'triggered_data':event['text'],
            'status':'Message received via trigger',
            'type':'trigger_message',
            'chat_id':event['chat_id'],
            'timeSorter':event['timeSorter']
        }))
        
    # Code to listen a new message from the chatroom consumer
    
        

# class UserChatroomConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user = self.scope['user']
#         if self.user.is_authenticated:
#             self.user_group_name = f'user_{self.user.id}'
#             await self.channel_layer.group_add(self.user_group_name, self.channel_name)
#             await self.accept()
#         else:
#             await self.close()
            
#     async def disconnect(self, close_code):
#         if self.user.is_authenticated:
#             await self.channel_layer.group_discard(
#                 self.user_group_name,
#                 self.channel_name
#             )
            
#     async def chatroom_added(self, event):
#         message = event['message']
#         await self.send(text_data=json.dumps({
#             'type':'chatroom_added',
#             'message':message
#         }))
        
# class ChatroomConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = f"chat_{self.room_name}"
#         self.user = self.scope['user']
        
#         if self.user.is_authenticated:
#             if not self.is_member(self.user, self.room_name):
#                 return self.close()
            
#             await self.channel_layer.group_add(
#                 self.room_group_name,
#                 self.channel_name
#             )
            
#             await self.accept()
#         else:
#             await self.close()
            
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_layer
#         )
        
#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data['message']
        
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type':'chat_message',
#                 'message': message,
#                 'sender': self.user.username
#             }
#         )
    
#     async def chat_message(self, event):
#         message = event['message']
#         sender = event['sender']
        
#         await self.send(text_data=json.dumps({
#             'type':'chat_message',
#             'message': message,
#             'sender':sender
#         }))
        
            
        