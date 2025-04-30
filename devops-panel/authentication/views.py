from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import TemplateView

class AuthenticationView (LoginRequiredMixin, TemplateView):
    pass

# Create your views here.

login_view = AuthenticationView.as_view(template_name = "authentication/auth-login.html")
loginAlt_view = AuthenticationView.as_view(template_name = "authentication/auth-login-alt.html")
register_view = AuthenticationView.as_view(template_name = "authentication/auth-register.html")
registerAlt_view = AuthenticationView.as_view(template_name = "authentication/auth-register-alt.html")
recoverPW_view = AuthenticationView.as_view(template_name = "authentication/auth-recover-pw.html")
recoverPWAlt_view = AuthenticationView.as_view(template_name = "authentication/auth-recover-pw-alt.html")
lockscreen_view = AuthenticationView.as_view(template_name = "authentication/auth-lock-screen.html")
lockscreenAlt_view = AuthenticationView.as_view(template_name = "authentication/auth-lock-screen-alt.html")
auth404_view = AuthenticationView.as_view(template_name = "authentication/auth-404.html")
auth404Alt_view = AuthenticationView.as_view(template_name = "authentication/auth-404-alt.html")
auth500_view = AuthenticationView.as_view(template_name = "authentication/auth-500.html")
auth500Alt_view = AuthenticationView.as_view(template_name = "authentication/auth-500Alt.html")