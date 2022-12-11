from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
class User(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class Profile(models.Model):
    class Meta:
        verbose_name = "user profile"
        verbose_name_plural = "user profiles"

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    last_location = models.PointField(
        verbose_name="last location",
        editable=False,
        blank=True,
        null=True,
        default=None,
        help_text="Geographic coordinates (lon/lat) as Point. Can be serialised from WKT (well-known text) "
                  "representation")

    def __str__(self):
        return f"{self.user}"


@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    try:
        my_profile = instance.profile
        my_profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
