from django.urls import path
from course import views


urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('session/create/', views.create_study_session, name='create_session'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/join/', views.join_session, name='join_session'),
    # Chat URLs
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('chat/create/public/', views.create_public_chat, name='create_public_chat'),
    path('chat/create/private/<int:student_id>/', views.create_private_chat, name='create_private_chat'),
    path('chat/<uuid:room_id>/', views.chat_room, name='chat_room'),
    
    # Resource URLs
    path('course/<int:course_id>/resources/', views.resource_list, name='resource_list'),
    path('resource/<int:resource_id>/', views.resource_detail, name='resource_detail'),
    path('course/<int:course_id>/upload-resource/', views.upload_resource, name='upload_resource'),
]