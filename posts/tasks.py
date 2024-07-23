from celery import shared_task
from .models import BackgroundTask, Post, PostFacebookPageTemplate, FacebookPage
from datetime import timedelta
from django.utils import timezone
from .utils import publish_post, apply_templates_to_image, translate
from django.core.files.storage import default_storage
import time

@shared_task
def publish_log(log_id, facebook_page_ids, task_id, publication_time):
    try:
        org_post = Post.objects.get(id=log_id)
        # org_post = post.post_page_template.post
        org_recipe_name = org_post.recipe_name
        org_description = org_post.description
        org_comment = org_post.comment
        org_image_path = org_post.image.path

        facebook_pages = FacebookPage.objects.filter(id__in=facebook_page_ids)

        edited_images = apply_templates_to_image(
            org_image_path,
            facebook_pages,
            org_recipe_name,
            should_translate=org_post.translate_post,
        )

        # Override the post publish now field, but not save it in db
        # Check if the publication_time in the feature and after 10 minutes from now
        # beacuse the facebook don't allow to schedual posts under 10 minutes in the featur 
        current_time = timezone.now()
        future_time = current_time + timedelta(minutes=10)
        if publication_time > future_time:
            org_post.publication_time = publication_time
            org_post.publish_now = False
        else:
            org_post.publish_now = True

        task = BackgroundTask.objects.get(id=task_id)
        success_count = 0

        for i, edited_image_data in enumerate(edited_images):
            try:
                facebook_page = edited_image_data['facebook_page']
                edited_image = edited_image_data['edited_image']
                template_image = edited_image_data['template_image']
                translated_recipe_name_input = edited_image_data['translated_recipe_name_input']
                
                if org_post.translate_post:
                    translated_description = translate(org_description, 'en', facebook_page.language)
                else:
                    translated_description = org_description

                if org_post.translate_post:
                    if org_comment:
                        translated_comment = translate(org_comment, 'en', facebook_page.language)
                    else:
                        translated_comment = org_comment
                else:
                    translated_comment = org_comment

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
            except Exception as e :
                print("Error in publish_log in background task: ", str(e))
                pass

        # task.number_succes_logs += success_count
        # task.save()
        # task.calculate_status()

    except Exception as e:
        print(f"Error publishing log {log_id}: {e}")

@shared_task
def schedule_task(task_id):
    print("<<< schedule_task is running >>>")
    try:
        task = BackgroundTask.objects.get(id=task_id)
        task.bg_task_status = 'in_progress'
        task.save()

        interval = timedelta(hours=task.interval_hours, minutes=task.interval_minutes)
        facebook_pages = task.facebook_pages.all()
        facebook_page_ids = [page.id for page in facebook_pages]
        next_time = task.publication_time if not task.publish_now else timezone.now()
        idel_time = task.idel_time

        print(f"Scheduling task {task_id} to start at {next_time}")
        
        for post in task.selected_posts.all():
            try:
                publish_log(post.id, facebook_page_ids, task.id, next_time)
                task.number_succes_logs += 1
                task.calculate_status()
                print(f"Scheduled log {post.id} for publishing at {next_time}")
                next_time += interval
                time.sleep(idel_time) # deafult 1 minute delay.
            except Exception as e:
                print(f"Error scheduling log {post.id}: {e}")
        
        task.bg_task_status = 'finished'
        task.save()

    except Exception as e:
        task.bg_task_status = 'failed'
        task.save()
        print(f"Error scheduling task {task_id}: {e}")