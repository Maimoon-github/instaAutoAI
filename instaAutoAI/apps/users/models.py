from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model — drop-in replacement for Django's built-in User.

    Extends AbstractUser with zero additional fields so that AUTH_USER_MODEL
    is satisfied from day one.  All future profile fields should be added
    here rather than creating a separate Profile model.

    Table name is pinned to 'users_user' to match the app label and avoid
    Django's default 'users_customuser' naming confusion in migrations.
    """

    class Meta:
        db_table = "users_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.username