import json
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from .tasks import schedule_task
from .models import BackgroundTask, Post, FacebookPage, PostLog, PostFacebookPageTemplate
from .forms import LogPostFilterForm, PostForm, PostFacebookPageTemplateFormSet, FacebookPageForm
from django.contrib import messages
from django.db import transaction
from .utils import apply_templates_to_image, translate, publish_post
import pytz
from django.core.files.storage import default_storage
from django.shortcuts import redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from urllib.parse import unquote
from dateutil.parser import parse
import pytz

# from django.conf import settings
# from .utils import FacebookTokenManager


def post_creation_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        formset = PostFacebookPageTemplateFormSet(request.POST, instance=form.instance)

        if form.is_valid():
            print("request.POST  :" , request.POST)
            # action = request.POST.get('action')
            # print("action: " , action)
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
                        edited_images = apply_templates_to_image(
                            original_image_path,
                            facebook_pages,
                            recipe_name_input,
                            should_translate=post.translate_post,
                            )
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
                                
                                if post.translate_post:
                                    specific_template.description = translate(post.description, 'en' , facebook_page.language)
                                else:
                                    specific_template.description = post.description
                                
                                if post.comment and post.translate_post:
                                    specific_template.comment = translate(post.comment, 'en' , facebook_page.language)
                                else:
                                    specific_template.comment = post.comment
                                
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

                    # Handle Publishing To FaceBook and Create a PostLog entry or just save it
                    for post_page_template in post.postfacebookpagetemplate_set.all():
                        if 'save_post' in request.POST:
                            if post.publish_now:
                                current_time = timezone.now()
                                post.publication_time = current_time
                                post.save()
                            post_page_template.is_published = True
                            post_page_template.failure_message = "The post has been saved and not published"
                            post_page_template.save()
                            PostLog.objects.create(post_page_template=post_page_template, user=request.user)
                        else:
                            publish_post(post_page_template=post_page_template)
                            PostLog.objects.create(post_page_template=post_page_template, user=request.user)

                if 'save_post' in request.POST:
                    messages.success(request, 'Post saved successfully!')
                else:
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
    paginator = Paginator(pages, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pages_manager/pages_list.html', {'page_obj': page_obj})

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


    # access_token_valid = True
    # access_token = request.session.get('access_token')
    # if not access_token:
    #     access_token_valid = False
    # else:
    #     fb_manager = FacebookTokenManager(
    #         app_id=settings.FACEBOOK_APP_ID,
    #         app_secret=settings.FACEBOOK_APP_SECRET,
    #         redirect_uri=settings.FACEBOOK_REDIRECT_URI
    #     )
    #     try:
    #         fb_manager.set_access_token(access_token)
    #         fb_manager.get_user_pages()
    #     except facebook.GraphAPIError:
    #         access_token_valid = False

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

# # @login_required
# def log_view(request):
#     logs = PostLog.objects.all().order_by('-scheduled_time')
#     form = LogPostFilterForm(request.GET or None)

#     if form.is_valid():
#         if form.cleaned_data.get('start_date'):
#             logs = logs.filter(post_page_template__post__publication_time__gte=form.cleaned_data['start_date'])
#         if form.cleaned_data.get('end_date'):
#             logs = logs.filter(post_page_template__post__publication_time__lte=form.cleaned_data['end_date'])
#         if form.cleaned_data.get('facebook_page'):
#             logs = logs.filter(post_page_template__facebook_page__in=form.cleaned_data['facebook_page'])
#         if form.cleaned_data.get('user'):
#             logs = logs.filter(post_page_template__post__user__in=form.cleaned_data['user'])

#     # Pagination
#     paginator = Paginator(logs, 10)  # Show 10 logs per page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     return render(request, 'posts/log.html', {'page_obj': page_obj, 'form': form})

def log_view(request):
    posts = Post.objects.all().order_by('-publication_time')
    form = LogPostFilterForm(request.GET or None)

    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            posts = posts.filter(publication_time__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            posts = posts.filter(publication_time__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('facebook_page'):
            posts = posts.filter(facebook_pages__in=form.cleaned_data['facebook_page'])
        if form.cleaned_data.get('user'):
            posts = posts.filter(user__in=form.cleaned_data['user'])

    # Pagination
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'posts/log.html', {'page_obj': page_obj, 'form': form})


@csrf_exempt
def republish_posts(request):
    '''
    This View will handle ajax post request from form in "log.html" page
    the form exist in modal.
    this view should handle the validations form for Re-publishing posts modal,
    and handle the creation of the celery tasks.
    '''
    if request.method == 'POST':
        try:
            data = unquote(request.body.decode('utf-8'))
            data_dict = dict(param.split('=') for param in data.split('&'))

            selected_posts = request.POST.getlist('selectedLogs[]')
            publication_time = data_dict.get('publicationTime', '')
            interval_hours = int(data_dict.get('intervalHours', 0))
            interval_minutes = int(data_dict.get('intervalMinutes', 0))
            facebook_pages = request.POST.getlist('facebookPages[]')
            idle_time = data_dict.get('idleTime' , '')
            publish_now = data_dict.get('publishNow') == 'true'
            user_timezone = data_dict.get('userTimezone', '')

            if not publication_time:
                publication_time = None

            if selected_posts:
                selected_posts = list(map(int, selected_posts))

            if facebook_pages:
                facebook_pages = list(map(int, facebook_pages))
            
            # if publication_time:
            #     publication_time = get_aware_datetime(publication_time)
            #     # # Convert to UTC time
            #     publication_time = publication_time.astimezone(pytz.UTC)
            #     publication_time = publication_time
            # Convert publication_time to a timezone-aware datetime
            if publication_time:
                publication_time = parse(publication_time)
                local_tz = pytz.timezone(user_timezone)
                publication_time = local_tz.localize(publication_time)
                publication_time = publication_time.astimezone(pytz.UTC)

            
            print("publication_time: " , publication_time)
            print("selected_posts: " , selected_posts)

            # Perform validations

            # Get the current time in UTC
            current_time_utc = timezone.now()

            if publication_time:
                # Check if publication_time is at least 10 minutes in the future
                if publication_time <= current_time_utc + timedelta(minutes=10):
                    return JsonResponse({'error': 'Publication time must be at least 10 minutes in the future.'}, status=400)

            if not selected_posts :
                return JsonResponse({'error': 'You must select at least one post to continue'}, status=400)

            if not publish_now and not publication_time:
                return JsonResponse({'error': 'You must set a publication time if not publishing immediately.'}, status=400)
            
            if not facebook_pages:
                return JsonResponse({'error': 'Facebook Pages: Missing required field'}, status=400)

            if publication_time and publish_now:
                return JsonResponse({'error': 'If you set the publishing time now, you cannot schedule the publishing time using Publication Time'}, status=400)

            if not idle_time.strip():
                return JsonResponse({'error': 'Idle time between posting posts: Missing required field'}, status=400)

            if not idle_time.strip().isnumeric():
                return JsonResponse({'error': 'Idle time between posting posts: must to be numeric value only'}, status=400)
            else:
                idle_time = float(idle_time)
            
            print("idle_time: " , idle_time)
            # Create the background task
            task = BackgroundTask.objects.create(
                publication_time=publication_time,
                interval_hours=interval_hours,
                interval_minutes=interval_minutes,
                publish_now=publish_now,
                idel_time=idle_time,
            )

            task.selected_posts.set(selected_posts)
            task.facebook_pages.set(facebook_pages)
            task.save()

            print("selected_logs: ", task.selected_posts)
            print("publication_time: ", task.publication_time)
            print("publication_time: ", type(task.publication_time))
            print("interval_hours: ", type(task.interval_hours))
            print("facebook_pages: ", type(task.facebook_pages))
            print("publish_now: ", publish_now)

            # Schedule the background task with Celery
            print("task.publication_time: ", task.publication_time)
            res = schedule_task.delay(task.id)

            return JsonResponse({'success': 'Posts scheduled for republishing'})
        except Exception as e:
            print("Error in republish_posts request view: ", str(e))
            try:
                task.delete()
            except Exception as error_delete:
                print("error_delete the background task" , str(error_delete))
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def background_tasks(request):
    if request.method == 'POST' and 'delete_tasks' in request.POST:
        task_ids = json.loads(request.POST.get('delete_tasks'))
        BackgroundTask.objects.filter(id__in=task_ids).delete()
        return redirect('background_tasks')

    tasks = BackgroundTask.objects.all().order_by('-updated_at')
    paginator = Paginator(tasks, 10)  # Show 10 tasks per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'posts/background_tasks.html', {'page_obj': page_obj})


def delete_posts(request):
    if request.method == 'POST':
        selected_posts = request.POST.getlist('selectedPosts[]')

        if selected_posts:
            # Retrieve the selected PostLog instances
            posts_to_delete = PostLog.objects.filter(post_page_template__post_id__in=selected_posts)

            # Collect images to delete from both Post and PostFacebookPageTemplate models
            images_to_delete = set()
            posts_to_delete_ids = set()
            post_fb_template_images = set()

            for post_log in posts_to_delete:
                post = post_log.post_page_template.post
                # Collect images from Post model
                image_path = post.image.path
                if default_storage.exists(image_path):
                    images_to_delete.add(image_path)

                # Collect IDs of posts to delete
                posts_to_delete_ids.add(post.id)

            # Collect images from PostFacebookPageTemplate model
            fb_templates = PostFacebookPageTemplate.objects.filter(post_id__in=posts_to_delete_ids)
            for fb_template in fb_templates:
                if fb_template.image:
                    image_path = fb_template.image.path
                    if default_storage.exists(image_path):
                        post_fb_template_images.add(image_path)

            # Delete associated images from Post model
            for image_path in images_to_delete:
                default_storage.delete(image_path)

            # Delete associated images from PostFacebookPageTemplate model
            for image_path in post_fb_template_images:
                default_storage.delete(image_path)

            # Delete the base posts
            Post.objects.filter(id__in=posts_to_delete_ids).delete()

            return JsonResponse({'success': 'Posts and associated images deleted successfully!'})
        else:
            return JsonResponse({'error': 'No posts selected.'}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)


def edit_post_log(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # post = log.post_page_template.post

    buttons = [
        {'name': 'save', 'label': 'Save', 'class': 'btn btn-primary'},
        {'name': 'save_republish', 'label': 'Save and Re-publish Post', 'class': 'btn btn-success'}
    ]

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if 'save_republish' in request.POST:
            try:
                sucess = handle_post_saving_or_republishing(request, False, post)
                if sucess:
                    return redirect(reverse('log'))
                else:
                    return render(request, 'posts/post_edit.html', {'form': form, 'buttons': buttons})
            except Exception as e:
                print("Error in handle_post_saving_or_republishing: " , str(e))

        else:
            try:
                sucess = handle_post_saving_or_republishing(request, True, post)
                if sucess:
                    return redirect(reverse('log'))
                else:
                    return render(request, 'posts/post_edit.html', {'form': form, 'buttons': buttons})
            except Exception as e:
                print("Error in handle_post_saving_or_republishing: " , str(e))
        
    else:
        post.publish_now = False
        post.publication_time = None
        form = PostForm(instance=post)


    context = {
        'form': form,
        'buttons': buttons,
    }
    return render(request, 'posts/post_edit.html', context)


def fetch_post_details(request, post_id):
    '''
    This view handles fetching information related to the expanded posts logs in the page [log.html]
    where the fetching info will include:
    1. the Facebook pages that posts are published on.
    2. the status of the publishing for each Facebook page.
    '''
    try:
        # Fetch all PostFacebookPageTemplate entries related to the post
        # post_logs = PostLog.objects.filter(post_page_template__post_id=post_id)
        all_post_page_templates = PostFacebookPageTemplate.objects.filter(post_id=post_id)

        # Extract Facebook page details from the PostFacebookPageTemplate entries
        facebook_pages = []
        for post_page_template in all_post_page_templates:
            facebook_page = post_page_template.facebook_page
            status = post_page_template.is_published
            failure_message = post_page_template.failure_message

            facebook_pages.append({
                'name': facebook_page.name,
                'status': status,  # Adjust this based on your actual field
                'failure_message':failure_message  # Adjust this based on your actual field
            })

        post_details = {
            'facebook_pages': facebook_pages
        }
        return JsonResponse(post_details, safe=False)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)

# Make sure the republishing is for one post for one page..
# other wise sugguest to republishing using Background Task republishing
# is better and will not happen any unexpected conflicts.
def handle_post_saving_or_republishing(request, save_only:bool, post=None):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            user_timezone = form.cleaned_data['user_timezone']
            publication_time = form.cleaned_data['publication_time']

            # Adjust publication time for user's timezone
            # print("user_timezone : " , user_timezone)
            # print("publication_time: " , publication_time)

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

            # if len(post.facebook_pages.all()) > 1:
            #     print(f"The Re-Publishing here is for one page only\n if you need to make Re-Publishing for this post\n You can do that using Background Task.")
            #     messages.error(request, 'The Re-Publishing here is for one page only\n if you need to make Re-Publishing for this post\n You can do that using Background Task.')
            #     return False
            try:
                with transaction.atomic():
                    post.save()
                    form.save_m2m()

                    # Apply templates to the image
                    try:
                        edited_images = apply_templates_to_image(
                            post.image.path,
                            post.facebook_pages.all(),
                            post.recipe_name,
                            should_translate=post.translate_post
                            )
                        for i, edited_image_data in enumerate(edited_images):
                            facebook_page = edited_image_data['facebook_page']
                            edited_image = edited_image_data['edited_image']
                            template_image = edited_image_data['template_image']
                            translated_recipe_name_input = edited_image_data['translated_recipe_name_input']

                            # Update PostFacebookPageTemplate with edited image and translated data
                            try:
                                specific_template = post.postfacebookpagetemplate_set.get(facebook_page=facebook_page)
                                path_editedimage = default_storage.save(edited_image.name, edited_image)
                                
                                if post.translate_post:
                                    specific_template.description = translate(post.description, 'en' , facebook_page.language)
                                else:
                                    specific_template.description = post.description
                                
                                if post.comment and post.translate_post:
                                    specific_template.comment = translate(post.comment, 'en' , facebook_page.language)
                                else:
                                    specific_template.comment = post.comment

                                specific_template.recipe_name = translated_recipe_name_input
                                specific_template.template = template_image
                                specific_template.image = path_editedimage
                                specific_template.save()
                            except Exception as e:
                                messages.error(request, 'Error updating PostFacebookPageTemplate')
                                raise e

                    except Exception as e:
                        messages.error(request, 'Error applying templates to image')
                        raise e

                    if save_only:
                        for post_page_template in post.postfacebookpagetemplate_set.all():
                            if post.publish_now:
                                current_time = timezone.now()
                                post.publication_time = current_time
                                post.save()
                            post_page_template.is_published = True
                            post_page_template.failure_message = "The post has been saved and not published"
                            post_page_template.save()
                    
                    else:
                        # Publish post to Facebook and log the action
                        for post_page_template in post.postfacebookpagetemplate_set.all():
                            publish_post(post_page_template=post_page_template)
                            # PostLog.objects.create(post_page_template=post_page_template, user=request.user)

                if save_only:
                    messages.success(request, 'Post saved successfully!')
                else:
                    messages.success(request, 'Post republished successfully!')
                
                return True
                # return redirect('log')

            except Exception as e:
                if not save_only:
                    messages.error(request, f'Error republishing post: {str(e)}')
                else:
                    messages.error(request, f'Error saving post: {str(e)}')
                return False
                # return render(request, 'posts/post_edit.html', context)

        else:
            messages.error(request, 'Form is not valid')
            return False



# def facebook_callback(request):
#     code = request.GET.get('code')
#     fb_manager = FacebookTokenManager(
#         app_id=settings.FACEBOOK_APP_ID,
#         app_secret=settings.FACEBOOK_APP_SECRET,
#         redirect_uri=settings.FACEBOOK_REDIRECT_URI
#     )
#     try:
#         short_lived_token = fb_manager.get_access_token_from_code(code)
#         print("short_lived_token: ", short_lived_token)
#         long_lived_token = fb_manager.get_long_lived_token()
#         print("long_lived_token: ", long_lived_token)
#         request.session['access_token'] = long_lived_token  # Store token in session or database as per your need
#         return redirect('page_create')
#     except Exception as e:
#         return HttpResponse(f'Error: {str(e)}')
    

# def facebook_login(request):
#     # fb_manager = FacebookTokenManager(
#     #     app_id=settings.FACEBOOK_APP_ID,
#     #     app_secret=settings.FACEBOOK_APP_SECRET,
#     #     redirect_uri=settings.FACEBOOK_REDIRECT_URI
#     # )
#     authorization_url = fb_manager.get_authorization_url()
#     return redirect(authorization_url)