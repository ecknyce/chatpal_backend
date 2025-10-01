from django.db import models, IntegrityError
from django.contrib.auth.models import User


# Create your models here.
class ChatRoomMember(models.Model):
    chatroom = models.ForeignKey('ChatRoom', on_delete=models.CASCADE)
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('chatroom','member')
    
    
    
class ChatRoom(models.Model):
    members = models.ManyToManyField(User, related_name="chat_rooms", through='ChatRoomMember')
    created_at = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def create_private_chat(cls, user1, user2):
        sorted_members  = sorted([user1.id, user2.id])
        if cls.objects.filter(members=sorted_members[0]).filter(members=sorted_members[1]).count() > 0:
            raise IntegrityError("A chatroom with this user already exists")
        new_chatroom = cls.objects.create()
        ChatRoomMember.objects.create(chatroom=new_chatroom, member=user1)
        ChatRoomMember.objects.create(chatroom=new_chatroom, member=user2)
        return new_chatroom
    
    
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_messages")
    content = models.TextField()
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="chatroom_messages")
    timestamp = models.DateTimeField(auto_now_add=True)
    


