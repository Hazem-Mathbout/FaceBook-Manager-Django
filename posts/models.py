from django.db import models
from template_manager.models import Template
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json


def load_language_choices(file_path='languages.json'):
    try:
        with open(file_path, 'r') as file:
            languages = json.load(file)
            return [(lang['code'], lang['name']) for lang in languages]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Fallback to a default set of languages if the file is not found or is invalid
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
    templates = models.ManyToManyField(Template)  # New field to link with Template

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
    # recurring_schedule = models.CharField(max_length=100, blank=True, null=True)
    facebook_pages = models.ManyToManyField(FacebookPage, through='PostFacebookPageTemplate')
    # facebook_pages = models.ManyToManyField(FacebookPage)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    publish_now = models.BooleanField(default=False)  # New field to indicate immediate publication

    def __str__(self):
        return self.recipe_name

    def save(self, *args, **kwargs):
        if self.publish_now:
            self.publication_time = None  # Clear publication_time if publishing immediately
        else:
            if not self.publication_time:
                raise ValidationError({"publication_time": "Publication time must be set if not publishing immediately."})

        super().save(*args, **kwargs)


class PostFacebookPageTemplate(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    facebook_page = models.ForeignKey(FacebookPage, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=False)
    description = models.TextField(null=True, blank=True)
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