import facebook
from django.utils import timezone
# from django.conf import settings
import random
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from io import BytesIO
import matplotlib.font_manager as fm
from django.core.files.storage import default_storage
import os
# from libretranslatepy import LibreTranslateAPI
from deep_translator import GoogleTranslator
import json
from .models import PostFacebookPageTemplate
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware
from django.conf import settings

def apply_templates_to_image(original_image_path, facebook_pages, org_recipe_name_input, should_translate: bool):
    try:
        # Open the original image
        original_image = Image.open(original_image_path)

        edited_images = []

        for facebook_page in facebook_pages:
            # Translate text if needed.
            if should_translate:
                try:
                    language = facebook_page.language
                    if language != 'en':  # 'en' : is the default language.
                        recipe_name_input = translate(org_recipe_name_input, 'en', language)
                    else:
                        recipe_name_input = org_recipe_name_input
                except Exception as e:
                    print("Exception in applying Translation To Template: ", str(e))
                    raise e
            else:
                recipe_name_input = org_recipe_name_input

            # Get related templates
            templates = facebook_page.templates.all()

            if not templates.exists():
                # No templates, append the original image
                try:
                    image_io = BytesIO()
                    original_image.save(image_io, format='PNG')

                    file_name_without_extension = os.path.splitext(os.path.basename(original_image_path))[0]

                    image_content = ContentFile(image_io.getvalue(), name=f'post_page_templates/{file_name_without_extension}.png')

                    # Append the original image to the list
                    edited_images.append({
                        'facebook_page': facebook_page,
                        'edited_image': image_content,  # ContentFile
                        'template_image': None,
                        'translated_recipe_name_input': recipe_name_input
                    })
                except Exception as e:
                    print("Error saving original image: ", str(e))
                    raise e
                
                continue  # Skip to the next Facebook page

            # Select a random template
            template = random.choice(templates)

            try:
                procced_bg_image = process_preview_template(
                    template=template,
                    bg_img_pth=template.background_image.path, 
                    text=recipe_name_input
                )
            except Exception as e:
                print("Cannot process_preview_template: ", str(e))
                raise e

            if has_alpha(procced_bg_image):
                procced_bg_image = extract_and_resize_alpha_mask(procced_bg_image)

            # Make a copy of the original image to apply the template
            edited_image = original_image.copy()
            # draw = ImageDraw.Draw(edited_image)

            # Get Position For Pasting the Background image on the original image.
            if template.background_position == 'top':
                bg_position = (0, 0)
            else:
                _, img_h = edited_image.size
                _, bg_h = procced_bg_image.size
                bg_position = (0, img_h - bg_h)

            # Paste the Processed background image into the main image.
            try:
                edited_image.paste(procced_bg_image, bg_position, procced_bg_image)
            except Exception as e:
                print("Error pasting background image: ", str(e))
                raise e

            # Save the edited image to a BytesIO object
            try:
                image_io = BytesIO()
                edited_image.save(image_io, format='PNG')

                file_name_without_extension = os.path.splitext(os.path.basename(original_image_path))[0]

                image_content = ContentFile(image_io.getvalue(), name=f'post_page_templates/{file_name_without_extension}.png')

                # Append the edited image to the list
                edited_images.append({
                    'facebook_page': facebook_page,
                    'edited_image': image_content,  # ContentFile
                    'template_image': template,
                    'translated_recipe_name_input': recipe_name_input
                })
            except Exception as e:
                print("Error saving edited image: ", str(e))
                raise e
    except Exception as e:
        print("Exception in applying Template: ", str(e))
        raise e

    return edited_images


def get_system_font_path(font_name):
    font_manager = fm.FontManager()
    for font_info in font_manager.ttflist:
        if font_info.name == font_name:
            return font_info.fname
    return None  # Return None if font path not found

def get_user_font_path(font_name):
    fonts_dir = settings.FONTS_DIR
    if not os.path.exists(fonts_dir):
        return None  # Return None if fonts directory doesn't exist

    # List all .ttf files in the fonts directory
    font_files = [os.path.splitext(f)[0] for f in os.listdir(fonts_dir) if os.path.isfile(os.path.join(fonts_dir, f)) and f.lower().endswith('.ttf')]

    # Search for the font file by name
    for file_name in font_files:
        if file_name.lower() == font_name.lower():  # Case insensitive match
            return os.path.join(fonts_dir, f"{file_name}.ttf")

def has_alpha(image):
    """
    Check if an image has an alpha (transparent) layer.

    Args:
    image_path (str): Path to the image file.

    Returns:
    bool: True if the image has an alpha layer, False otherwise.
    """
    # image = Image.open(image_path)
    return image.mode in ('RGBA', 'LA', 'P')
    # except Exception as e:
    #     print(f"Error opening image: {e}")
    #     return False

def extract_and_resize_alpha_mask(image, output_path=None):
    """
    Extract the alpha mask from an image, crop it to the non-transparent parts, and save the result.

    Args:
    image_path (str): Path to the input image file.
    output_path (str): Path to save the extracted alpha mask image.
    """
    try:
        # Ensure the image has an alpha channel
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # image = Image.open(image_path).convert("RGBA")
        alpha = image.split()[3]  # Extract the alpha channel
        
        # Find the bounding box of the non-transparent regions
        bbox = alpha.getbbox()
        
        if bbox:
            # Crop the original image to the bounding box
            image_cropped = image.crop(bbox)
            
            # Save the cropped image
            if output_path:
                image_cropped.save(output_path)
            print(f"Cropped image extracted and saved to {output_path}")
            return image_cropped
        else:
            print("The image is fully transparent or has no transparent regions.")
            return image
    
    except IndexError as e:
        print("Error: The image does not have an alpha channel.")
        raise e
    
    except Exception as e:
        print(f"Error processing image: {e}")
        raise e

def override_image_with_content_file(existing_image_path, new_content_file:ContentFile):
    # Save the new content to the existing image path using Django's default storage
    try:
        if default_storage.exists(existing_image_path):
            default_storage.delete(existing_image_path)
        default_storage.save(existing_image_path, new_content_file)
    except Exception as e:
        print("[Error][override_image_with_content_file]: ", str(e))
        raise e

def translate(text, source='en' , to = '') -> str:
    '''Return the translated text from "source" to "to" Languge '''

    # lt = LibreTranslateAPI("https://translate.terraprint.co/")

    if text and (to == source):
        return text

    if text and to and source:
        try:
            translated = GoogleTranslator(source=source, target=to).translate(text)  # output -> Weiter so, du bist großartig
            # translated_text = translate_api(text, source, to, timeout=30)
            print("translated_text: ", translated)
            return translated.strip()
        except Exception as e:
            raise e
    else:
        raise Exception("The Translation process need: 'text', 'source languge', 'to languge'.")

def publish_post(post_page_template: PostFacebookPageTemplate, overid_db_ins=True):
    post = post_page_template.post
    facebook_page = post_page_template.facebook_page
    recipe_name = post_page_template.recipe_name
    image = post_page_template.image
    description = post_page_template.description
    comment = post_page_template.comment


    # Create a connection to the Facebook Graph API
    graph = facebook.GraphAPI(access_token=facebook_page.access_token)

    try:
        # If there is an image, upload it first without publishing it
        photo_id = None
        if image:
            with open(image.path, 'rb') as image_file:
                photo_response = graph.put_photo(
                    image=image_file,  # Assuming 'image' is a Django FileField or ImageField
                    album_path=f'{facebook_page.page_id}/photos',
                    published=False  # Do not publish the photo as a separate post
                )
                photo_id = photo_response['id']

        if post.publish_now:
            # Attempt to publish the post immediately
            if photo_id:
                attached_media = [{'media_fbid': photo_id}]
                response = graph.put_object(
                    parent_object=facebook_page.page_id,
                    connection_name='feed',
                    message=description,
                    name=recipe_name,  # Include the recipe_name as the title
                    attached_media=json.dumps(attached_media)  # Convert the list to a JSON string
                )
            else:
                response = graph.put_object(
                    parent_object=facebook_page.page_id,
                    connection_name='feed',
                    message=description,
                    name=recipe_name  # Include the recipe_name as the title
                )

            # If successful, update the post_page_template
            if overid_db_ins:
                current_time = timezone.now()
                post.publication_time = current_time
                # post.publish_now = True
                post_page_template.is_published = True
                post_page_template.failure_message = "Successfully published"
                post_page_template.save()
                post.save()
        else:
            # Schedule the post
            scheduled_time = int(post.publication_time.timestamp())
            # print("post_scheduled_time: ", post.publication_time)
            # print("scheduled_time_timestamp: ", scheduled_time)
            if photo_id:
                attached_media = [{'media_fbid': photo_id}]
                response = graph.put_object(
                    parent_object=facebook_page.page_id,
                    connection_name='feed',
                    message=description,
                    name=recipe_name,  # Include the recipe_name as the title
                    attached_media=json.dumps(attached_media),  # Convert the list to a JSON string
                    published=False,
                    scheduled_publish_time=scheduled_time
                )
            else:
                response = graph.put_object(
                    parent_object=facebook_page.page_id,
                    connection_name='feed',
                    message=description,
                    name=recipe_name,  # Include the recipe_name as the title
                    published=False,
                    scheduled_publish_time=scheduled_time
                )

            # Update the post_page_template with scheduled status
            if overid_db_ins:
                post_page_template.is_published = True
                post_page_template.failure_message = "The post has been scheduled for publication."
                post_page_template.save()
        
        add_comment_to_post(
            graph=graph,
            post_id=response['id'],
            comment_msg=comment,
            scheduled_time=post.publication_time # datetime or none.
        )

    except facebook.GraphAPIError as e:
        # If there's an error, update the failure message
        post_page_template.is_published = False
        post_page_template.failure_message = f"Failed to publish: {str(e)}"
        post_page_template.save()
        print("facebook.GraphAPIError: ", str(e))
    
    # Update or refresh the Access Token For that Page has been publishing now...
    try:
        token_info  = graph.extend_access_token(
            app_id= facebook_page.app_id,
            app_secret= facebook_page.app_secret
            )
        facebook_page.access_token = token_info['access_token']
        facebook_page.save()
        # messages.error(request, 'refresh access token done.')
    except Exception as e:
        print("Exception When refresh the Access Token: ", str(e))
        # messages.error(request, 'refresh access did not work')
        pass

def add_comment_to_post(graph, post_id:str , comment_msg:str, scheduled_time):
    if graph and post_id and comment_msg:
        try:
            if scheduled_time:
                scheduled_time = int(scheduled_time.timestamp())
                scheduled_time += 5
                graph.put_object(
                    post_id,
                    "comments",
                    message=comment_msg,
                    published=False,
                    scheduled_publish_time=scheduled_time
                    )
            else:
                graph.put_object(post_id, "comments", message=comment_msg)
        except Exception as e:
            print("Error in add_comment_to_post: ", str(e))
            raise e

# ---------------------------------- My code To handle Acess Token -----------------------

class FacebookTokenManager:
    def __init__(self, app_id, app_secret, redirect_uri):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.short_lived_token = None
        self.long_lived_token = None
        self.graph = None

    def get_access_token_from_code(self, code):
        self.graph = facebook.GraphAPI()
        token_info = self.graph.get_access_token_from_code(
            code,
            redirect_uri=self.redirect_uri,
            app_id=self.app_id,
            app_secret=self.app_secret
        )
        self.short_lived_token = token_info['access_token']
        return self.short_lived_token

    def get_long_lived_token(self):
        self.graph = facebook.GraphAPI(access_token=self.short_lived_token)
        token_info = self.graph.extend_access_token(
            app_id=self.app_id,
            app_secret=self.app_secret
        )
        self.long_lived_token = token_info['access_token']
        return self.long_lived_token

    def set_access_token(self, token):
        self.long_lived_token = token
        self.graph = facebook.GraphAPI(access_token=self.long_lived_token)

    def get_user_pages(self):
        self.graph = facebook.GraphAPI(access_token=self.long_lived_token)
        pages = self.graph.get_connections(id='me', connection_name='accounts')
        return pages['data']

    def refresh_access_token(self, user_access_token):
        """ Refresh the user access token if it is expired. """
        try:
            self.graph = facebook.GraphAPI(access_token=user_access_token)
            extended_token_info = self.graph.extend_access_token(
                app_id=self.app_id,
                app_secret=self.app_secret
            )
            return extended_token_info['access_token']
        except Exception as e:
            return None
    
    def get_authorization_url(self):
        oauth_dialog_url = f"https://www.facebook.com/v10.0/dialog/oauth?client_id={self.app_id}&redirect_uri={self.redirect_uri}&scope=pages_manage_posts,pages_read_engagement"
        # oauth_dialog_url = f"https://www.facebook.com/v10.0/dialog/oauth?client_id={self.app_id}&redirect_uri={self.redirect_uri}"

        return oauth_dialog_url

def get_aware_datetime(date_str:str):
    if date_str:
        ret = parse_datetime(date_str)
        if not is_aware(ret):
            ret = make_aware(ret)
        return ret
    return None

def process_preview_template(template, text: str, bg_img_pth: str):
    # Load the background image
    if not bg_img_pth:
        raise ValueError("Template must have a background image.")
    
    background_image = Image.open(bg_img_pth)

    # Load the font
    font_path = get_user_font_path(template.font_type)
    if not os.path.exists(font_path):
        raise ValueError("Font file not found.")
    
    font = ImageFont.truetype(font_path, int(template.text_size))

    # Create an ImageDraw object
    draw = ImageDraw.Draw(background_image)

    # Calculate the bounding box
    if isinstance(template.bounding_box, str):
        bounding_box_dict = json.loads(template.bounding_box)
        bounding_box_tuple = (
            bounding_box_dict['x'], 
            bounding_box_dict['y'], 
            bounding_box_dict['width'], 
            bounding_box_dict['height']
        )
    elif isinstance(template.bounding_box, dict):
        bounding_box_dict = template.bounding_box
        bounding_box_tuple = (
            bounding_box_dict['x'], 
            bounding_box_dict['y'], 
            bounding_box_dict['width'], 
            bounding_box_dict['height']
        )
    else:
        bounding_box_tuple = template.bounding_box
    
    if not bounding_box_tuple:
        raise ValueError("Template must have a bounding box.")

    bounding_box_tuple = tuple(abs(float(value)) for value in bounding_box_tuple)
    left, top, width, height = bounding_box_tuple

    # Draw bounding box for debugging
    # draw.rectangle([(left, top), (left + width, top + height)], outline='red', width=3)

    # Initialize variables for text wrapping and vertical centering
    wrapped_lines = []
    total_text_height = 0
    line_spacing = 8  # Adjust as needed

    # Wrap text to fit within the bounding box width
    for line in text.split('\n'):
        words = line.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_width = draw.textlength(test_line, font=font,)
            if test_width <= width:
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                total_text_height += draw.textbbox((0, 0), current_line, font=font)[3] - draw.textbbox((0, 0), current_line, font=font,)[1]
                current_line = word
        if current_line:
            wrapped_lines.append(current_line)
            total_text_height += draw.textbbox((0, 0), current_line, font=font,)[3] - draw.textbbox((0, 0), current_line, font=font,)[1]

    # Calculate starting Y position for vertical centering
    # start_y = top + (height - total_text_height) / 2
    # start_y = top + (total_text_height) / 2
    start_y = top

    # Draw the text line by line with spacing
    current_height = start_y
    for line in wrapped_lines:
        text_width = draw.textlength(line, font=font,)
        text_bbox = draw.textbbox((0, 0), line, font=font,)
        text_height = text_bbox[3] - text_bbox[1]

        x_position = left + (width - text_width) / 2
        
        # Draw stroke if stroke_thickness > 0
        if int(template.stroke_thickness) > 0:
            draw.text(
                (x_position, current_height),
                line,
                font=font,
                fill=template.stroke_color,
                stroke_width=int(template.stroke_thickness),
                stroke_fill=template.stroke_color
            )
        
        # Draw the text
        draw.text(
            (x_position, current_height),
            line,
            font=font,
            fill=template.text_color
        )
        
        current_height += text_height + line_spacing  # Add line spacing

        # Check if the next line will fit in the bounding box
        if current_height > top + height:
            raise ValueError("Text does not fit within the bounding box.")

    
    # ============ Previouse ================
    # # Save the image to a ContentFile
    # output = BytesIO()
    # background_image.save(output, format='PNG')
    # output.seek(0)
    # return ContentFile(output.read(), 'edited_image.png')

    # ============ New ======================
    return background_image