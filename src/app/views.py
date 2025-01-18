# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView
from django.http import JsonResponse
from .models import *
from django.utils import timezone
import uuid

def home(request):
    return render(request, 'app/home.html')

@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user
    }
    
    if hasattr(user, 'mentee'):
        # Mentee dashboard
        context.update({
            'resources': Resource.objects.filter(course=user.mentee.course),
            'upcoming_sessions': MentorSession.objects.filter(
                participants=user,
                scheduled_time__gt=timezone.now()
            ),
            'attended_sessions': SessionAttendance.objects.filter(mentee=user),
        })
    else:
        # Mentor dashboard
        context.update({
            'created_sessions': MentorSession.objects.filter(mentor=user),
            'ratings': MentorRating.objects.filter(mentor=user),
        })
    
    return render(request, 'app/dashboard.html', context)

class MentorSessionCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = MentorSession
    fields = ['title', 'description', 'scheduled_time', 'duration', 'max_participants']
    template_name = 'app/mentor_session_form.html'
    
    def test_func(self):
        return self.request.user.is_mentor
    
    def form_valid(self, form):
        form.instance.mentor = self.request.user
        form.instance.call = Call.objects.create(
            call_type='conference',
            room_id=f"session_{uuid.uuid4().hex[:10]}"
        )
        return super().form_valid(form)

@login_required
def start_one_to_one_call(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    call = Call.objects.create(
        call_type='one_to_one',
        room_id=f"call_{uuid.uuid4().hex[:10]}"
    )
    call.participants.add(request.user, other_user)
    return JsonResponse({'room_id': call.room_id})

@login_required
def create_chat(request):
    if request.method == 'POST':
        chat_type = request.POST.get('chat_type')
        participants = request.POST.getlist('participants')
        
        chat = Chat.objects.create(chat_type=chat_type)
        chat.participants.add(request.user, *participants)
        
        return JsonResponse({'chat_id': chat.id})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

class ResourceCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Resource
    fields = ['title', 'description', 'file', 'course']
    template_name = 'app/resource_form.html'
    
    def test_func(self):
        return self.request.user.is_mentor
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

@login_required
def rate_mentor(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(MentorSession, id=session_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        MentorRating.objects.create(
            mentor=session.mentor,
            mentee=request.user,
            session=session,
            rating=rating,
            comment=comment
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)