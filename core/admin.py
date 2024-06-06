from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
        add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username","first_name","last_name","email", "password1", "password2"),
            },
        ),
    )
