from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(School)
admin.site.register(Course)
admin.site.register(Mentee)
admin.site.register(Resource)
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(Call)
admin.site.register(MentorSession)
admin.site.register(SessionAttendance)


