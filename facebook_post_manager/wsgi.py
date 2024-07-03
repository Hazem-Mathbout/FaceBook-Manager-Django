"""
WSGI config for facebook_post_manager project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application


# Load environment variables from .env file
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facebook_post_manager.settings.production')

application = get_wsgi_application()

print("hazem -> get_wsgi_application Done")
