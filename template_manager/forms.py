from django import forms
from .models import Template

class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = '__all__'
        # fields = [
        #     'font_type', 'text_color', 'stroke', 'stroke_thickness', 
        #     'stroke_color', 'background_image', 'text_position_x', 'text_position_y'
        # ]
        widgets = {
            'font_type': forms.Select(attrs={'class': 'form-control'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            # 'stroke': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'stroke_thickness': forms.NumberInput(attrs={'class': 'form-control'}),
            'stroke_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'text_position_x': forms.NumberInput(attrs={'class': 'form-control'}),
            'text_position_y': forms.NumberInput(attrs={'class': 'form-control'}),
        }
