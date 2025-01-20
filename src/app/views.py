from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages
from django.db.models import Avg, Count
from django.core.exceptions import PermissionDenied
from .models import Mentor, User, MentorSession, SessionAttendance, MentorRating, Resource, Call, Mentee
import uuid
from typing import Dict, Any
from django.urls import reverse
from .forms import *

class DashboardMixin:
    """Mixin to handle common dashboard functionality"""
    def get_dashboard_context(self, user: User) -> Dict[str, Any]:
        """Get basic context for dashboard"""
        return {
            'user': user,
            'notifications': user.notifications.filter(read=False)[:5],  # Assuming you add notifications
        }
    
def home(request):
    return render(request, 'app/home.html')

@login_required
def dashboard(request, username):
    """
    Enhanced dashboard view with better error handling and optimized queries
    """
    profile_user = get_object_or_404(User.objects.select_related('mentee', 'mentor'), 
                                    username=username)
    
    # Security check with custom error message
    if request.user != profile_user:
        messages.warning(request, "You can only access your own dashboard.")
        return redirect('app:dashboard', username=request.user.username)
    
    context = DashboardMixin().get_dashboard_context(profile_user)
    
    try:
        if hasattr(profile_user, 'mentee'):
            mentee = profile_user.mentee  # Get the Mentee instance
            
            # Optimize queries with select_related and prefetch_related
            upcoming_sessions = (MentorSession.objects
                .filter(participants=mentee,  # Use the mentee instance here
                        scheduled_time__gt=timezone.now())
                .select_related('mentor', 'call')
                .prefetch_related('participants'))
            
            # Use the mentee instance directly
            attended_sessions = (SessionAttendance.objects
                .filter(mentee=mentee)  # Ensure this uses the Mentee instance
                .select_related('session', 'session__mentor')
                .order_by('-session__scheduled_time'))
            
            resources = (Resource.objects
                .filter(course=mentee.course)
                .select_related('course', 'uploaded_by'))
            
            context.update({
                'role': 'mentee',
                'resources': resources,
                'upcoming_sessions': upcoming_sessions,
                'attended_sessions': attended_sessions,
                'course_progress': mentee.get_course_progress(),
            })
            
        elif hasattr(profile_user, 'mentor'):
            mentor = profile_user.mentor
            
            mentor_stats = (MentorSession.objects
                .filter(mentor=mentor)
                .aggregate(
                    avg_rating=Avg('ratings__rating'),
                    total_sessions=Count('id'),
                    unique_participants=Count('participants', distinct=True)
                ))
            
            created_sessions = (MentorSession.objects
                .filter(mentor=mentor)
                .prefetch_related('participants')
                .order_by('-scheduled_time'))
            
            recent_ratings = (MentorRating.objects
                .filter(mentor=mentor)
                .select_related('mentee', 'session')
                .order_by('-created_at')[:5])
            
            context.update({
                'role': 'mentor',
                'created_sessions': created_sessions,
                'recent_ratings': recent_ratings,
                'stats': mentor_stats,
            })
            
        else:
            messages.info(request, "Please complete your profile setup to access the dashboard.")
            return redirect('app:account_profile')
            
    except Exception as e:
        messages.error(request, f"An error occurred while loading the dashboard: {str(e)}")
        # Log the error here
    
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
        return hasattr(self.request.user, 'mentor')
    
    def form_valid(self, form):
        try:
            form.instance.mentor = self.request.user.mentor
            form.instance.call = Call.objects.create(
                call_type='conference',
                room_id=f"session_{uuid.uuid4().hex[:10]}"
            )
            response = super().form_valid(form)
            messages.success(self.request, "Session created successfully!")
            return response
        except Exception as e:
            messages.error(self.request, f"Failed to create session: {str(e)}")
            return self.form_invalid(form)
    
    def get_success_url(self):
        # Replace 'dashboard' with the name of the URL pattern for your dashboard
        return reverse('app:dashboard', kwargs={'username': self.request.user.username})           
        
        

@login_required
def start_one_to_one_call(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        other_user = get_object_or_404(User, id=user_id)
        
        # Check if there's already an active call
        existing_call = Call.objects.filter(
            call_type='one_to_one',
            participants__in=[request.user, other_user],
            ended_at__isnull=True
        ).first()
        
        if existing_call:
            return JsonResponse({'room_id': existing_call.room_id})
        
        # Create new call
        call = Call.objects.create(
            call_type='one_to_one',
            room_id=f"call_{uuid.uuid4().hex[:10]}"
        )
        call.participants.add(request.user, other_user)
        
        return JsonResponse({
            'room_id': call.room_id,
            'message': 'Call created successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def rate_mentor(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        session = get_object_or_404(MentorSession, id=session_id)
        
        # Verify the user attended the session
        if not SessionAttendance.objects.filter(
            session=session,
            mentee=request.user.mentee
        ).exists():
            return JsonResponse({'error': 'You must attend the session to rate it'}, status=403)
        
        # Check if user already rated this session
        if MentorRating.objects.filter(
            session=session,
            mentee=request.user.mentee
        ).exists():
            return JsonResponse({'error': 'You have already rated this session'}, status=400)
        
        rating = int(request.POST.get('rating'))
        if not 1 <= rating <= 5:
            return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
        
        MentorRating.objects.create(
            mentor=session.mentor,
            mentee=request.user.mentee,
            session=session,
            rating=rating,
            comment=request.POST.get('comment', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Rating submitted successfully'
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid rating value'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

class ResourceCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Resource
    fields = ['title', 'description', 'file', 'course']
    template_name = 'app/resource_form.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'mentor')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if hasattr(self.request.user, 'mentor'):
            # Limit course choices to mentor's courses
            form.fields['course'].queryset = self.request.user.mentor.courses.all()
        return form
    
    def form_valid(self, form):
        try:
            form.instance.uploaded_by = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, "Resource created successfully!")
            return response
        except Exception as e:
            messages.error(self.request, f"Failed to create resource: {str(e)}")
            return self.form_invalid(form)
        
@login_required
def profile_setup(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            user = request.user
            
            try:
                if role == 'mentor':
                    mentor = Mentor.objects.create(
                        user=user,
                        expertise=form.cleaned_data['expertise'],
                        available=True
                    )
                    # Add selected courses to the mentor
                    mentor.courses.set(form.cleaned_data['courses'])
                    
                else:  # mentee
                    Mentee.objects.create(
                        user=user,
                        school=form.cleaned_data['school'],
                        course=form.cleaned_data['course'],
                        enrollment_date=timezone.now()
                    )
                
                messages.success(request, "Profile setup completed successfully!")
                return redirect('app:dashboard', username=user.username)
                
            except Exception as e:
                messages.error(request, f"An error occurred while setting up your profile: {str(e)}")
    else:
        form = ProfileForm()
    
    return render(request, 'app/profile_setup.html', {'form': form})