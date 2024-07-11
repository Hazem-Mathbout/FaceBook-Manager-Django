from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

class AdminRequiredMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # print("AdminRequiredMiddleware is called")
        # print(f"Path: {request.path}, Authenticated: {request.user.is_authenticated}, Is Staff: {request.user.is_staff}")
        if not request.path.startswith('/admin/login/') and not request.path.startswith('/auth/') and not request.user.is_authenticated:
            return redirect('custom_admin_login')
        if not request.path.startswith('/admin/login/') and not request.path.startswith('/auth/') and not request.user.is_staff:
            raise PermissionDenied
        response = self.get_response(request)
        return response
