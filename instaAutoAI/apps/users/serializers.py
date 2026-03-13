from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the User model.

    Exposes only the four non-sensitive fields needed by the /me/ endpoint.
    All fields are marked read_only to prevent accidental writes through
    this serializer.  Password hash is never included.
    """

    class Meta:
        model = User
        fields = ["id", "username", "email", "date_joined"]
        extra_kwargs = {
            "id":           {"read_only": True},
            "username":     {"read_only": True},
            "email":        {"read_only": True},
            "date_joined":  {"read_only": True},
        }