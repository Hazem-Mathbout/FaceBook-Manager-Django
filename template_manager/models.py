# models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from .utils import list_system_fonts

class Template(models.Model):
    font_choices = [(font, font) for font in list_system_fonts()]

    TEXT_POSITION_CHOICES = [
        ('top_left', 'Top Left'),
        ('top_center', 'Top Center'),
        ('top_right', 'Top Right'),
        ('middle_left', 'Middle Left'),
        ('middle_center', 'Middle Center'),
        ('middle_right', 'Middle Right'),
        ('bottom_left', 'Bottom Left'),
        ('bottom_center', 'Bottom Center'),
        ('bottom_right', 'Bottom Right'),
    ]

    name = models.CharField(max_length=100)
    font_type = models.CharField(max_length=100, choices=font_choices)
    text_color = models.CharField(max_length=7)  # Hex color code
    text_size = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(100)],
    )  # Restrict text size between 10 and 100
    # stroke = models.BooleanField(default=False)
    stroke_thickness = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Test",
    )  # Restrict stroke thickness between 1 and 10
    stroke_color = models.CharField(max_length=7, blank=True, null=True)  # Hex color code
    background_image = models.ImageField(upload_to='templates_backgrounds/', blank=True, null=True)
    text_position = models.CharField(max_length=30, choices=TEXT_POSITION_CHOICES)

    def __str__(self):
        return f"Template {self.id} - {self.name}"

    def delete(self, *args, **kwargs):
        from posts.models import FacebookPage  # Import models to avoid circular import

        linked_pages = FacebookPage.objects.filter(templates=self)
        if linked_pages.exists():
            page_names = '(' +  ', '.join(linked_pages.values_list('name', flat=True)) + ')'
            raise ValidationError(f"This template cannot be deleted because it is linked with the following pages: {page_names}. You can only modify the template or create a new one.")
        
        super().delete(*args, **kwargs)
