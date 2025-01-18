from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [    
    path('', views.home, name='home'),
    path('/dashboard', views.dashboard, name='dashboard'),
    path('session/create/', views.MentorSessionCreate.as_view(), name='create_session'),
    path('call/start/<int:user_id>/', views.start_one_to_one_call, name='start_call'),
    path('chat/create/', views.create_chat, name='create_chat'),
    path('resource/create/', views.ResourceCreate.as_view(), name='create_resource'),
    path('rate/mentor/<int:session_id>/', views.rate_mentor, name='rate_mentor'),
]
