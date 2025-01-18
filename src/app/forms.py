from django import forms
from allauth.account.forms import SignupForm
from .models import User

class CustomSignupForm(SignupForm):
    USER_TYPE_CHOICES = [
        ('mentor', 'Mentor'),
        ('mentee', 'Mentee'),
    ]
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label="Sign Up As")

    def save(self, request):
        user = super().save(request)
        user_type = self.cleaned_data['user_type']

        if user_type == 'mentor':
            user.is_mentor = True
        else:
            user.is_mentor = False

        user.save()
        return user
