from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AuditLog

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "institution", "company", "is_active")
    list_filter = ("role", "is_active")

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "entity", "object_id", "created_at")
    readonly_fields = ("created_at",)
