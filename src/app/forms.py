from django import forms
from .models import School, Course

class ProfileForm(forms.Form):
    ROLE_CHOICES = [
        ('mentor', 'Mentor'),
        ('mentee', 'Mentee'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    
    # Fields for mentee
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        required=False,
        empty_label="Select a school"
    )
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        empty_label="Select a course"
    )
    
    # Fields for mentor
    expertise = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text="Describe your areas of expertise"
    )
    
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select courses you can mentor"
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
                raise forms.ValidationError("At least one course is required for mentors")
        
        return cleaned_data