from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ChatRoomMember
from django.contrib.auth.models import User

@receiver(post_save, sender=ChatRoomMember)
def notify_new_chatroom(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        user_id = instance.member.id
        members = instance.chatroom.members.all()
        chat_name = "Anonymous Chat"
        for member in members:
            if member.username != instance.member.username:
                chat_name = member.username
        chatroom_data = {
            'id': instance.chatroom.id,
            'chat_name': chat_name
        }
        
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type":"new_chatroom",
                "chatroom": chatroom_data
            }
        )