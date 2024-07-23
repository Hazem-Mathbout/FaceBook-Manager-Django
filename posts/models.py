from django.db import models
from template_manager.models import Template
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json
from django.conf import settings
import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def load_language_choices(file_path=os.path.join(base_dir, 'languages.json')):
    try:
        with open(file_path, 'r') as file:
            languages = json.load(file)
            return [(lang['code'], lang['name']) for lang in languages]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Fallback to a default set of languages if the file is not found or is invalid
        print("languages.json path : ", os.path.join(base_dir, 'languages.json'))
        print("Error: " , str(e))
        return [
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            # Add more default languages as needed
        ]
    

class FacebookPage(models.Model):
    name = models.CharField(max_length=100)
    page_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=255)
    app_id = models.CharField(max_length=100 , null=False, blank=False)
    app_secret = models.CharField(max_length=100, null=False, blank=False)
    templates = models.ManyToManyField(Template, null=True, blank=True)  # New field to link with Template

    # Add Language Selection for Page tranlation here...
    language = models.CharField(
        max_length=10, 
        choices=load_language_choices(), 
        default='en'
    )
    
    def __str__(self):
        return self.name


class Post(models.Model):
    image = models.ImageField(upload_to='posts_photo/')
    description = models.TextField()
    recipe_name = models.CharField(max_length=100)
    publication_time = models.DateTimeField(blank=True, null=True)  # Allow null/blank for immediate posts
    facebook_pages = models.ManyToManyField(FacebookPage, through='PostFacebookPageTemplate')
    # facebook_pages = models.ManyToManyField(FacebookPage)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    publish_now = models.BooleanField(default=False)  # New field to indicate immediate publication
    comment = models.TextField(null=True, blank=True)
    translate_post = models.BooleanField(default=False)

    def __str__(self):
        return self.recipe_name

    def save(self, *args, **kwargs):
        if not self.publication_time and not self.publish_now:
            raise ValidationError({"publication_time": "Publication time must be set if not publishing immediately."})

        super().save(*args, **kwargs)


class PostFacebookPageTemplate(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    facebook_page = models.ForeignKey(FacebookPage, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=False)
    description = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    recipe_name = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='post_page_templates/', blank=True, null=True)
    # Add status filed.
    is_published = models.BooleanField(default=False)
    failure_message = models.TextField(default="The post has not been published yet!")  # Holds the failure message if any

    class Meta:
        unique_together = ('post', 'facebook_page')

    def __str__(self):
        return f"{self.post} - {self.facebook_page}"



class PostLog(models.Model):
    post_page_template = models.ForeignKey(PostFacebookPageTemplate, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.post_page_template.post.recipe_name} by {self.user.username}"

class BackgroundTask(models.Model):

    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('finished', 'Finished'),
        ('failed', 'Failed')
    ]

    publication_time = models.DateTimeField(null=True, blank=True)
    interval_hours = models.IntegerField()
    interval_minutes = models.IntegerField()
    idel_time = models.IntegerField(default=1)
    publish_now = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(default=0)  # Percentage of completion of succefual publishing posts
    number_succes_logs = models.IntegerField(default=0)
    bg_task_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')

    # Relationships to selected posts and Facebook pages
    selected_posts = models.ManyToManyField(Post, related_name='background_tasks') # This holding the posts ids from the UI.
    facebook_pages = models.ManyToManyField(FacebookPage, related_name='background_tasks')

    def calculate_status(self):
        total_logs = self.selected_posts.count()
        published_logs = self.number_succes_logs
        if total_logs > 0:
            self.status = (published_logs / total_logs) * 100
        self.save()

    def get_number_posts(self):
        return self.selected_posts.count()

    def __str__(self):
        return f"Task {self.id} - {self.status}% complete"