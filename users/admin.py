from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_airport_admin')
    list_filter = ('is_staff', 'is_superuser', 'is_airport_admin')
    fieldsets = UserAdmin.fieldsets + (
        ('Airport Admin', {'fields': ('is_airport_admin',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Airport Admin', {'fields': ('is_airport_admin',)}),
    )
