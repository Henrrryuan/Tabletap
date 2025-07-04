from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.http import HttpResponseForbidden

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please login first")
                return redirect('login')
            
            # 如果是顾客（非员工/管理员），不需要检查角色
            if not (request.user.is_staff or request.user.is_superuser):
                return view_func(request, *args, **kwargs)
            
            # 对于员工/管理员，检查他们的角色
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, "User profile does not exist")
                return redirect('login')
            
            if request.user.is_superuser or request.user.userprofile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You do not have permission to access this page")
            return HttpResponseForbidden("403 Forbidden")
        
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required(['admin'])(view_func)

def staff_required(view_func):
    return role_required(['admin', 'staff'])(view_func)