from django.urls import path
from . import views

app_name = "monitoring"

urlpatterns = [
    path('', views.index, name='index'),
    path('receiver/<int:receiver_id>/', views.receiver_view, name='receiver_view'),
    path('receiver/<int:receiver_id>/report/', views.download_report, name='download_report'),
    path('gsm_provider/<int:provider_id>/', views.gsm_provider_view, name='gsm_provider_view'),
    path('gsm_provider/<int:provider_id>/report/', views.download_gsm_provider_report, name='download_gsm_provider_report'),
    path('devices/', views.all_devices, name='all_devices'),
    path('devices/report/', views.download_all_devices_report, name='download_all_devices_report'),
]