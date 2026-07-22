from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("user-register/", RegistrationView.as_view(), name='register'),
    path("user-change/username/", change_username, name='change_username'),
    path("user-change/password/", change_password, name='change_password'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('new/chatroom/', create_private_view, name="new_chat"),
    path('chatrooms/', get_chatrooms, name="chat_list"),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/recover/email',recover_credentials, name="recover_credentials"),
    path('api/test/',test_deployment, name="test_deployment"),
    path('api/delete/message/', delete_message, name="delete_message"),
]
