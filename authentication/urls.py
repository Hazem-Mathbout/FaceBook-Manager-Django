from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_admin_login, name='custom_admin_login'),
    path('custom_logout/', views.custom_logout, name='custom_logout'),
]
