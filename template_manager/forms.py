from django import forms
from .models import Template
from .utils import list_user_uploaded_fonts

class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = '__all__'
        widgets = {
            'font_type': forms.Select(attrs={'class': 'form-control'}),
            'text_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'stroke_thickness': forms.NumberInput(attrs={'class': 'form-control'}),
            'stroke_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'background_position': forms.Select(attrs={'class': 'form-control'}),
            'bounding_box': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),

        }
    
    def clean(self):
        cleaned_data = super().clean()
        background_position = cleaned_data.get('background_position')
        bounding_box = cleaned_data.get('bounding_box')
        background_image = cleaned_data.get('bounding_box')

        if not background_image:
            self.add_error('background_image', 'Background image cannot be empty.')

        if not background_position:
            self.add_error('background_position', 'Background position cannot be empty.')

        if not bounding_box:
            self.add_error('bounding_box', 'Bounding box cannot be empty.')

        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font_choices = [(font, font) for font in list_user_uploaded_fonts()]
        self.fields['font_type'].choices = font_choices


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class FontUploadForm(forms.Form):
    fonts = MultipleFileField(label='Select font files: ', required=True)

    def clean_fonts(self):
        files = self.files.getlist('fonts')
        for file in files:
            if not file.name.endswith('.ttf'):
                raise forms.ValidationError("Only .ttf files are allowed.")
        return files