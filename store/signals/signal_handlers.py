from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from store.models import Customer


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer(sender, **kwargs):
    if kwargs['created']:
        Customer.objects.create(user=kwargs['instance'])