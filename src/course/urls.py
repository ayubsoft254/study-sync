from django.urls import path
from course.views import home_view

urlpatterns = [
    path('', home_view, name=home_view ),
]