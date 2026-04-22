from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def admin_required(view_func):
    """Permette l'accesso solo agli utenti con is_admin=True."""
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_admin or request.user.is_staff):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped


def login_required_custom(view_func):
    """Redirect a /login se l'utente non è autenticato."""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped
