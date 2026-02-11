from django.views.generic import ListView, CreateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import Incident, IncidentNote, IncidentLog
from .forms import (
    IncidentReportForm, IncidentAnalysisForm, IncidentResponseForm,
    IncidentActionForm, IncidentCloseForm, IncidentNoteForm
)
from core.mixins import (
    SZBIPermissionRequiredMixin, szbi_permission_required,
    PERM_INCIDENTS_VIEW_ALL, PERM_INCIDENTS_VIEW_OWN,
    PERM_INCIDENTS_ADMIN, PERM_INCIDENTS_MANAGE
)

# Uprawnienia do przeglądania wszystkich incydentów
INCIDENTS_VIEW_ALL_PERMISSIONS = [PERM_INCIDENTS_ADMIN, PERM_INCIDENTS_VIEW_ALL, PERM_INCIDENTS_MANAGE]
# Uprawnienia do zarządzania incydentami
INCIDENTS_MANAGE_PERMISSIONS = [PERM_INCIDENTS_ADMIN, PERM_INCIDENTS_MANAGE]


def _log_action(incident, user, action, description=""):
    """Helper do logowania akcji na incydencie"""
    IncidentLog.objects.create(
        incident=incident,
        user=user,
        action=action,
        description=description
    )


class IncidentDeleteView(SZBIPermissionRequiredMixin, DeleteView):
    """Usuwanie incydentu"""
    model = Incident
    template_name = "incidents/incident_confirm_delete.html"
    success_url = reverse_lazy('incidents:list')
    szbi_permission_required = [PERM_INCIDENTS_ADMIN]

    def form_valid(self, form):
        incident_title = self.object.title
        response = super().form_valid(form)
        messages.success(self.request, f'Incydent "{incident_title}" został usunięty.')
        return response


# ============== LISTA INCYDENTÓW ==============

class MyIncidentsListView(SZBIPermissionRequiredMixin, ListView):
    """Lista moich zgłoszeń"""
    model = Incident
    template_name = "incidents/my_incidents.html"
    context_object_name = "incidents"
    szbi_permission_required = [PERM_INCIDENTS_VIEW_OWN, PERM_INCIDENTS_VIEW_ALL, PERM_INCIDENTS_ADMIN, PERM_INCIDENTS_MANAGE]
    
    def get_queryset(self):
        return Incident.objects.filter(reporter=self.request.user).order_by('-created_at')


class AllIncidentsListView(SZBIPermissionRequiredMixin, ListView):
    """Lista wszystkich incydentów (dla administratorów)"""
    model = Incident
    template_name = "incidents/incident_list.html"
    context_object_name = "incidents"
    szbi_permission_required = INCIDENTS_VIEW_ALL_PERMISSIONS
    
    def get_queryset(self):
        qs = Incident.objects.select_related('reporter', 'assigned_to').all()
        
        # Filtrowanie
        status = self.request.GET.get('status')
        severity = self.request.GET.get('severity')
        category = self.request.GET.get('category')
        search = self.request.GET.get('q')
        
        if status:
            qs = qs.filter(status=status)
        if severity:
            qs = qs.filter(severity=severity)
        if category:
            qs = qs.filter(category=category)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Incident.STATUS_CHOICES
        context['severity_choices'] = Incident.SEVERITY_CHOICES
        context['category_choices'] = Incident.CATEGORY_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_severity'] = self.request.GET.get('severity', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_search'] = self.request.GET.get('q', '')
        return context


# ============== ZGŁASZANIE INCYDENTU ==============

class IncidentReportView(SZBIPermissionRequiredMixin, CreateView):
    """Zgłaszanie nowego incydentu"""
    model = Incident
    form_class = IncidentReportForm
    template_name = "incidents/incident_report.html"
    szbi_permission_required = [PERM_INCIDENTS_VIEW_OWN, PERM_INCIDENTS_VIEW_ALL, PERM_INCIDENTS_ADMIN, PERM_INCIDENTS_MANAGE]
    
    def get_success_url(self):
        return reverse('incidents:my_list')

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        response = super().form_valid(form)
        _log_action(self.object, self.request.user, 'created',
                    f'Zgłoszono incydent: {self.object.title}')
        messages.success(self.request, 'Incydent został zgłoszony.')
        return response


# ============== SZCZEGÓŁY INCYDENTU ==============

class IncidentDetailView(SZBIPermissionRequiredMixin, DetailView):
    """Szczegóły incydentu"""
    model = Incident
    template_name = "incidents/incident_detail.html"
    context_object_name = "incident"
    szbi_permission_required = [PERM_INCIDENTS_VIEW_OWN, PERM_INCIDENTS_VIEW_ALL, PERM_INCIDENTS_ADMIN, PERM_INCIDENTS_MANAGE]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notes'] = self.object.notes.select_related('author').all()
        context['logs'] = self.object.logs.select_related('user').all()[:20]
        context['note_form'] = IncidentNoteForm()
        
        # Formularze dla różnych faz
        context['analysis_form'] = IncidentAnalysisForm(instance=self.object)
        context['response_form'] = IncidentResponseForm(instance=self.object)
        context['action_form'] = IncidentActionForm(instance=self.object)
        context['close_form'] = IncidentCloseForm(instance=self.object)
        
        return context


# ============== WORKFLOW - ZMIANA STATUSU ==============

@szbi_permission_required(INCIDENTS_MANAGE_PERMISSIONS)
def incident_advance_status(request, pk):
    """Przejście do następnej fazy workflow"""
    incident = get_object_or_404(Incident, pk=pk)
    next_status = incident.get_next_status()
    
    if next_status:
        old_status = incident.get_status_display()
        incident.status = next_status
        
        if next_status == 'closed':
            incident.closed_at = timezone.now()
        
        incident.save()
        new_status = incident.get_status_display()
        
        _log_action(incident, request.user, 'status_changed',
                    f'Zmieniono status z "{old_status}" na "{new_status}"')
        messages.success(request, f'Status zmieniony na "{new_status}".')
    
    return redirect('incidents:detail', pk=pk)


# ============== AKTUALIZACJA W FAZACH ==============

@szbi_permission_required(INCIDENTS_MANAGE_PERMISSIONS)
def incident_update_analysis(request, pk):
    """Aktualizacja danych analizy"""
    incident = get_object_or_404(Incident, pk=pk)
    
    if request.method == 'POST':
        form = IncidentAnalysisForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            _log_action(incident, request.user, 'updated', 'Zaktualizowano analizę incydentu')
            messages.success(request, 'Analiza została zapisana.')
    
    return redirect('incidents:detail', pk=pk)


@szbi_permission_required(INCIDENTS_MANAGE_PERMISSIONS)
def incident_update_response(request, pk):
    """Aktualizacja danych reakcji"""
    incident = get_object_or_404(Incident, pk=pk)
    
    if request.method == 'POST':
        form = IncidentResponseForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            _log_action(incident, request.user, 'updated', 'Zaktualizowano reakcję na incydent')
            messages.success(request, 'Reakcja została zapisana.')
    
    return redirect('incidents:detail', pk=pk)


@szbi_permission_required(INCIDENTS_MANAGE_PERMISSIONS)
def incident_update_action(request, pk):
    """Aktualizacja działań po incydencie"""
    incident = get_object_or_404(Incident, pk=pk)
    
    if request.method == 'POST':
        form = IncidentActionForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            _log_action(incident, request.user, 'updated', 'Zaktualizowano działania po incydencie')
            messages.success(request, 'Działania zostały zapisane.')
    
    return redirect('incidents:detail', pk=pk)


@szbi_permission_required(INCIDENTS_MANAGE_PERMISSIONS)
def incident_close(request, pk):
    """Zamknięcie incydentu"""
    incident = get_object_or_404(Incident, pk=pk)
    
    if request.method == 'POST':
        form = IncidentCloseForm(request.POST, instance=incident)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.status = 'closed'
            incident.closed_at = timezone.now()
            incident.save()
            
            _log_action(incident, request.user, 'closed', 'Zamknięto incydent')
            messages.success(request, 'Incydent został zamknięty.')
    
    return redirect('incidents:detail', pk=pk)


# ============== NOTATKI ==============

@szbi_permission_required([PERM_INCIDENTS_VIEW_OWN, PERM_INCIDENTS_VIEW_ALL, PERM_INCIDENTS_ADMIN, PERM_INCIDENTS_MANAGE])
def incident_add_note(request, pk):
    """Dodawanie notatki do incydentu"""
    incident = get_object_or_404(Incident, pk=pk)
    
    if request.method == 'POST':
        form = IncidentNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.incident = incident
            note.author = request.user
            note.save()
            
            _log_action(incident, request.user, 'note_added',
                        f'Dodano notatkę: {note.get_note_type_display()}')
            messages.success(request, 'Notatka została dodana.')
    
    return redirect('incidents:detail', pk=pk)
