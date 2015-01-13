from django.contrib.auth.backends import ModelBackend
from django.db.models.query_utils import Q
from django.utils import six
from django.contrib.auth.models import User


class MetaUser(type):
    def __new__(self,name,bases,attrs):
        if not bases or bases[0] == object:
            return type.__new__(self,name,bases,attrs)
        cls = User
        meta = cls._meta
        field_dict = {f.name: f for f in meta.fields }
        for k, v in attrs.items():
            if k in field_dict:
                field = field_dict[k]
                attrs = ('verbose_name','_unique','max_length', 'help_text')
                attrs = v.__dict__.keys()
                for a in attrs:
                    value = getattr(v, a, None)
                    if value is not None:
                        setattr(field, a, value)
            else:
                cls.add_to_class(k,v)
        return cls


@six.add_metaclass(MetaUser)
class UserBase(User):
    pass


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


