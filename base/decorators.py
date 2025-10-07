# ---------- base/decorators.py ----------
from django.shortcuts import redirect

def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if "user_id" not in request.session:
            return redirect("user_login")  # 👈 make sure this matches your login URL name
        return view_func(request, *args, **kwargs)
    return wrapper
