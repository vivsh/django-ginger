from django.contrib.auth.models import User, check_password
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class CaseInsensitiveBackend(ModelBackend):
    """
    By default ModelBackend does case _sensitive_ username authentication, which isn't what is
    generally expected.  This backend supports case insensitive username authentication.
    """

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username))
            if user.check_password(password):
                return user
            else:
                return None
        except User.DoesNotExist:
            return None

