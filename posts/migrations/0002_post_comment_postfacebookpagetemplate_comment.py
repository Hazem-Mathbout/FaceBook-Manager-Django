# Generated by Django 5.0.6 on 2024-07-04 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='postfacebookpagetemplate',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
    ]
