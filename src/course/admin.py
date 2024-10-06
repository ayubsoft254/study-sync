from django.contrib import admin
from .models import StudySession, ChatRoom, Resource, Course, StudentProfile, ChatRoom, University

# Register your models here.
admin.site.register(StudySession)
admin.site.register(ChatRoom)
admin.site.register(Resource)
admin.site.register(Course)
admin.site.register(StudentProfile)
admin.site.register(University)
