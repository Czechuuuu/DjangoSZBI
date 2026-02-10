from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.db.models import Q

from .models import (
    Document, DocumentISOMapping, DocumentVersion,
    DocumentLog, DocumentAccess, DocumentAcknowledgement
)
from .forms import (
    DocumentForm, DocumentISOMappingForm, DocumentVersionForm,
    DocumentAccessForm, WorkflowTransitionForm
)
from dictionary.models import ISORequirement


def _log_action(document, user, action, description=""):
    """Helper do logowania akcji na dokumencie"""
    DocumentLog.objects.create(
        document=document,
        user=user,
        action=action,
        description=description
    )


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"
    
    def get_queryset(self):
        qs = Document.objects.prefetch_related('iso_mappings', 'versions').all()
        
        # Filtrowanie
        status = self.request.GET.get('status')
        doc_type = self.request.GET.get('type')
        search = self.request.GET.get('q')
        
        if status:
            qs = qs.filter(status=status)
        if doc_type:
            qs = qs.filter(document_type=doc_type)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(designation__icontains=search) |
                Q(description__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Document.STATUS
        context['type_choices'] = Document.DOCUMENT_TYPE_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['current_search'] = self.request.GET.get('q', '')
        return context


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"
    success_url = reverse_lazy('documents:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        _log_action(self.object, self.request.user, 'created',
                    f'Utworzono dokument [{self.object.designation}] {self.object.title}')
        messages.success(self.request, f'Dokument "{self.object.designation}" został utworzony.')
        return response


class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = "documents/document_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['iso_mappings'] = self.object.iso_mappings.select_related(
            'iso_requirement', 'created_by'
        ).all()
        context['versions'] = self.object.versions.all()
        context['current_version'] = self.object.get_current_version()
        context['access_entries'] = self.object.access_entries.select_related('permission_group', 'granted_by').all()
        context['acknowledgements'] = self.object.acknowledgements.select_related('user', 'version').all()
        context['logs'] = self.object.logs.select_related('user').all()[:20]
        context['workflow_form'] = WorkflowTransitionForm(document=self.object)
        context['allowed_transitions'] = self.object.get_allowed_transitions()
        
        # Sprawdź czy bieżący user potwierdził zapoznanie z aktualną wersją
        current_version = context['current_version']
        if current_version:
            context['user_acknowledged'] = DocumentAcknowledgement.objects.filter(
                document=self.object,
                user=self.request.user,
                version=current_version
            ).exists()
        else:
            context['user_acknowledged'] = False
        
        return context


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"
    
    def form_valid(self, form):
        response = super().form_valid(form)
        _log_action(self.object, self.request.user, 'updated',
                    f'Zaktualizowano dokument [{self.object.designation}]')
        messages.success(self.request, 'Dokument został zaktualizowany.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('documents:detail', kwargs={'pk': self.object.pk})


# === WERSJE ===

@login_required
def document_add_version(request, pk):
    """Dodawanie nowej wersji dokumentu"""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = DocumentVersionForm(request.POST, request.FILES)
        if form.is_valid():
            version = form.save(commit=False)
            version.document = document
            version.created_by = request.user
            
            if form.cleaned_data.get('mark_as_current'):
                version.is_current = True
            
            version.save()
            
            action = 'version_added'
            desc = f'Dodano wersję {version.version_number}'
            if version.is_current:
                desc += ' (oznaczona jako obowiązująca)'
                action = 'version_set_current'
            
            _log_action(document, request.user, action, desc)
            messages.success(request, f'Dodano wersję {version.version_number}.')
            return redirect('documents:detail', pk=pk)
    else:
        # Sugeruj kolejny numer wersji
        last_version = document.versions.first()
        suggested = "1.0"
        if last_version:
            try:
                parts = last_version.version_number.split('.')
                parts[-1] = str(int(parts[-1]) + 1)
                suggested = '.'.join(parts)
            except (ValueError, IndexError):
                suggested = last_version.version_number + ".1"
        
        form = DocumentVersionForm(initial={'version_number': suggested})
    
    return render(request, 'documents/document_add_version.html', {
        'form': form,
        'document': document,
    })


@login_required
def document_set_current_version(request, pk, version_pk):
    """Ustawienie wersji jako obowiązującej"""
    document = get_object_or_404(Document, pk=pk)
    version = get_object_or_404(DocumentVersion, pk=version_pk, document=document)
    
    if request.method == 'POST':
        version.is_current = True
        version.save()  # save() automatycznie zdejmie flagę z innych
        
        _log_action(document, request.user, 'version_set_current',
                    f'Ustawiono wersję {version.version_number} jako obowiązującą')
        messages.success(request, f'Wersja {version.version_number} jest teraz obowiązująca.')
    
    return redirect('documents:detail', pk=pk)


@login_required
def document_download_version(request, pk, version_pk):
    """Pobieranie pliku wersji dokumentu"""
    document = get_object_or_404(Document, pk=pk)
    version = get_object_or_404(DocumentVersion, pk=version_pk, document=document)
    
    if not version.file:
        raise Http404("Plik nie istnieje.")
    
    return FileResponse(version.file.open('rb'), as_attachment=True, 
                       filename=version.file.name.split('/')[-1])


# === WORKFLOW ===

@login_required
def document_workflow_transition(request, pk):
    """Zmiana statusu dokumentu (workflow)"""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = WorkflowTransitionForm(request.POST, document=document)
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            comment = form.cleaned_data.get('comment', '')
            
            if document.can_transition_to(new_status):
                old_status = document.get_status_display()
                document.status = new_status
                document.save()
                
                new_status_display = document.get_status_display()
                desc = f'Zmieniono status: {old_status} → {new_status_display}'
                if comment:
                    desc += f' | Komentarz: {comment}'
                
                _log_action(document, request.user, 'status_changed', desc)
                messages.success(request, f'Status zmieniony na: {new_status_display}')
            else:
                messages.error(request, 'Niedozwolona zmiana statusu.')
        else:
            messages.error(request, 'Nieprawidłowe dane formularza.')
    
    return redirect('documents:detail', pk=pk)


# === DOSTĘP ===

@login_required
def document_grant_access(request, pk):
    """Nadawanie dostępu do dokumentu przez grupę uprawnień"""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = DocumentAccessForm(request.POST)
        if form.is_valid():
            access = form.save(commit=False)
            access.document = document
            access.granted_by = request.user
            
            # Sprawdź czy dostęp dla tej grupy już istnieje
            existing = DocumentAccess.objects.filter(
                document=document, permission_group=access.permission_group
            ).first()
            
            if existing:
                existing.access_level = access.access_level
                existing.granted_by = request.user
                existing.save()
                messages.info(request, f'Zaktualizowano dostęp dla grupy "{access.permission_group.name}".')
                desc = f'Zaktualizowano dostęp dla grupy "{access.permission_group.name}" na {access.get_access_level_display()}'
            else:
                access.save()
                messages.success(request, f'Nadano dostęp grupie "{access.permission_group.name}".')
                desc = f'Nadano dostęp {access.get_access_level_display()} grupie "{access.permission_group.name}"'
            
            _log_action(document, request.user, 'access_granted', desc)
            return redirect('documents:detail', pk=pk)
    else:
        form = DocumentAccessForm()
    
    return render(request, 'documents/document_grant_access.html', {
        'form': form,
        'document': document,
    })


@login_required
def document_revoke_access(request, pk, access_pk):
    """Cofanie dostępu do dokumentu"""
    document = get_object_or_404(Document, pk=pk)
    access = get_object_or_404(DocumentAccess, pk=access_pk, document=document)
    
    if request.method == 'POST':
        group_name = access.permission_group.name
        access.delete()
        _log_action(document, request.user, 'access_revoked',
                    f'Cofnięto dostęp grupie "{group_name}"')
        messages.success(request, f'Cofnięto dostęp grupie "{group_name}".')
        return redirect('documents:detail', pk=pk)
    
    return render(request, 'documents/document_revoke_access.html', {
        'document': document,
        'access': access,
    })


# === ZAPOZNANIE ===

@login_required
def document_acknowledge(request, pk):
    """Potwierdzenie zapoznania się z dokumentem"""
    document = get_object_or_404(Document, pk=pk)
    current_version = document.get_current_version()
    
    if request.method == 'POST':
        if not current_version:
            messages.error(request, 'Brak obowiązującej wersji dokumentu.')
            return redirect('documents:detail', pk=pk)
        
        ack, created = DocumentAcknowledgement.objects.get_or_create(
            document=document,
            user=request.user,
            version=current_version,
            defaults={'notes': request.POST.get('notes', '')}
        )
        
        if created:
            _log_action(document, request.user, 'acknowledged',
                       f'{request.user.username} potwierdził zapoznanie się z wersją {current_version.version_number}')
            messages.success(request, 'Potwierdzono zapoznanie się z dokumentem.')
        else:
            messages.info(request, 'Już wcześniej potwierdzono zapoznanie z tą wersją.')
    
    return redirect('documents:detail', pk=pk)


# === UDOSTĘPNIONE DLA MNIE ===

class SharedWithMeListView(LoginRequiredMixin, ListView):
    model = DocumentAccess
    template_name = "documents/shared_with_me.html"
    context_object_name = "access_list"
    
    def _get_user_permission_groups(self):
        """Zwraca wszystkie grupy uprawnień użytkownika (bezpośrednie, stanowisko, dział)"""
        from core.models import PermissionGroup
        user = self.request.user
        group_ids = set()
        
        # Przez Employee
        try:
            employee = user.employee
            # Bezpośrednio przypisane grupy
            group_ids.update(
                employee.permission_group_assignments.values_list('permission_group_id', flat=True)
            )
            # Przez stanowiska
            for position in employee.positions.all():
                group_ids.update(
                    position.permission_assignments.values_list('permission_group_id', flat=True)
                )
            # Przez dział
            if employee.department:
                group_ids.update(
                    employee.department.permission_assignments.values_list('permission_group_id', flat=True)
                )
        except Exception:
            pass
        
        return group_ids
    
    def get_queryset(self):
        group_ids = self._get_user_permission_groups()
        return DocumentAccess.objects.filter(
            permission_group_id__in=group_ids
        ).select_related(
            'document', 'document__owner', 'permission_group', 'granted_by'
        ).order_by('-granted_at')


# === POWIĄZANIA ISO ===

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
                _log_action(document, request.user, 'iso_linked',
                           f'Powiązano z wymaganiem {mapping.iso_requirement.iso_id}')
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
        _log_action(document, request.user, 'iso_unlinked',
                   f'Usunięto powiązanie z wymaganiem {iso_id}')
        messages.success(request, f'Usunięto powiązanie z wymaganiem {iso_id}.')
        return redirect('documents:detail', pk=pk)
    
    return render(request, 'documents/document_remove_iso_mapping.html', {
        'document': document,
        'mapping': mapping,
    })
