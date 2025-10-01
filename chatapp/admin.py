from django.contrib import admin
from .models import ChatRoom, Message, ChatRoomMember
# Register your models here.
admin.site.register(ChatRoom)
admin.site.register(Message)
admin.site.register(ChatRoomMember)