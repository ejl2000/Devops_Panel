from django.urls import path

from .views import *
 
app_name = "authentication" 
urlpatterns = [
  path("login", view=login_view, name="login"),
  path("loginAlt", view=loginAlt_view, name="loginAlt"),
  path("register", view=register_view, name="register"),
  path("registerAlt", view=registerAlt_view, name="registerAlt"),
  path("recoverPW", view=recoverPW_view, name="recoverPW"),
  path("recoverPWAlt", view=recoverPWAlt_view, name="recoverPWAlt"),
  path("lockscreen", view=lockscreen_view, name="lockscreen"),
  path("lockscreenAlt", view=lockscreenAlt_view, name="lockscreenAlt"),
  path("auth404", view=auth404_view, name="auth404"),
  path("auth404Alt", view=auth404Alt_view, name="auth404Alt"),
  path("auth500", view=auth500_view, name="auth500"),
  path("auth500Alt", view=auth500Alt_view, name="auth500Alt"),
]