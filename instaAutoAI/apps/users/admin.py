from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(AdminUserCreationForm):
    """
    Creation form for the custom User model.

    Uses AdminUserCreationForm (Django 5.1+) rather than UserCreationForm.
    UserCreationForm raises FieldError on the 'usable_password' field in
    Django 5.0+ and must not be used.
    """

    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = AdminUserCreationForm.Meta.fields


class CustomUserChangeForm(UserChangeForm):
    """
    Change form for the custom User model.
    """

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for the custom User model.

    Extends UserAdmin.fieldsets rather than replacing it entirely —
    replacing it would silently break the permissions and groups display.
    """

    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ["username", "email", "is_staff", "is_active", "date_joined"]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    search_fields = ["username", "email"]
    ordering = ["username"]

    # Extend parent fieldsets — do NOT replace them.
    # UserAdmin.fieldsets already covers personal info, permissions, dates.
    fieldsets = UserAdmin.fieldsets
    add_fieldsets = UserAdmin.add_fieldsets