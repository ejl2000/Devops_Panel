# dashboard/urls.py

from django.urls import path
from .views import (
 index_view, DashboardView, FetchDashboardDataView
)

app_name = "dashboard"

urlpatterns = [
    path('', index_view, name='index'),
    path("fetch-dashboard-data/", FetchDashboardDataView.as_view(), name='fetch_dashboard_data'),
]