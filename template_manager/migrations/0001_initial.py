# Generated by Django 5.0.6 on 2024-06-16 04:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('font_type', models.CharField(choices=[('AA-GALAXY', 'AA-GALAXY'), ('AGA Arabesque', 'AGA Arabesque'), ('AGA Arabesque Desktop', 'AGA Arabesque Desktop'), ('Akhbar MT', 'Akhbar MT'), ('Al-Jazeera-Arabic', 'Al-Jazeera-Arabic'), ('Aldhabi', 'Aldhabi'), ('Andalus', 'Andalus'), ('Arabic Typesetting', 'Arabic Typesetting'), ('Arial', 'Arial'), ('Bahnschrift', 'Bahnschrift'), ('Bold Italic Art', 'Bold Italic Art'), ('Book Antiqua', 'Book Antiqua'), ('Bookman Old Style', 'Bookman Old Style'), ('Bookshelf Symbol 7', 'Bookshelf Symbol 7'), ('BoutrosNewsH1', 'BoutrosNewsH1'), ('Calibri', 'Calibri'), ('Cambria', 'Cambria'), ('Candara', 'Candara'), ('Century', 'Century'), ('Century Gothic', 'Century Gothic'), ('Comic Sans MS', 'Comic Sans MS'), ('Consolas', 'Consolas'), ('Constantia', 'Constantia'), ('Corbel', 'Corbel'), ('Courier New', 'Courier New'), ('DIN Next LT Arabic', 'DIN Next LT Arabic'), ('DecoType Naskh', 'DecoType Naskh'), ('DecoType Naskh Extensions', 'DecoType Naskh Extensions'), ('DecoType Naskh Special', 'DecoType Naskh Special'), ('DecoType Naskh Swashes', 'DecoType Naskh Swashes'), ('DecoType Naskh Variants', 'DecoType Naskh Variants'), ('DecoType Thuluth', 'DecoType Thuluth'), ('Diwani Bent', 'Diwani Bent'), ('Diwani Letter', 'Diwani Letter'), ('Diwani Outline Shaded', 'Diwani Outline Shaded'), ('Diwani Simple Outline', 'Diwani Simple Outline'), ('Diwani Simple Outline 2', 'Diwani Simple Outline 2'), ('Diwani Simple Striped', 'Diwani Simple Striped'), ('Dubai', 'Dubai'), ('Ebrima', 'Ebrima'), ('Farsi Simple Bold', 'Farsi Simple Bold'), ('Farsi Simple Outline', 'Farsi Simple Outline'), ('Franklin Gothic Medium', 'Franklin Gothic Medium'), ('Gabriola', 'Gabriola'), ('Gadugi', 'Gadugi'), ('Garamond', 'Garamond'), ('Georgia', 'Georgia'), ('Hacen Tunisia Lt', 'Hacen Tunisia Lt'), ('Haettenschweiler', 'Haettenschweiler'), ('HoloLens MDL2 Assets', 'HoloLens MDL2 Assets'), ('Impact', 'Impact'), ('Ink Free', 'Ink Free'), ('Italic Outline Art', 'Italic Outline Art'), ('Javanese Text', 'Javanese Text'), ('Kufi Extended Outline', 'Kufi Extended Outline'), ('Kufi Outline Shaded', 'Kufi Outline Shaded'), ('Lato', 'Lato'), ('Led Italic Font', 'Led Italic Font'), ('Leelawadee', 'Leelawadee'), ('Leelawadee UI', 'Leelawadee UI'), ('Lucida Console', 'Lucida Console'), ('Lucida Sans Unicode', 'Lucida Sans Unicode'), ('MS Gothic', 'MS Gothic'), ('MS Outlook', 'MS Outlook'), ('MS Reference Sans Serif', 'MS Reference Sans Serif'), ('MS Reference Specialty', 'MS Reference Specialty'), ('MT Extra', 'MT Extra'), ('MV Boli', 'MV Boli'), ('Malgun Gothic', 'Malgun Gothic'), ('Microsoft Himalaya', 'Microsoft Himalaya'), ('Microsoft JhengHei', 'Microsoft JhengHei'), ('Microsoft New Tai Lue', 'Microsoft New Tai Lue'), ('Microsoft PhagsPa', 'Microsoft PhagsPa'), ('Microsoft Sans Serif', 'Microsoft Sans Serif'), ('Microsoft Tai Le', 'Microsoft Tai Le'), ('Microsoft Uighur', 'Microsoft Uighur'), ('Microsoft YaHei', 'Microsoft YaHei'), ('Microsoft Yi Baiti', 'Microsoft Yi Baiti'), ('MingLiU-ExtB', 'MingLiU-ExtB'), ('Mongolian Baiti', 'Mongolian Baiti'), ('Monotype Corsiva', 'Monotype Corsiva'), ('Monotype Koufi', 'Monotype Koufi'), ('Montserrat', 'Montserrat'), ('Mudir MT', 'Mudir MT'), ('Myanmar Text', 'Myanmar Text'), ('Nirmala UI', 'Nirmala UI'), ('Old Antic Bold', 'Old Antic Bold'), ('Old Antic Decorative', 'Old Antic Decorative'), ('Old Antic Outline', 'Old Antic Outline'), ('Old Antic Outline Shaded', 'Old Antic Outline Shaded'), ('PT Bold Arch', 'PT Bold Arch'), ('PT Bold Broken', 'PT Bold Broken'), ('PT Bold Dusky', 'PT Bold Dusky'), ('PT Bold Heading', 'PT Bold Heading'), ('PT Bold Mirror', 'PT Bold Mirror'), ('PT Bold Stars', 'PT Bold Stars'), ('PT Separated Baloon', 'PT Separated Baloon'), ('PT Simple Bold Ruled', 'PT Simple Bold Ruled'), ('Palatino Linotype', 'Palatino Linotype'), ('Roboto', 'Roboto'), ('SC_SHARJAH', 'SC_SHARJAH'), ('Sakkal Majalla', 'Sakkal Majalla'), ('Segoe MDL2 Assets', 'Segoe MDL2 Assets'), ('Segoe Print', 'Segoe Print'), ('Segoe Script', 'Segoe Script'), ('Segoe UI', 'Segoe UI'), ('Segoe UI Emoji', 'Segoe UI Emoji'), ('Segoe UI Historic', 'Segoe UI Historic'), ('Segoe UI Symbol', 'Segoe UI Symbol'), ('SimSun', 'SimSun'), ('SimSun-ExtB', 'SimSun-ExtB'), ('Simple Bold Jut Out', 'Simple Bold Jut Out'), ('Simple Indust Outline', 'Simple Indust Outline'), ('Simple Indust Shaded', 'Simple Indust Shaded'), ('Simple Outline Pat', 'Simple Outline Pat'), ('Simplified Arabic', 'Simplified Arabic'), ('Simplified Arabic Fixed', 'Simplified Arabic Fixed'), ('Sitka Small', 'Sitka Small'), ('Sylfaen', 'Sylfaen'), ('Symbol', 'Symbol'), ('Tahoma', 'Tahoma'), ('Tajawal', 'Tajawal'), ('Tajawal Black', 'Tajawal Black'), ('Tajawal ExtraBold', 'Tajawal ExtraBold'), ('Tajawal ExtraLight', 'Tajawal ExtraLight'), ('Tajawal Light', 'Tajawal Light'), ('Tajawal Medium', 'Tajawal Medium'), ('Times New Roman', 'Times New Roman'), ('Traditional Arabic', 'Traditional Arabic'), ('Trebuchet MS', 'Trebuchet MS'), ('Urdu Typesetting', 'Urdu Typesetting'), ('Verdana', 'Verdana'), ('Webdings', 'Webdings'), ('Wingdings', 'Wingdings'), ('Wingdings 2', 'Wingdings 2'), ('Wingdings 3', 'Wingdings 3'), ('Yu Gothic', 'Yu Gothic')], max_length=100)),
                ('text_color', models.CharField(max_length=7)),
                ('text_size', models.IntegerField(validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(100)])),
                ('stroke', models.BooleanField(default=False)),
                ('stroke_thickness', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('stroke_color', models.CharField(blank=True, max_length=7, null=True)),
                ('background_image', models.ImageField(upload_to='templates_backgrounds/')),
                ('text_position', models.CharField(choices=[('top_left', 'Top Left'), ('top_center', 'Top Center'), ('top_right', 'Top Right'), ('middle_left', 'Middle Left'), ('middle_center', 'Middle Center'), ('middle_right', 'Middle Right'), ('bottom_left', 'Bottom Left'), ('bottom_center', 'Bottom Center'), ('bottom_right', 'Bottom Right')], max_length=30)),
            ],
        ),
    ]
