from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse

from .models import SoADeclaration, SoAEntry, SoALog
from .forms import SoADeclarationForm, SoAEntryForm, SoAStatusForm
from dictionary.models import ISODomain, ISOObjective, ISORequirement
from core.mixins import (
    SZBIPermissionRequiredMixin, szbi_permission_required,
    PERM_COMPLIANCE_ADMIN, PERM_COMPLIANCE_OWNER, PERM_COMPLIANCE_MANAGER, PERM_COMPLIANCE_APPROVER
)

# Uprawnienia do przeglądania deklaracji
SOA_VIEW_PERMISSIONS = [PERM_COMPLIANCE_ADMIN, PERM_COMPLIANCE_OWNER, PERM_COMPLIANCE_MANAGER, PERM_COMPLIANCE_APPROVER]
# Uprawnienia do edycji deklaracji
SOA_EDIT_PERMISSIONS = [PERM_COMPLIANCE_ADMIN, PERM_COMPLIANCE_OWNER, PERM_COMPLIANCE_MANAGER]


def _log_action(declaration, user, action, description=""):
    """Helper do logowania akcji na deklaracji"""
    SoALog.objects.create(
        declaration=declaration,
        user=user,
        action=action,
        description=description
    )


# ============== DEKLARACJE ==============

class SoADeclarationListView(SZBIPermissionRequiredMixin, ListView):
    model = SoADeclaration
    template_name = "soa/declaration_list.html"
    context_object_name = "declarations"
    szbi_permission_required = SOA_VIEW_PERMISSIONS
    
    def get_queryset(self):
        qs = SoADeclaration.objects.select_related('owner', 'created_by').annotate(
            entries_count=Count('entries')
        ).all()
        
        # Filtrowanie
        status = self.request.GET.get('status')
        search = self.request.GET.get('q')
        
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(designation__icontains=search) |
                Q(description__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = SoADeclaration.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('q', '')
        return context


class SoADeclarationCreateView(SZBIPermissionRequiredMixin, CreateView):
    model = SoADeclaration
    form_class = SoADeclarationForm
    template_name = "soa/declaration_form.html"
    szbi_permission_required = [PERM_COMPLIANCE_ADMIN, PERM_COMPLIANCE_OWNER]
    
    def get_success_url(self):
        return reverse('soa:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        _log_action(self.object, self.request.user, 'created',
                    f'Utworzono deklarację [{self.object.designation}] {self.object.name}')
        messages.success(self.request, f'Deklaracja "{self.object.designation}" została utworzona.')
        return response


class SoADeclarationDetailView(SZBIPermissionRequiredMixin, DetailView):
    model = SoADeclaration
    template_name = "soa/declaration_detail.html"
    context_object_name = "declaration"
    szbi_permission_required = SOA_VIEW_PERMISSIONS
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = self.object.entries.select_related(
            'requirement', 'requirement__objective', 'requirement__objective__domain',
            'responsible_person'
        ).prefetch_related('related_documents').all()
        context['logs'] = self.object.logs.select_related('user').all()[:20]
        context['status_form'] = SoAStatusForm(initial={'new_status': self.object.status})
        
        # Grupowanie wpisów po domenach
        domains = {}
        for entry in context['entries']:
            domain = entry.requirement.objective.domain if entry.requirement.objective else None
            domain_key = domain.code if domain else 'Inne'
            if domain_key not in domains:
                domains[domain_key] = {
                    'domain': domain,
                    'entries': []
                }
            domains[domain_key]['entries'].append(entry)
        context['entries_by_domain'] = dict(sorted(domains.items()))
        
        return context


class SoADeclarationUpdateView(SZBIPermissionRequiredMixin, UpdateView):
    model = SoADeclaration
    form_class = SoADeclarationForm
    template_name = "soa/declaration_form.html"
    szbi_permission_required = SOA_EDIT_PERMISSIONS

    def get_success_url(self):
        return reverse('soa:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        _log_action(self.object, self.request.user, 'updated',
                    f'Zaktualizowano deklarację [{self.object.designation}]')
        messages.success(self.request, f'Deklaracja "{self.object.designation}" została zaktualizowana.')
        return response


class SoADeclarationDeleteView(SZBIPermissionRequiredMixin, DeleteView):
    model = SoADeclaration
    template_name = "soa/declaration_confirm_delete.html"
    success_url = reverse_lazy('soa:list')
    szbi_permission_required = [PERM_COMPLIANCE_ADMIN]

    def form_valid(self, form):
        designation = self.object.designation
        response = super().form_valid(form)
        messages.success(self.request, f'Deklaracja "{designation}" została usunięta.')
        return response


@szbi_permission_required(SOA_EDIT_PERMISSIONS)
def soa_change_status(request, pk):
    """Zmiana statusu deklaracji"""
    declaration = get_object_or_404(SoADeclaration, pk=pk)
    
    if request.method == 'POST':
        form = SoAStatusForm(request.POST)
        if form.is_valid():
            old_status = declaration.get_status_display()
            declaration.status = form.cleaned_data['new_status']
            declaration.save()
            new_status = declaration.get_status_display()
            
            _log_action(declaration, request.user, 'status_changed',
                        f'Zmieniono status z "{old_status}" na "{new_status}"')
            messages.success(request, f'Status zmieniony na "{new_status}".')
    
    return redirect('soa:detail', pk=pk)


# ============== POZYCJE DEKLARACJI ==============

@szbi_permission_required(SOA_EDIT_PERMISSIONS)
def soa_entry_add(request, pk):
    """Dodawanie nowej pozycji do deklaracji"""
    declaration = get_object_or_404(SoADeclaration, pk=pk)
    
    if request.method == 'POST':
        form = SoAEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.declaration = declaration
            entry.save()
            form.save_m2m()  # Zapisz relacje ManyToMany
            
            _log_action(declaration, request.user, 'entry_added',
                        f'Dodano pozycję: {entry.requirement.iso_id}')
            messages.success(request, f'Dodano pozycję {entry.requirement.iso_id}.')
            return redirect('soa:detail', pk=pk)
    else:
        form = SoAEntryForm()
    
    return render(request, 'soa/entry_form.html', {
        'form': form,
        'declaration': declaration,
        'domains': ISODomain.objects.all(),
    })


@szbi_permission_required(SOA_EDIT_PERMISSIONS)
def soa_entry_edit(request, pk, entry_pk):
    """Edycja pozycji w deklaracji"""
    declaration = get_object_or_404(SoADeclaration, pk=pk)
    entry = get_object_or_404(SoAEntry, pk=entry_pk, declaration=declaration)
    
    if request.method == 'POST':
        form = SoAEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            
            _log_action(declaration, request.user, 'entry_updated',
                        f'Zaktualizowano pozycję: {entry.requirement.iso_id}')
            messages.success(request, f'Pozycja {entry.requirement.iso_id} została zaktualizowana.')
            return redirect('soa:detail', pk=pk)
    else:
        form = SoAEntryForm(instance=entry)
    
    return render(request, 'soa/entry_form.html', {
        'form': form,
        'declaration': declaration,
        'entry': entry,
        'domains': ISODomain.objects.all(),
    })


@szbi_permission_required(SOA_EDIT_PERMISSIONS)
def soa_entry_delete(request, pk, entry_pk):
    """Usuwanie pozycji z deklaracji"""
    declaration = get_object_or_404(SoADeclaration, pk=pk)
    entry = get_object_or_404(SoAEntry, pk=entry_pk, declaration=declaration)
    
    if request.method == 'POST':
        iso_id = entry.requirement.iso_id
        entry.delete()
        
        _log_action(declaration, request.user, 'entry_removed',
                    f'Usunięto pozycję: {iso_id}')
        messages.success(request, f'Pozycja {iso_id} została usunięta.')
        return redirect('soa:detail', pk=pk)
    
    return render(request, 'soa/entry_confirm_delete.html', {
        'declaration': declaration,
        'entry': entry,
    })


# ============== API ENDPOINTS ==============

@szbi_permission_required(SOA_VIEW_PERMISSIONS)
def api_objectives_by_domain(request, domain_id):
    """API: Zwraca cele dla wybranej domeny"""
    objectives = ISOObjective.objects.filter(domain_id=domain_id).values('id', 'code', 'name')
    return JsonResponse(list(objectives), safe=False)


@szbi_permission_required(SOA_VIEW_PERMISSIONS)
def api_requirements_by_objective(request, objective_id):
    """API: Zwraca wymagania dla wybranego celu"""
    requirements = ISORequirement.objects.filter(objective_id=objective_id).values('id', 'iso_id', 'name')
    return JsonResponse(list(requirements), safe=False)
