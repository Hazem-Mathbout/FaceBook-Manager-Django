from django.urls import path
from .views import template_list, template_create, template_update, template_delete, TemplateDetailView

urlpatterns = [
    path('', template_list, name='template_list'),
    path('create/', template_create, name='template_create'),
    path('update/<int:pk>/', template_update, name='template_update'),
    path('delete/<int:pk>/', template_delete, name='template_delete'),
    path('template/<int:pk>/', TemplateDetailView.as_view(), name='template_detail'),
]
