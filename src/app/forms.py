from django import forms
from .models import Profile

class RoleSelectionForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role']
        widgets = {
            'role': forms.RadioSelect(choices=Profile.ROLE_CHOICES),
        }
