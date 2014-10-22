
from django.utils import six
from django.contrib.auth.models import User


class MetaUser(type):
    def __new__(self,name,bases,attrs):
        if not bases or bases[0] == object:
            return type.__new__(self,name,bases,attrs)
        cls  = User
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
class UserBase(object):
    pass