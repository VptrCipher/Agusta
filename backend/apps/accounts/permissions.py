from django.contrib.auth.models import Group
from rest_framework.permissions import SAFE_METHODS, BasePermission


ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_VIEWER = "viewer"
ASSIGNABLE_ROLES = (ROLE_USER, ROLE_VIEWER)


def is_admin_user(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser


def is_business_writer(user):
    if not user or not user.is_authenticated:
        return False
    return user.role in {ROLE_ADMIN, ROLE_USER}


def ensure_role_groups():
    for role in ASSIGNABLE_ROLES:
        Group.objects.get_or_create(name=role)


def set_user_role(user, role):
    if role not in ASSIGNABLE_ROLES:
        raise ValueError("Only user and viewer roles can be assigned")
    ensure_role_groups()
    user.groups.remove(*Group.objects.filter(name__in=ASSIGNABLE_ROLES))
    user.groups.add(Group.objects.get(name=role))


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsUser(BasePermission):
    """Normal user — can create/update/delete records."""
    def has_permission(self, request, view):
        return is_business_writer(request.user)


class IsViewer(BasePermission):
    """Read-only — can only view records."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsBusinessWriterOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_business_writer(request.user)
