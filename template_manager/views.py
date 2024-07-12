import json
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .utils import process_preview_template

# from facebook_post_manager.posts.utils import apply_templates_to_image

from .models import Template
from .forms import TemplateForm, FontUploadForm
from django.views.generic.detail import DetailView
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.conf import settings
import os

def template_list(request):
    templates = Template.objects.all()
    # Pagination
    paginator = Paginator(templates, 10)  # Show 10 templates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'template_manager/template_list.html', {'page_obj': page_obj})

def template_create(request):
    if request.method == 'POST':
        form = TemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template created successfully!')
            return redirect('template_list')
        else:
            messages.error(request, 'The Template Form Not Valid!')
    else:
        form = TemplateForm()
    
    context = {
        'form': form,
        'buttons': [
            {'name': 'save_template', 'class': 'btn-primary', 'label': 'Save Template'},
            {'name': 'live_preview', 'class': 'btn btn-success', 'label': 'Live Preview'},
        ]
    }

    return render(request, 'template_manager/template_form.html', {'form': form})

def template_update(request, pk):
    template = get_object_or_404(Template, pk=pk)
    if request.method == 'POST':
        form = TemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template modified successfully!')
            return redirect('template_list')
        else:
            messages.error(request, 'The Form Not Valid!')
    else:
        form = TemplateForm(instance=template)

    # context = {
    #     'template': template,
    #     'buttons': [
    #         {'name': 'save_template', 'class': 'btn-primary', 'label': 'Save Template'},
    #         {'name': 'live_preview', 'class': 'btn btn-success', 'label': 'Live Preview'},
    #     ]
    # }

    return render(request, 'template_manager/template_form.html', {'form' : form})

def template_delete(request, pk):
    template = get_object_or_404(Template, pk=pk)
    if request.method == 'POST':
        try:
            template.delete()
            messages.success(request, 'Template deleted successfully!', 'success')
            return redirect('template_list')
        except ValidationError as e:
            messages.error(request, e.message)

    return render(request, 'template_manager/template_confirm_delete.html', {'template': template})


class TemplateDetailView(DetailView):
    model = Template
    template_name = 'template_manager/template_detail.html'
    context_object_name = 'template'


def install_fonts(files):
    if not os.path.exists(settings.FONTS_DIR):
        os.makedirs(settings.FONTS_DIR)
    for file in files:
        file_path = os.path.join(settings.FONTS_DIR, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

def font_upload_view(request):
    if request.method == 'POST':
        form = FontUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                install_fonts(form.cleaned_data['fonts'])
                messages.success(request, "Fonts installed successfully!")
                return redirect('template_list')
            except Exception as e:
                messages.error(request, f"Error installing fonts: {str(e)}")
        else:
            messages.error(request, "Please upload valid .ttf files.")
    else:
        form = FontUploadForm()
    return render(request, 'template_manager/font_upload.html', {'form': form})



def live_preview(request):
    if request.method == 'GET' or request.method == 'POST':
        template_id = request.GET.get('template_id') or request.POST.get('template_id')
        template_instance = None

        if template_id:
            try:
                template_instance = Template.objects.get(pk=template_id)
            except Template.DoesNotExist:
                return HttpResponse('Template not found.', status=404)

        if request.method == 'POST':
            form = TemplateForm(request.POST, request.FILES, instance=template_instance)
            if form.is_valid():
                template_instance = form.instance
                background_image = request.FILES.get('background_image')
                background_image_url = request.POST.get('background_image_url', None)
                # print("background_image_url: " , background_image_url)
                
                # Save the temporary image to a temporary location
                if background_image :
                    fs = FileSystemStorage(location=settings.TEMP_MEDIA_ROOT)
                    filename = fs.save(background_image.name, background_image)
                    background_image_url = settings.TEMP_MEDIA_URL + filename

                context = {
                    'template': template_instance,
                    'background_image_url': background_image_url,
                    'form': form,
                }
                return render(request, 'template_manager/live_preview.html', context)
            else:
                return HttpResponse('This Template is not valid.', status=400)
        else:
            form = TemplateForm(instance=template_instance)

        context = {
            'template': template_instance,
            'background_image_url': template_instance.background_image.url,
            'form': form,
        }
        return render(request, 'template_manager/live_preview.html', context)
    else:
        return HttpResponse('Invalid request method', status=405)

@csrf_exempt
def generate_preview_image(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        text = data.get('text', '')
        background_image_url = data.get('backgroundImageUrl', '')
        form_data = data.get('formData', {})  # Retrieve formData from request body

        # Process the form data (if needed)
        # Example usage: print(form_data.get('field_name', ''))
        instance = Template(
            name=form_data.get('name', ''),
            font_type=form_data.get('font_type', ''),
            text_color=form_data.get('text_color', ''),
            text_size=form_data.get('text_size', 0),
            stroke_thickness=form_data.get('stroke_thickness', 0),
            stroke_color=form_data.get('stroke_color', ''),
            background_position=form_data.get('background_position', ''),
            bounding_box=form_data.get('bounding_box', {}),
            background_image = background_image_url
        )

        try:
            # Call the utility function to generate the image
            edited_image = process_preview_template(
                template=instance, 
                text=text,
                bg_img_name=background_image_url
            )
        except Exception as e:
            error_message = str(e)
            print("Error in generate_preview_image: " , error_message)
            # raise e
            return JsonResponse({'error': error_message}, status=400)
        
        # Save the image to a temporary location
        fs = FileSystemStorage(location=settings.TEMP_MEDIA_ROOT)
        filename = fs.save('edited_image.png', edited_image)
        image_url = os.path.join(settings.TEMP_MEDIA_URL, filename)

        # Return the generated image data as a response
        return JsonResponse({'image_url': image_url })
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)