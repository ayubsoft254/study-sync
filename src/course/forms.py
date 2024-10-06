from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator
from .models import University, Department, User, Resource, ResourceComment
from django.forms.widgets import ClearableFileInput

class UniversitySignupForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'domain', 'description', 'logo']

class StudentSignupForm(UserCreationForm):
    university_email = forms.EmailField(
        validators=[EmailValidator()],
        help_text="Please use your university email address"
    )
    department = forms.ModelChoiceField(queryset=Department.objects.none())
    student_id = forms.CharField(max_length=50)
    year_of_study = forms.IntegerField(min_value=1, max_value=6)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'university_email', 
                 'password1', 'password2', 'department', 'student_id', 'year_of_study']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'university_email' in self.data:
            try:
                email_domain = self.data['university_email'].split('@')[1]
                university = University.objects.get(domain=email_domain)
                self.fields['department'].queryset = Department.objects.filter(
                    university=university
                )
            except (University.DoesNotExist, IndexError):
                self.fields['department'].queryset = Department.objects.none()

class ResourceUploadForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'resource_type', 'file', 'external_link']

    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        file = cleaned_data.get('file')
        external_link = cleaned_data.get('external_link')

        if resource_type == 'link' and not external_link:
            raise forms.ValidationError('External link is required for link resources.')
        elif resource_type != 'link' and not file:
            raise forms.ValidationError('File is required for this resource type.')

class ResourceCommentForm(forms.ModelForm):
    class Meta:
        model = ResourceComment
        fields = ['content']