from django.db.models.signals import post_save
from django.shortcuts import redirect
from allauth.account.signals import email_confirmed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Mentor, Mentee

@receiver(email_confirmed)
def email_confirmed_redirect(request, email_address, **kwargs):
    """
    Redirect authenticated users to the role selection page after email confirmation.
    """
    user = email_address.user
    if user.is_authenticated:
        return redirect('/select-role/')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=Profile)
def create_role_specific_profile(sender, instance, **kwargs):
    """
    Automatically create Mentor or Mentee profiles based on the selected role.
    """
    if instance.role == 'mentor' and not hasattr(instance.user, 'mentor_profile'):
        Mentor.objects.create(user=instance.user)
    elif instance.role == 'mentee' and not hasattr(instance.user, 'mentee_profile'):
        Mentee.objects.create(user=instance.user)
