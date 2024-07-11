from celery import shared_task
from .models import BackgroundTask, PostLog, PostFacebookPageTemplate, FacebookPage
from datetime import timedelta
from django.utils import timezone
from .utils import publish_post, apply_templates_to_image, translate
from django.core.files.storage import default_storage

@shared_task
def publish_log(log_id, facebook_page_ids, task_id):
    try:
        log = PostLog.objects.get(id=log_id)
        org_post = log.post_page_template.post
        org_recipe_name = org_post.recipe_name
        org_description = org_post.description
        org_comment = org_post.comment
        org_image_path = org_post.image.path

        facebook_pages = FacebookPage.objects.filter(id__in=facebook_page_ids)

        edited_images = apply_templates_to_image(
            org_image_path,
            facebook_pages,
            org_recipe_name
        )

        # Override the post publish now field, but not save it in db
        org_post.publish_now = True

        task = BackgroundTask.objects.get(id=task_id)
        success_count = 0

        for i, edited_image_data in enumerate(edited_images):
            facebook_page = edited_image_data['facebook_page']
            edited_image = edited_image_data['edited_image']
            template_image = edited_image_data['template_image']
            translated_recipe_name_input = edited_image_data['translated_recipe_name_input']
            translated_description = translate(org_description, 'en', facebook_page.language)
            translated_comment = translate(org_comment, 'en', facebook_page.language)

            path_editedimage = default_storage.save(edited_image.name, edited_image)

            print(f"Edited image path: {edited_image.name}")

            # Creating an instance of PostFacebookPageTemplate
            ins = PostFacebookPageTemplate(
                post=org_post, 
                facebook_page=facebook_page,  
                template=template_image, 
                description=translated_description,
                comment=translated_comment,
                recipe_name=translated_recipe_name_input,
                image=path_editedimage,
                is_published=False,
                failure_message="This is background task..."
            )

            publish_post(post_page_template=ins, overid_db_ins=False)

            success_count += 1

            print(f"Successfully published log {log_id}")

            # Delete the saved image after it's no longer needed
            default_storage.delete(path_editedimage)
            print(f"Deleted image path: {path_editedimage}")

        task.number_succes_logs += success_count
        task.save()
        task.calculate_status()

    except Exception as e:
        print(f"Error publishing log {log_id}: {e}")

@shared_task
def schedule_task(task_id):
    print("<<< schedule_task is running >>>")
    try:
        task = BackgroundTask.objects.get(id=task_id)
        interval = timedelta(hours=task.interval_hours, minutes=task.interval_minutes)
        facebook_pages = task.facebook_pages.all()
        facebook_page_ids = [page.id for page in facebook_pages]
        next_time = task.publication_time if not task.publish_now else timezone.now()

        print(f"Scheduling task {task_id} to start at {next_time}")
        
        for log in task.selected_logs.all():
            try:
                publish_log.apply_async((log.id, facebook_page_ids, task.id), eta=next_time)
                print(f"Scheduled log {log.id} for publishing at {next_time}")
                next_time += interval
            except Exception as e:
                print(f"Error scheduling log {log.id}: {e}")

    except Exception as e:
        print(f"Error scheduling task {task_id}: {e}")