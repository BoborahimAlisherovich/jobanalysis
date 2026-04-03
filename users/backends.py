from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import models

CustomUser = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    Allows login with either username or email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(CustomUser.USERNAME_FIELD)
        
        # Try to fetch the user by searching the username OR email field
        user = CustomUser.objects.filter(
            models.Q(username__iexact=username) | models.Q(email__iexact=username)
        ).first()

        if user and user.check_password(password):
            return user
        return None
