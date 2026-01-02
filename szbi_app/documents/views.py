from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Document, DocumentISOMapping
from .forms import DocumentForm, DocumentISOMappingForm
from dictionary.models import ISORequirement


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"
    
    def get_queryset(self):
        return Document.objects.prefetch_related('iso_mappings').all()


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"
    success_url = reverse_lazy('documents:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = "documents/document_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['iso_mappings'] = self.object.iso_mappings.select_related(
            'iso_requirement', 'created_by'
        ).all()
        return context


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"
    
    def get_success_url(self):
        return reverse_lazy('documents:detail', kwargs={'pk': self.object.pk})


@login_required
def document_add_iso_mapping(request, pk):
    """Dodawanie powiązania dokumentu z wymaganiem ISO"""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = DocumentISOMappingForm(request.POST)
        if form.is_valid():
            mapping = form.save(commit=False)
            mapping.document = document
            mapping.created_by = request.user
            
            # Sprawdź czy powiązanie już istnieje
            if DocumentISOMapping.objects.filter(
                document=document, 
                iso_requirement=mapping.iso_requirement
            ).exists():
                messages.error(request, 'To powiązanie już istnieje.')
            else:
                mapping.save()
                messages.success(request, f'Powiązano dokument z wymaganiem {mapping.iso_requirement.iso_id}.')
            return redirect('documents:detail', pk=pk)
    else:
        form = DocumentISOMappingForm()
    
    return render(request, 'documents/document_add_iso_mapping.html', {
        'form': form,
        'document': document,
    })


@login_required
def document_remove_iso_mapping(request, pk, mapping_pk):
    """Usuwanie powiązania dokumentu z wymaganiem ISO"""
    document = get_object_or_404(Document, pk=pk)
    mapping = get_object_or_404(DocumentISOMapping, pk=mapping_pk, document=document)
    
    if request.method == 'POST':
        iso_id = mapping.iso_requirement.iso_id
        mapping.delete()
        messages.success(request, f'Usunięto powiązanie z wymaganiem {iso_id}.')
        return redirect('documents:detail', pk=pk)
    
    return render(request, 'documents/document_remove_iso_mapping.html', {
        'document': document,
        'mapping': mapping,
    })
