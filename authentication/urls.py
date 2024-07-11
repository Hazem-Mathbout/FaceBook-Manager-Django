from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_admin_login, name='custom_admin_login'),
]
