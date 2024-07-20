from django.urls import path
from . import views

urlpatterns = [
    path('', views.log_view, name='log'),
    path('post-create/', views.post_creation_view, name='post_creation'), 
    path('republish-posts/', views.republish_posts, name='republish_posts'),
    path('pages/', views.pages_list, name='pages_list'),
    path('pages/create/', views.page_create, name='page_create'),
    path('pages/update/<int:pk>/', views.modify_page_view, name='modify_page'),
    path('pages/delete/<int:pk>/', views.delete_page_view, name='delete_page'),

    path('background-tasks/', views.background_tasks, name='background_tasks'),
    path('delete-posts/', views.delete_posts, name='delete_posts'),
    path('edit/<int:post_id>/', views.edit_post_log, name='edit_post_log'),

    path('fetch_post_details/<int:post_id>/', views.fetch_post_details, name='fetch_post_details'),

    # --------------- Facebook Tokens -----------
    
    # path('facebook/login/', views.facebook_login, name='facebook_login'),
    # path('facebook/callback/', views.facebook_callback, name='facebook_callback')


    
    # Pages Urls...
    # path('pages/', views.page_management_view, name='page_management'),
    # path('pages/delete/<int:page_id>/', views.delete_page_view, name='delete_page'),
    # path('pages/modify/<int:page_id>/', views.modify_page_view, name='modify_page'),
]
