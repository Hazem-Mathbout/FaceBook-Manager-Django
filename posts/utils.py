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

# from typing import Dict, Any
# from urllib import request, parse
# import json
# def apply_templates_to_image(original_image_path, facebook_pages, recipe_name_input):
#     try:
#         # Open the original image
#         original_image = Image.open(original_image_path)

#         edited_images = []

#         for facebook_page in facebook_pages:
#             # Get related templates
#             templates = facebook_page.templates.all()

#             if not templates.exists():
#                 continue  # Skip if no templates are associated with the Facebook page
            
#             # Select a random template
#             template = random.choice(templates)

#             # Make a copy of the original image to apply the template
#             edited_image = original_image.copy()
#             draw = ImageDraw.Draw(edited_image)

#             # Get font path
#             font_path = get_font_path(template.font_type)

#             # Load the font
#             font = ImageFont.truetype(font_path, template.text_size)

#             # Set text position
#             # init_text_position = get_initial_text_position(edited_image.size, template.text_position, template.text_size)
#             text_position, wrapped_text = get_text_position(edited_image.size, template.text_position, recipe_name_input, font)

#             print("wrapped_text: ", wrapped_text)
#             # Wrap the recipe_name_input text
#             # max_width = edited_image.width - text_position[0]  # Adjust based on your text position
#             # wrapped_text = wrap_text(recipe_name_input, font, max_width)

#             # Draw the wrapped text on the image
#             y = text_position[1]
#             for line in wrapped_text:
#                 if template.stroke_thickness > 0:
#                     draw.text((text_position[0], y), line, font=font, fill=template.stroke_color, stroke_width=template.stroke_thickness, stroke_fill=template.stroke_color)
                
#                 draw.text((text_position[0], y), line, font=font, fill=template.text_color)
                
#                 # bounding_box = font.getbbox(line, direction='ltr')
#                 # h = bounding_box[1] - bounding_box[3]
#                 y += 100  # Move to the next line with some padding

#             # Save the edited image to a BytesIO object
#             image_io = BytesIO()
#             edited_image.save(image_io, format='PNG')
#             image_content = ContentFile(image_io.getvalue(), name=f'{facebook_page.name}_edited.png')

#             # Append the edited image to the list
#             edited_images.append({
#                 'facebook_page': facebook_page,
#                 'edited_image': image_content,
#             })
#     except Exception as e:
#         print("Exception in applying Template: ", str(e))
#         return str(e)
    
#     return edited_images




# -------------------------------------------------------

def apply_templates_to_image(original_image_path, facebook_pages, org_recipe_name_input):
    try:
        # Open the original image
        original_image = Image.open(original_image_path)

        edited_images = []

        for facebook_page in facebook_pages:
            # Translate text.
            try:
                language = facebook_page.language
                if language != 'en': # 'en' : is the default language.
                    recipe_name_input = translate(org_recipe_name_input, 'en', language)
                else:
                    recipe_name_input = org_recipe_name_input
            except Exception as e:
                print("Exception in applying Translation To Template: ", str(e))
                raise e

            # Get related templates
            templates = facebook_page.templates.all()

            if not templates.exists():
                continue  # Skip if no templates are associated with the Facebook page
            
            # Select a random template
            template = random.choice(templates)

            # Make a copy of the original image to apply the template
            edited_image = original_image.copy()
            draw = ImageDraw.Draw(edited_image)

            # Get font path
            font_path = get_font_path(template.font_type)

            # Load the font
            font = ImageFont.truetype(font_path, template.text_size)

            # Set text position
            try:
                text_position, wrapped_text = get_text_position(edited_image.size, template.text_position, recipe_name_input, font)
            except Exception as e:
                print("Error in get_text_position: ", str(e))
                raise e

            # Calculate text width and height for the bounding box
            try:
                text_width = max([font.getlength(line) for line in wrapped_text])
                text_height = template.text_size * len(wrapped_text)
            except Exception as e:
                print("Error calculating text width and height: ", str(e))
                raise e

            # Add padding to the text bounding box
            padding = 40
            padded_text_width = text_width + 2 * padding
            padded_text_height = text_height + 2 * padding

            # Check for background image
            if template.background_image:
                background_image = Image.open(template.background_image.path)
                
                # Checking if there is an alpha(transparent) layer.
                # Edit the background_image if there is transparent layer.
                if has_alpha(background_image):
                    background_image = extract_and_resize_alpha_mask(background_image)

                # Calculate the new size while maintaining the aspect ratio
                try:
                    bg_width, bg_height = background_image.size
                    aspect_ratio = bg_width / bg_height

                    if padded_text_width / aspect_ratio < padded_text_height:
                        new_bg_height = padded_text_height
                        new_bg_width = int(new_bg_height * aspect_ratio)
                    else:
                        new_bg_width = padded_text_width
                        new_bg_height = int(new_bg_width / aspect_ratio)
                except Exception as e:
                    print("Error calculating new background image size: ", str(e))
                    raise e

                background_image = background_image.resize((bg_width, int(new_bg_height)))
                # background_image = background_image.resize((int(padded_text_width), int(padded_text_height)))


                # Create a mask using the alpha channel of the background image
                try:
                    mask = background_image.split()[3]
                except Exception as e:
                    print("Error creating mask: ", str(e))
                    raise e

                # Calculate the position to paste the background image
                try:
                    range_x = int((new_bg_width - padded_text_width) // 2)
                    range_y = int((new_bg_height - padded_text_height) // 2)

                    bg_position = (
                        0,
                        min((text_position[1] - padding - range_y), (edited_image.size[1] - new_bg_height))
                    )
                except Exception as e:
                    print("Error calculating background image position: ", str(e))
                    raise e

                print("bg_position: ", bg_position)
                print("text_position: ", text_position)
                print("bg_image size: ", background_image.size)
                print("mask size: ", mask.size)

                # Paste the background image into the text area using the mask
                try:
                    edited_image.paste(background_image, bg_position, background_image)
                except Exception as e:
                    print("Error pasting background image: ", str(e))
                    raise e

            # Draw the wrapped text on the image
            try:
                if "bottom" in template.text_position:
                    bottom_padding = 20
                    y = (text_position[1] - bottom_padding) if (len(wrapped_text) > 1) else  text_position[1]
                elif "top" in template.text_position:
                    bottom_padding = 20
                    y = (text_position[1] + bottom_padding) if (len(wrapped_text) > 1) else  text_position[1]
                else:
                    y = text_position[1]

                for line in wrapped_text:
                    if template.stroke_thickness > 0:
                        draw.text((text_position[0], y), line, font=font, fill=template.stroke_color, stroke_width=template.stroke_thickness, stroke_fill=template.stroke_color)
                    draw.text((text_position[0], y), line, font=font, fill=template.text_color)
                    y += template.text_size  # Move to the next line
            except Exception as e:
                print("Error drawing text: ", str(e))
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
                    'edited_image': image_content,
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

# -------------------------------------------------------







# def get_initial_text_position(image_size, text_position_choice, text_size, padding=20):
#     width, height = image_size
#     positions = {
#         'top_left': (padding, padding),
#         'top_center': (width // 2, padding),
#         'top_right': (width - padding, padding),
#         'middle_left': (padding, height // 2),
#         'middle_center': (width // 2, height // 2),
#         'middle_right': (width - padding, height // 2),
#         'bottom_left': (padding, height - text_size - padding),
#         'bottom_center': (width // 2, height - text_size - padding),
#         'bottom_right': (width - padding, height - text_size - padding),
#     }
#     return positions[text_position_choice]

def get_text_position(image_size, text_position_choice, text, font, padding=20):
    width, height = image_size
    max_text_width = width - 2 * padding
    wrapped_text = wrap_text(text, font, max_text_width)

    # Calculate total text height for wrapped text
    text_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in wrapped_text])
    text_width = max([font.getbbox(line)[2] - font.getbbox(line)[0] for line in wrapped_text])

    positions = {
        'top_left': (padding, padding),
        'top_center': ((width - text_width) // 2, padding),
        'top_right': (width - text_width - padding, padding),
        'middle_left': (padding, (height - text_height) // 2),
        'middle_center': ((width - text_width) // 2, (height - text_height) // 2),
        'middle_right': (width - text_width - padding, (height - text_height) // 2),
        'bottom_left': (padding, height - text_height - padding),
        'bottom_center': ((width - text_width) // 2, height - text_height - padding),
        'bottom_right': (width - text_width - padding, height - text_height - padding),
    }
    return positions[text_position_choice], wrapped_text


def wrap_text(text, title_font, max_width):
    all_lines = []
    all_words = text.split()  # Split text into words

    # Start with the first word
    line = []
    while all_words:
        word = all_words[0]
        new_text = ' '.join(line + [word]).strip()
        # print('>', word, new_text)
        if title_font.getlength(new_text) > max_width:
            all_lines.append(' '.join(line).strip())
            line = []
        else:
            line += [word]
            all_words = all_words[1:]
    
    if line:
        all_lines.append(' '.join(line).strip())

    # print("all_lines: " , all_lines)
    return all_lines

def get_font_path(font_name):
    font_manager = fm.FontManager()
    for font_info in font_manager.ttflist:
        if font_info.name == font_name:
            return font_info.fname
    return None  # Return None if font path not found


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
    



def publish_post(post_page_template: PostFacebookPageTemplate):
    post = post_page_template.post
    facebook_page = post_page_template.facebook_page
    recipe_name = post_page_template.recipe_name
    image = post_page_template.image
    description = post_page_template.description

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
            post_page_template.is_published = True
            post_page_template.failure_message = "The post has been scheduled for publication."
            post_page_template.save()
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

# Example usage
# post_page_template_instance = PostFacebookPageTemplate.objects.get(id=1)
# publish_post(post_page_template_instance)





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