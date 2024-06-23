from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, FacebookPage, PostLog, PostFacebookPageTemplate
from .forms import LogPostFilterForm, PostForm, PostFacebookPageTemplateFormSet, FacebookPageForm
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from .utils import apply_templates_to_image, translate, publish_post
import os
import pytz
from django.core.files.storage import default_storage
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from .utils import FacebookTokenManager
import facebook


def post_creation_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        formset = PostFacebookPageTemplateFormSet(request.POST, instance=form.instance)

        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            user_timezone = form.cleaned_data['user_timezone']
            print("user_timezone: " , user_timezone)
            publication_time = form.cleaned_data['publication_time']
            if publication_time:
                # If the publication_time is not naive, make it naive first
                if publication_time.tzinfo is not None:
                    publication_time = publication_time.replace(tzinfo=None)

                # Convert the publication_time to the user's local timezone
                if user_timezone:
                    local_tz = pytz.timezone(user_timezone)
                    publication_time = local_tz.localize(publication_time)

                    # Convert to UTC time
                    publication_time = publication_time.astimezone(pytz.UTC)
                    post.publication_time = publication_time

            try:
                with transaction.atomic():
                    post.save()
                    form.save_m2m()  # Save many-to-many data
                    formset.instance = post
                    formset.save()

                    # Process the original image with the templates
                    original_image_path = post.image.path
                    facebook_pages = post.facebook_pages.all()

                    recipe_name_input = post.recipe_name

                    try:
                        edited_images = apply_templates_to_image(original_image_path, facebook_pages, recipe_name_input)
                        # Save the edited images to a desired location or attach them to the post
                        for i, edited_image_data in enumerate(edited_images):
                            facebook_page = edited_image_data['facebook_page']
                            edited_image = edited_image_data['edited_image'] # type : ContentFile
                            template_image = edited_image_data['template_image']
                            translated_recipe_name_input = edited_image_data['translated_recipe_name_input']

                            # Overide the post facebookpage template data model...

                            try:
                                post_instance = Post.objects.get(id=post.pk)
                                facebook_page_instance = FacebookPage.objects.get(id=facebook_page.pk)
                                specific_template = PostFacebookPageTemplate.objects.get(post=post_instance, facebook_page=facebook_page_instance)
                                
                                path_editedimage = default_storage.save(edited_image.name, edited_image)
                                
                                specific_template.description = translate(post.description, 'en' , facebook_page.language)
                                specific_template.recipe_name = translated_recipe_name_input
                                specific_template.template = template_image
                                specific_template.image = path_editedimage
                                
                                specific_template.save()

                                # override_image_with_content_file(specific_template.image.path, edited_image)

                            except Exception as e:
                                messages.error(request, 'There is an error in overide the original data with new data')
                                print("Error: ", str(e))
                                raise e

                            # # Save the edited image in the same directory as the original image
                            # file_name_without_extension = os.path.splitext(os.path.basename(original_image_path))[0]
                            # edited_image_name = os.path.join(
                            #     os.path.dirname(original_image_path),
                            #     f"{facebook_page}_{file_name_without_extension}_{i}_edited.png"
                            # )
                            # with open(edited_image_name, 'wb') as f:
                            #     f.write(edited_image.read())

                    except Exception as e:
                        messages.error(request, 'There is an error in applying a template to the image.')
                        print("Error: ", str(e))
                        raise e

                    # Delete the original image for the main post. (Not Needed any more.)
                    try:
                        if post.image:
                                post.image.delete(save=False)
                    except Exception as e:
                            print(f"[error]: Ther an error in deleteing image post")
                            raise e

                    # Handle Publishing To FaceBook and Create a PostLog entry
                    for post_page_template in post.postfacebookpagetemplate_set.all():
                        publish_post(post_page_template=post_page_template)
                        PostLog.objects.create(post_page_template=post_page_template, user=request.user)

                messages.success(request, 'Post created successfully!')
                return redirect('log')

            except Exception as e:
                # Rollback: Delete the post and its image
                try:
                    if post.pk:  # Check if the post has a primary key
                        if post.image:  # Check if there is an image
                            post.image.delete(save=False)  # Delete the image file
                        post.delete()  # Delete the post
                except Exception as error_delete:
                    print("[Error]: " ,str(error_delete))
                    pass
                messages.error(request, str(e))
                print("[Error]: " , str(e))
                return render(request, 'posts/post_creation.html', {'form': form, 'formset': formset})

        else:
            messages.error(request, 'Something is wrong!')
            return render(request, 'posts/post_creation.html', {'form': form, 'formset': formset})

    else:
        form = PostForm()
        formset = PostFacebookPageTemplateFormSet(instance=form.instance)

    return render(request, 'posts/post_creation.html', {'form': form, 'formset': formset})


def pages_list(request):
    pages = FacebookPage.objects.all()
    return render(request, 'pages_manager/pages_list.html', {'pages': pages})

# @login_required
def page_create(request):
    if request.method == 'POST':
        form = FacebookPageForm(request.POST,  request=request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Page added successfully!')
            return redirect('pages_list')
        else:
            messages.error(request, 'The form is not valid! Please check the access token and other details.')
    else:
        form = FacebookPageForm(request=request)


    access_token_valid = True
    access_token = request.session.get('access_token')
    if not access_token:
        access_token_valid = False
    else:
        fb_manager = FacebookTokenManager(
            app_id=settings.FACEBOOK_APP_ID,
            app_secret=settings.FACEBOOK_APP_SECRET,
            redirect_uri=settings.FACEBOOK_REDIRECT_URI
        )
        try:
            fb_manager.set_access_token(access_token)
            fb_manager.get_user_pages()
        except facebook.GraphAPIError:
            access_token_valid = False

    # return render(request, 'pages_manager/page_form.html', {
    #     'form': form,
    #     'access_token_valid': access_token_valid
    # })
    return render(request, 'pages_manager/page_form.html', {'form': form})



# @login_required
def delete_page_view(request, pk):
    page = get_object_or_404(FacebookPage, pk=pk)
    if request.method == 'POST':
        page.delete()
        messages.success(request, 'Page deleted successfully!', 'success')
        return redirect('pages_list')
    return render(request, 'pages_manager/delete_page.html', {'page': page})

# @login_required
def modify_page_view(request, pk):
    page = get_object_or_404(FacebookPage, pk=pk)
    if request.method == 'POST':
        form = FacebookPageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, 'Page modified successfully!')
            return redirect('pages_list')
        else:
            messages.error(request, 'The Form Not Valid!')
    else:
        form = FacebookPageForm(instance=page)
    return render(request, 'pages_manager/modify_page.html', {'form': form, 'page': page})

# @login_required
def log_view(request):
    logs = PostLog.objects.all().order_by('-scheduled_time')
    form = LogPostFilterForm(request.GET or None)

    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            logs = logs.filter(post_page_template__post__publication_time__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            logs = logs.filter(post_page_template__post__publication_time__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('facebook_page'):
            logs = logs.filter(post_page_template__facebook_page__in=form.cleaned_data['facebook_page'])
        if form.cleaned_data.get('user'):
            logs = logs.filter(post_page_template__post__user__in=form.cleaned_data['user'])

    return render(request, 'posts/log.html', {'logs': logs, 'form': form})




def facebook_callback(request):
    code = request.GET.get('code')
    fb_manager = FacebookTokenManager(
        app_id=settings.FACEBOOK_APP_ID,
        app_secret=settings.FACEBOOK_APP_SECRET,
        redirect_uri=settings.FACEBOOK_REDIRECT_URI
    )
    try:
        short_lived_token = fb_manager.get_access_token_from_code(code)
        print("short_lived_token: ", short_lived_token)
        long_lived_token = fb_manager.get_long_lived_token()
        print("long_lived_token: ", long_lived_token)
        request.session['access_token'] = long_lived_token  # Store token in session or database as per your need
        return redirect('page_create')
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}')
    

def facebook_login(request):
    fb_manager = FacebookTokenManager(
        app_id=settings.FACEBOOK_APP_ID,
        app_secret=settings.FACEBOOK_APP_SECRET,
        redirect_uri=settings.FACEBOOK_REDIRECT_URI
    )
    authorization_url = fb_manager.get_authorization_url()
    return redirect(authorization_url)