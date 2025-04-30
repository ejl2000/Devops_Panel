# config/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.http import HttpResponse


def healthz(request):
    return HttpResponse("OK", status=200)


def ready(request):
    return HttpResponse("Ready", status=200)


urlpatterns = [
                  path(settings.ADMIN_URL, admin.site.urls),

                  # User management
                  path("users/", include("devopspanel.users.urls", namespace="users")),
                  path("accounts/", include("allauth.urls")),

                  # Include Core URLs at the root
                  path("services/", include("devopspanel.core.urls", namespace="core")),
                  path("", include("devopspanel.dashboard.urls", namespace="dashboard")),
                  # Assign a distinct prefix to Dashboard URLs to avoid conflicts
                  # path("dashboard/", include("devopspanel.dashboard.urls", namespace="dashboard")),

                  # path("apps/", include("devopspanel.apps.urls", namespace="apps")),
                  path("pages/", include("devopspanel.pages.urls", namespace="pages")),
                  path("uikit/", include("devopspanel.uikit.urls", namespace="uikit")),
                  path("authentication/", include("authentication.urls", namespace="authentication")),
                  path("__reload__/", include("django_browser_reload.urls")),
                  path('select2/', include(('django_select2.urls', 'django_select2'), namespace='select2')),

                  path("healthz/", healthz, name="healthz"),
                  path("ready/", ready, name="ready"),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
