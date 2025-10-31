from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        try:
            social = SocialAccount.objects.get(user=instance, provider='steam')
            profile.steam_id = social.uid
            profile.avatar_url = social.extra_data.get('avatarfull')
            profile.save()
        except SocialAccount.DoesNotExist:
            pass
