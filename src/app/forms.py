from django import forms
from django.contrib.auth.models import User
from .models import School, Course, Mentee, Mentor

class ProfileForm(forms.Form):
    ROLE_CHOICES = [
        ('mentee', 'Mentee'),
        ('mentor', 'Mentor'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="I want to join as a"
    )
    
    # Fields for Mentee
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        required=False,
        label="School",
        help_text="Select your school (required for mentees)"
    )
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        label="Course",
        help_text="Select your course (required for mentees)"
    )
    
    # Fields for Mentor
    expertise = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Areas of Expertise",
        help_text="Required for mentors: List your skills and areas of expertise"
    )
    
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Courses you can mentor",
        help_text="Select the courses you're qualified to mentor (required for mentors)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        if role == 'mentee':
            if not cleaned_data.get('school'):
                raise forms.ValidationError("School is required for mentees")
            if not cleaned_data.get('course'):
                raise forms.ValidationError("Course is required for mentees")
                
        elif role == 'mentor':
            if not cleaned_data.get('expertise'):
                raise forms.ValidationError("Expertise is required for mentors")
            if not cleaned_data.get('courses'):
                raise forms.ValidationError("Please select at least one course to mentor")
                
        return cleaned_data