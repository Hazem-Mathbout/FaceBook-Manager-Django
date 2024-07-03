from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Template
from .forms import TemplateForm
from django.views.generic.detail import DetailView
from django.core.exceptions import ValidationError

def template_list(request):
    templates = Template.objects.all()
    return render(request, 'template_manager/template_list.html', {'templates': templates})

def template_create(request):
    if request.method == 'POST':
        form = TemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template created successfully!')
            return redirect('template_list')
        else:
            messages.error(request, 'The Form Not Valid!')
    else:
        form = TemplateForm()
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
    return render(request, 'template_manager/template_form.html', {'form': form})

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