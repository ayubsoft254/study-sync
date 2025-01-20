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
]
