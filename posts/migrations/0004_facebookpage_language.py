# Generated by Django 5.0.6 on 2024-06-19 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_postfacebookpagetemplate_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='facebookpage',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French')], default='en', max_length=10),
        ),
    ]
