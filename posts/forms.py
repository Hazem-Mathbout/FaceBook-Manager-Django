from django import forms
from .models import Post, FacebookPage, PostFacebookPageTemplate, Template
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
import facebook
from django.conf import settings
from .utils import FacebookTokenManager
import pytz
from datetime import timedelta
from django.utils import timezone

class PostForm(forms.ModelForm):
    user_timezone = forms.CharField(widget=forms.HiddenInput(), required=False)  # Add this field to capture the user's timezone

    class Meta:
        model = Post
        fields = ['image', 'description', 'recipe_name', 'publication_time', 'facebook_pages', 'publish_now']
        widgets = {
            'publication_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'placeholder': 'Enter description here'}),
            'recipe_name': forms.TextInput(attrs={'placeholder': 'Enter recipe name'}),
            'facebook_pages': forms.SelectMultiple(attrs={'placeholder': 'Select Facebook pages'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        publish_now = cleaned_data.get("publish_now")
        publication_time = cleaned_data.get("publication_time")
        user_timezone = cleaned_data.get("user_timezone")

        if not publish_now and not publication_time:
            raise forms.ValidationError({"publication_time": "You must set a publication time if not publishing immediately."})

        if publication_time:
            # If the publication_time is not naive, make it naive first
            if publication_time.tzinfo is not None:
                publication_time = publication_time.replace(tzinfo=None)
            
            # Convert the publication_time to the user's local timezone
            if user_timezone:
                local_tz = pytz.timezone(user_timezone)
                publication_time = local_tz.localize(publication_time)
                # Convert to UTC time
                publication_time_utc = publication_time.astimezone(pytz.UTC)
            else:
                publication_time_utc = publication_time

            current_time_utc = timezone.now().astimezone(pytz.UTC)

            # Check if the publication time is in the past
            if publication_time_utc < current_time_utc:
                raise forms.ValidationError({"publication_time": "Scheduled time must be in the future."})

            # Minimum Scheduling Time: 10 minutes
            min_scheduled_time = current_time_utc + timedelta(minutes=10)
            if publication_time_utc < min_scheduled_time:
                raise forms.ValidationError({"publication_time": "Scheduled time must be at least 10 minutes in the future."})

            # Maximum Scheduling Time: 30 days
            max_scheduled_time = current_time_utc + timedelta(days=29)
            if publication_time_utc > max_scheduled_time:
                raise forms.ValidationError({"publication_time": "Scheduled time cannot be more than 30 days in the future."})

        return cleaned_data


class PostFacebookPageTemplateForm(forms.ModelForm):
    class Meta:
        model = PostFacebookPageTemplate
        fields = ['post', 'facebook_page', 'template', 'description', 'recipe_name', 'image']
        widgets = {
            'template': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        print("kwargs: ", kwargs)
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs:
            instance = kwargs['instance']
            if instance and instance.facebook_page:
                self.fields['template'].queryset = instance.facebook_page.templates.all()
            else:
                self.fields['template'].queryset = Template.objects.none()



PostFacebookPageTemplateFormSet = inlineformset_factory(
    Post, 
    PostFacebookPageTemplate, 
    form=PostFacebookPageTemplateForm,
    extra=1,
    can_delete=False
)


class FacebookPageForm(forms.ModelForm):
    class Meta:
        model = FacebookPage
        fields = ['name', 'page_id', 'access_token', 'templates', 'language']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'page_id': forms.TextInput(attrs={'class': 'form-control'}),
            'access_token': forms.TextInput(attrs={'class': 'form-control'}),
            'templates': forms.SelectMultiple(attrs={'class': 'form-control', 'placeholder': 'Select Templates'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # self.request = kwargs.pop('request', None)
        self.request =  kwargs.pop('request', None)
        # print("request: ", request)
        super(FacebookPageForm, self).__init__(*args, **kwargs)

    def clean_access_token(self):
        # access_token = self.request.session.get('access_token')
        # if not access_token:
            # raise forms.ValidationError("Access token is missing. Please authenticate with Facebook again.")
        print("request: ", self.request)
        
        access_token = self.cleaned_data['access_token']
        if not access_token:
            raise forms.ValidationError("Access token is missing. Please authenticate with Facebook again.")
        
        
        fb_manager = FacebookTokenManager(
            app_id=settings.FACEBOOK_APP_ID,
            app_secret=settings.FACEBOOK_APP_SECRET,
            redirect_uri=settings.FACEBOOK_REDIRECT_URI
        )
        
        try:
            long_access_token = access_token
            fb_manager.short_lived_token = access_token
            long_access_token = fb_manager.get_long_lived_token()
            fb_manager.set_access_token(long_access_token)
            fb_manager.get_user_pages()
        except facebook.GraphAPIError:
            new_access_token = fb_manager.refresh_access_token(long_access_token)
            if not new_access_token:
                raise forms.ValidationError("The provided access token is invalid or expired.")
            self.cleaned_data['access_token'] = new_access_token

        self.cleaned_data['access_token'] = long_access_token
        try:
            self.request.session['access_token'] = long_access_token
        except Exception as e:
            print("The request Object is None now.")
        print("long_access_token", long_access_token)
        return self.cleaned_data['access_token']




class LogPostFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    facebook_page = forms.ModelMultipleChoiceField(
        queryset=FacebookPage.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2-multiple'}),
    )
    user = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2-multiple'}),
    )