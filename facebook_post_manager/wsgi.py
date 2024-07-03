"""
WSGI config for facebook_post_manager project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application


# Load environment variables from .env file


print("hazem -> get_wsgi_application")


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facebook_post_manager.settings')

application = get_wsgi_application()

print("hazem -> get_wsgi_application Done")
