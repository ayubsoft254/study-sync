from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/<str:username>/', views.dashboard, name='dashboard'),
    path('accounts/redirect/', views.login_redirect, name='login_redirect'),   
    path('session/create/', views.MentorSessionCreate.as_view(), name='create_session'),
    path('call/start/<int:user_id>/', views.start_one_to_one_call, name='start_call'),    
    path('resource/create/', views.ResourceCreate.as_view(), name='create_resource'),
    path('rate/mentor/<int:session_id>/', views.rate_mentor, name='rate_mentor'),
    path('profile/setup/', views.profile_setup, name='account_profile'),
    path('sessions/', views.sessions_view, name='sessions'),
    path('agora/token/<str:channel_name>/', views.generate_agora_token, name='agora_token'),
    path('session/<int:session_id>/join/', views.join_session, name='join_session'),
    path('messages/send/', views.send_message, name='send_message'),
    path('api/messages/<int:user_id>/', views.get_messages, name='get_messages'),
    path('chats/', views.chat_list, name='chat_list'),  # Add this line
    path('chat/<int:user_id>/', views.chat_view, name='chat'),
]
