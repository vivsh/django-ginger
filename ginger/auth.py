from django.contrib.auth.backends import ModelBackend
from django.db.models.query_utils import Q
from django.utils import six
from django.contrib.auth.models import User, AbstractUser


__all__ = ["GingerUser", "CaseInsensitiveBackend"]


class MetaUser(type):
    def __new__(self, name, bases, attrs):
        if bases == (AbstractUser,) and name == 'GingerUser':
            return type.__new__(self, name, (), {})
        cls = User
        meta = cls._meta
        field_dict = {f.name: f for f in meta.fields}
        for k, v in attrs.items():
            if k in field_dict:
                field = field_dict[k]
                attrs = v.__dict__.keys()
                for a in attrs:
                    value = getattr(v, a, None)
                    if value is not None:
                        setattr(field, a, value)
            elif k not in cls.__dict__ and not hasattr(cls, k):
                cls.add_to_class(k,v)
            else:
                cls.add_to_class(k, v)
        return cls


@six.add_metaclass(MetaUser)
class GingerUser(AbstractUser):
    class Meta(AbstractUser.Meta):
        abstract = True


class CaseInsensitiveBackend(ModelBackend):
    """
    By default ModelBackend does case _sensitive_ username authentication, which isn't what is
    generally expected.  This backend supports case insensitive username authentication.
    """
    #
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).get()
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None


