from django.contrib import admin
from .models import FacebookPage, Post, PostLog, PostFacebookPageTemplate, BackgroundTask
# Register your models here.

admin.site.register([FacebookPage, Post, PostLog, PostFacebookPageTemplate, BackgroundTask])