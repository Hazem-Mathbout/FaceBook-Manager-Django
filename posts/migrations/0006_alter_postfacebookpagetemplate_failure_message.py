# Generated by Django 5.0.6 on 2024-06-20 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_postfacebookpagetemplate_failure_message_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='postfacebookpagetemplate',
            name='failure_message',
            field=models.TextField(blank=True, default='The post has not been published yet!', null=True),
        ),
    ]
