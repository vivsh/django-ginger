
from ginger.exceptions import LoginRequired, PermissionRequired
from django.core.exceptions import PermissionDenied


__all__ = ['PermissionRequiredMixin', 'PrivilegeRequiredMixin', 'LoginRequiredMixin',
           'StaffRequiredMixin', 'SuperUserRequiredMixin', 'OwnerRequiredMixin']


class PermissionRequiredMixin(object):

    def get_permission_url(cls, user):
        raise NotImplementedError

    def get_user(self):
        user = super(PermissionRequiredMixin, self).get_user()
        url = self.get_permission_url()
        if url is not None:
            raise PermissionRequired(self.request, url)
        return user


class LoginRequiredMixin(object):

    def get_user(self):
        user = super(LoginRequiredMixin, self).get_user()
        if not user.is_authenticated():
            raise LoginRequired(self.request)
        return user


class OwnerRequiredMixin(LoginRequiredMixin):

    def get_user(self):
        user = super(OwnerRequiredMixin, self).get_user()
        if self.object.owner != user:
            raise PermissionDenied
        return user


class PrivilegeRequiredMixin(LoginRequiredMixin):
    
    def get_user(self):
        user = super(PrivilegeRequiredMixin, self).get_user()
        if not self.has_privileges(user):
            raise PermissionDenied
        return user

    def has_privileges(self, user):
        raise NotImplementedError


class StaffRequiredMixin(PrivilegeRequiredMixin):

    def has_privileges(self, user):
        return user.is_staff


class SuperUserRequiredMixin(PrivilegeRequiredMixin):

    def has_privileges(self, user):
        return user.is_superuser


