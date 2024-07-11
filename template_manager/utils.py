# utils.py
import json
import matplotlib.font_manager as fm
import os
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from io import BytesIO
import os

def list_system_fonts():
    font_paths = fm.findSystemFonts(fontpaths=None, fontext='ttf')
    font_names = [fm.FontProperties(fname=font_path).get_name() for font_path in font_paths]
    return sorted(set(font_names))  # Return unique and sorted font names

def list_user_uploaded_fonts():
    fonts_dir = settings.FONTS_DIR
    if not os.path.exists(fonts_dir):
        return []  # Return empty list if directory doesn't exist

    # List all files in the fonts directory
    font_files = [f for f in os.listdir(fonts_dir) if os.path.isfile(os.path.join(fonts_dir, f))]

    # Filter only .ttf files and strip the file extension
    ttf_fonts = [os.path.splitext(f)[0] for f in font_files if f.lower().endswith('.ttf')]

    return ttf_fonts

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

def process_preview_template(template, text: str, bg_img_name: str):
    # Load the background image
    if not bg_img_name:
        raise ValueError("Template must have a background image.")
    
    try:
        background_image_path = os.path.join(template.background_image.storage.base_location, 'temp', bg_img_name)
        background_image = Image.open(background_image_path)
    except Exception as e:
        background_image_path = os.path.join(template.background_image.storage.base_location, 'templates_backgrounds', bg_img_name)
        background_image = Image.open(background_image_path)
        pass

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
    else:
        bounding_box_tuple = template.bounding_box
    
    if not bounding_box_tuple:
        raise ValueError("Template must have a bounding box.")
    
    bounding_box_tuple = tuple(abs(value) for value in bounding_box_tuple)
    left, top, width, height = bounding_box_tuple

    # Draw bounding box for debugging
    draw.rectangle([(left, top), (left + width, top + height)], outline='red', width=3)

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
            test_width = draw.textlength(test_line, font=font, font_size=int(template.text_size))
            if test_width <= width:
                current_line = test_line
            else:
                wrapped_lines.append(current_line)
                total_text_height += draw.textbbox((0, 0), current_line, font=font, font_size=int(template.text_size))[3] - draw.textbbox((0, 0), current_line, font=font, font_size=int(template.text_size))[1]
                current_line = word
        if current_line:
            wrapped_lines.append(current_line)
            total_text_height += draw.textbbox((0, 0), current_line, font=font, font_size=int(template.text_size))[3] - draw.textbbox((0, 0), current_line, font=font, font_size=int(template.text_size))[1]

    print("top: ", top)
    print("height: " , height)
    print("total_text_height: " , total_text_height)

    # Calculate starting Y position for vertical centering
    # start_y = top + (height - total_text_height) / 2
    # start_y = top + (total_text_height) / 2
    start_y = top
    print("start_y: " , start_y)

    # Draw the text line by line with spacing
    current_height = start_y
    for line in wrapped_lines:
        text_width = draw.textlength(line, font=font, font_size=int(template.text_size))
        text_bbox = draw.textbbox((0, 0), line, font=font, font_size=int(template.text_size))
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

    # Save the image to a ContentFile
    output = BytesIO()
    background_image.save(output, format='PNG')
    output.seek(0)
    return ContentFile(output.read(), 'edited_image.png')