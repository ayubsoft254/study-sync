from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator
from .models import University, Department, User, Resource, ResourceComment
from django.forms.widgets import ClearableFileInput

class UniversitySignupForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'domain', 'description', 'logo']

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