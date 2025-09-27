from django.core.exceptions import PermissionDenied

from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


def superuser_only(func):
    def wrap(request, *args, **kwargs):
        if request.user.is_superuser:
            return func(request, *args, **kwargs)

        elif not request.user.is_active:
            raise "Your account is inactive."

        else:
            raise PermissionDenied

    return wrap


def cl_only(func):
    def wrap(request, *args, **kwargs):
        if request.user.is_cl:
            return func(request, *args, **kwargs)

        elif not request.user.is_active:
            raise "Your account is inactive."

        else:
            raise PermissionDenied

    return wrap


def cl_pa_only(func):
    def wrap(request, *args, **kwargs):
        if request.user.is_cl or request.user.is_superuser:
            return func(request, *args, **kwargs)
        elif not request.user.is_active:
            raise "Your account is inactive."
        else:
            raise PermissionDenied

    return wrap


def is_actionable(func):
    def wrap(request, *args, **kwargs):
        if request.user.is_actionable:
            return func(request, *args, **kwargs)

        elif not request.user.is_active:
            raise "Your account is inactive."

        else:
            raise PermissionDenied

    return wrap


class IsPlatformAdminstrator(BasePermission):
    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.is_superuser):
            raise AuthenticationFailed("401 Unauthorized")
        if not request.user.is_active:
            raise "Your account is inactive."
        return True


class IsCategoryLeader(BasePermission):
    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.is_cl):
            raise AuthenticationFailed("401 Unauthorized")
        if not request.user.is_active:
            raise "Your account is inactive."
        return True


class IsClOrPA(BasePermission):
    def has_permission(self, request, view):
        if not (
            request.user.is_authenticated
            and request.user.is_cl
            or request.user.is_superuser
            and request.user.is_authenticated
        ):
            raise AuthenticationFailed("401 Unauthorized")

        if not request.user.is_active:
            raise "Your account is inactive."

        return True


class IsActionable(BasePermission):
    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.is_actionable):
            raise AuthenticationFailed("401 Unauthorized")

        if not request.user.is_active:
            raise "Your account is inactive."

        return True
