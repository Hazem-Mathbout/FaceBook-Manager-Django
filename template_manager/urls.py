from django.urls import path
from .views import template_list, live_preview, generate_preview_image , template_create, template_update, template_delete, font_upload_view, TemplateDetailView

urlpatterns = [
    path('', template_list, name='template_list'),
    path('create/', template_create, name='template_create'),
    path('update/<int:pk>/', template_update, name='template_update'),
    path('delete/<int:pk>/', template_delete, name='template_delete'),
    path('template/<int:pk>/', TemplateDetailView.as_view(), name='template_detail'),
    path('fonts/upload/', font_upload_view, name='font_upload'),
    # path('live_preview/<template>/', live_preview, name='live_preview'),

    path('live-preview/', live_preview, name='live_preview'),
    path('generate_preview_image/', generate_preview_image, name='generate_preview_image'),

]
