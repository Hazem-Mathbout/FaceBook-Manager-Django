# In your_app/signals.py

import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Template

@receiver(post_save, sender=Template)
def cleanup_temp_files(sender, instance, **kwargs):
    temp_folder = os.path.join(settings.BASE_DIR, 'media', 'temp')

    # Loop through all files in the temp directory and delete them
    for filename in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            # Handle exceptions as needed (e.g., logging)
            pass

    # Optionally, you can log or print a message here
    print(f"All files deleted from {temp_folder}")
