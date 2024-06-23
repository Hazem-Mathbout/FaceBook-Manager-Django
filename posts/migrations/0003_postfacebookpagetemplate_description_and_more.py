# Generated by Django 5.0.6 on 2024-06-18 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_remove_post_recurring_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='postfacebookpagetemplate',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='postfacebookpagetemplate',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='post_page_templates/'),
        ),
        migrations.AddField(
            model_name='postfacebookpagetemplate',
            name='recipe_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
