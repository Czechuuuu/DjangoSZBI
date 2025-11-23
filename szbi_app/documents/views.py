from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import Document

class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    fields = ['title', 'description']
    template_name = "documents/document_form.html"
    success_url = reverse_lazy('documents:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
