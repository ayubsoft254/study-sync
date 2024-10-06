from django.urls import path
from course import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('session/create/', views.create_study_session, name='create_session'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/join/', views.join_session, name='join_session'),
    path('courses/', views.course_list, name='course_list'),
    path('profile/', views.profile, name='profile'),
    path('feedback/<int:session_id>/', views.submit_feedback, name='submit_feedback'),
]