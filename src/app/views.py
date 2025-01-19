# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView
from django.http import JsonResponse
from .forms import RoleSelectionForm
from .models import *
from django.utils import timezone
from django.contrib import messages
import uuid
from django.db.models import Avg



def home(request):
    return render(request, 'app/home.html')

def dashboard(request, username):
           
    # Fetch the profile user or return 404 if not found
    profile_user = get_object_or_404(User, username=username)
    
    # Redirect users trying to access another user's dashboard
    if request.user != profile_user:
        messages.warning(request, "Redirected to your dashboard.")
        return redirect('app:dashboard', username=request.user.username)
    
    # Common context for the dashboard
    context = {'user': profile_user}
    
    if hasattr(profile_user, 'mentee'):
        # Mentee-specific context
        mentee = profile_user.mentee 
        avg_rating = MentorRating.objects.filter(mentor=mentor).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        participant_count = MentorSession.objects.filter(mentor=mentor).values('participants').distinct().count()
        
        context.update({
            'resources': Resource.objects.filter(course=mentee.course).select_related('course'),
            'upcoming_sessions': MentorSession.objects.filter(
                participants=profile_user,
                scheduled_time__gt=timezone.now()
            ).select_related('mentor'),
            'attended_sessions': SessionAttendance.objects.filter(
                mentee=mentee
            ).select_related('session__mentor'),

            'avg_rating': avg_rating,  # Add the average rating to the context
            'participant_count': participant_count,  # Add the participant count to the context
        })
    elif hasattr(profile_user, 'mentor'):
        # Mentor-specific context
        mentor = profile_user.mentor  # Access the Mentor object
        context.update({
            'created_sessions': MentorSession.objects.filter(mentor=mentor).prefetch_related('participants'),
            'ratings': MentorRating.objects.filter(mentor=mentor).select_related('mentee', 'session'),
        })
    # else:
    #     # Default for users without mentee or mentor roles
    #     messages.info(request, "Your account is not yet configured for dashboard access.")
    #     return redirect('account_profile')  # Adjust the redirect URL as needed

    # Render the dashboard with the context
    return render(request, 'app/dashboard.html', context)

def login_redirect(request):
    if request.user.is_authenticated:
        # Use the namespaced URL name
        return redirect('app:dashboard', username=request.user.username)
    return redirect('account_login')

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


@login_required
def select_role(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = RoleSelectionForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('home')  # Redirect to your desired page
    else:
        form = RoleSelectionForm(instance=profile)
    return render(request, 'select_role.html', {'form': form})