# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Mentee

@receiver(post_save, sender=User)
def create_mentee_or_mentor_profile(sender, instance, created, **kwargs):
    if created:
        if not instance.is_mentor:
            Mentee.objects.create(user=instance)
