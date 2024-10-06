from django.urls import path
from course import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('session/create/', views.create_study_session, name='create_session'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/join/', views.join_session, name='join_session'),
    path('chat/<uuid:room_id>/', views.chat_room, name='chat_room'),
    path('chat/create/<int:student_id>/', views.create_private_chat, name='create_private_chat'),
]