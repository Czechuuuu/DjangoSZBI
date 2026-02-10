from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import FileResponse
from functools import wraps

from .models import ISODomain, ISOObjective, ISORequirement, ISOAttachment
from .forms import ISODomainForm, ISOObjectiveForm, ISORequirementForm, ISOAttachmentForm
from core.models import ActivityLog


def has_dictionary_permission(user):
    """
    Sprawdza czy użytkownik ma uprawnienia do modułu słownika ISO.
    Admin/superuser zawsze ma dostęp.
    Pracownik musi mieć uprawnienie z kategorii 'dictionary'.
    """
    if user.is_superuser or user.is_staff:
        return True
    
    if hasattr(user, 'employee'):
        employee = user.employee
        permissions = employee.get_permissions()
        for perm in permissions:
            if perm.category == 'dictionary':
                return True
    
    return False


def dictionary_permission_required(view_func):
    """Dekorator wymagający uprawnień do słownika ISO"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not has_dictionary_permission(request.user):
            messages.error(request, 'Nie masz uprawnień do modułu Słownik ISO.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def log_activity(request, action, obj, description):
    """Pomocnicza funkcja do logowania aktywności"""
    ActivityLog.log(
        user=request.user,
        action=action,
        category='system',
        object_type=obj.__class__.__name__,
        object_id=obj.pk if obj.pk else None,
        object_repr=str(obj),
        description=description,
        request=request
    )


# =============================================================================
# DRZEWO ISO - widok główny
# =============================================================================

@login_required
@dictionary_permission_required
def iso_tree(request):
    """Widok drzewa ISO: domeny → cele → wymagania"""
    domains = ISODomain.objects.prefetch_related(
        'objectives__requirements'
    ).all()
    
    # Statystyki
    stats = {
        'domains': ISODomain.objects.count(),
        'objectives': ISOObjective.objects.count(),
        'total': ISORequirement.objects.count(),
        'applied': ISORequirement.objects.filter(is_applied='yes').count(),
        'not_applied': ISORequirement.objects.filter(is_applied='no').count(),
        'partial': ISORequirement.objects.filter(is_applied='partial').count(),
        'not_applicable': ISORequirement.objects.filter(is_applied='not_applicable').count(),
    }
    
    # Wymagania bez przypisanego celu
    orphan_requirements = ISORequirement.objects.filter(objective__isnull=True)
    
    return render(request, 'dictionary/iso_tree.html', {
        'domains': domains,
        'stats': stats,
        'orphan_requirements': orphan_requirements,
    })


# =============================================================================
# DOMENY ISO
# =============================================================================

@login_required
@dictionary_permission_required
def domain_create(request):
    """Tworzenie domeny ISO"""
    if request.method == 'POST':
        form = ISODomainForm(request.POST)
        if form.is_valid():
            domain = form.save()
            log_activity(request, 'create', domain, f'Utworzono domenę ISO "{domain}"')
            messages.success(request, f'Domena "{domain}" została utworzona.')
            return redirect('dictionary:iso_tree')
    else:
        form = ISODomainForm()
    
    return render(request, 'dictionary/domain_form.html', {
        'form': form,
        'title': 'Dodaj domenę ISO',
    })


@login_required
@dictionary_permission_required
def domain_update(request, pk):
    """Edycja domeny ISO"""
    domain = get_object_or_404(ISODomain, pk=pk)
    if request.method == 'POST':
        form = ISODomainForm(request.POST, instance=domain)
        if form.is_valid():
            domain = form.save()
            log_activity(request, 'update', domain, f'Zaktualizowano domenę ISO "{domain}"')
            messages.success(request, f'Domena "{domain}" została zaktualizowana.')
            return redirect('dictionary:iso_tree')
    else:
        form = ISODomainForm(instance=domain)
    
    return render(request, 'dictionary/domain_form.html', {
        'form': form,
        'title': f'Edytuj domenę: {domain}',
        'domain': domain,
    })


@login_required
@dictionary_permission_required
def domain_delete(request, pk):
    """Usuwanie domeny ISO"""
    domain = get_object_or_404(ISODomain, pk=pk)
    from core.views import get_related_objects, has_blocking_relations
    related = get_related_objects(domain)
    blocked = has_blocking_relations(related)
    
    if request.method == 'POST' and not blocked:
        name = str(domain)
        domain_id = domain.pk
        try:
            domain.delete()
            ActivityLog.log(
                user=request.user, action='delete', category='system',
                object_type='ISODomain', object_id=domain_id, object_repr=name,
                description=f'Usunięto domenę ISO "{name}"', request=request
            )
            messages.success(request, f'Domena "{name}" została usunięta.')
        except Exception as e:
            messages.error(request, f'Nie można usunąć domeny: {e}')
        return redirect('dictionary:iso_tree')
    
    return render(request, 'dictionary/domain_confirm_delete.html', {
        'domain': domain,
        'related': related,
        'blocked': blocked,
    })


# =============================================================================
# CELE WYMAGAŃ ISO
# =============================================================================

@login_required
@dictionary_permission_required
def objective_create(request, domain_pk=None):
    """Tworzenie celu wymagań"""
    initial = {}
    if domain_pk:
        initial['domain'] = get_object_or_404(ISODomain, pk=domain_pk)
    
    if request.method == 'POST':
        form = ISOObjectiveForm(request.POST)
        if form.is_valid():
            objective = form.save()
            log_activity(request, 'create', objective, f'Utworzono cel wymagań "{objective}"')
            messages.success(request, f'Cel "{objective}" został utworzony.')
            return redirect('dictionary:iso_tree')
    else:
        form = ISOObjectiveForm(initial=initial)
    
    return render(request, 'dictionary/objective_form.html', {
        'form': form,
        'title': 'Dodaj cel wymagań',
    })


@login_required
@dictionary_permission_required
def objective_update(request, pk):
    """Edycja celu wymagań"""
    objective = get_object_or_404(ISOObjective, pk=pk)
    if request.method == 'POST':
        form = ISOObjectiveForm(request.POST, instance=objective)
        if form.is_valid():
            objective = form.save()
            log_activity(request, 'update', objective, f'Zaktualizowano cel "{objective}"')
            messages.success(request, f'Cel "{objective}" został zaktualizowany.')
            return redirect('dictionary:iso_tree')
    else:
        form = ISOObjectiveForm(instance=objective)
    
    return render(request, 'dictionary/objective_form.html', {
        'form': form,
        'title': f'Edytuj cel: {objective}',
        'objective': objective,
    })


@login_required
@dictionary_permission_required
def objective_delete(request, pk):
    """Usuwanie celu wymagań"""
    objective = get_object_or_404(ISOObjective, pk=pk)
    from core.views import get_related_objects, has_blocking_relations
    related = get_related_objects(objective)
    blocked = has_blocking_relations(related)
    
    if request.method == 'POST' and not blocked:
        name = str(objective)
        obj_id = objective.pk
        try:
            objective.delete()
            ActivityLog.log(
                user=request.user, action='delete', category='system',
                object_type='ISOObjective', object_id=obj_id, object_repr=name,
                description=f'Usunięto cel wymagań "{name}"', request=request
            )
            messages.success(request, f'Cel "{name}" został usunięty.')
        except Exception as e:
            messages.error(request, f'Nie można usunąć celu: {e}')
        return redirect('dictionary:iso_tree')
    
    return render(request, 'dictionary/objective_confirm_delete.html', {
        'objective': objective,
        'related': related,
        'blocked': blocked,
    })


# =============================================================================
# WYMAGANIA ISO
# =============================================================================

@login_required
@dictionary_permission_required
def iso_requirement_list(request):
    """Lista wymagań ISO z filtrowaniem i paginacją"""
    requirements = ISORequirement.objects.select_related('objective__domain').all()
    
    # Filtrowanie
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    domain_filter = request.GET.get('domain', '')
    
    if search:
        requirements = requirements.filter(
            Q(iso_id__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(implementation_method__icontains=search)
        )
    
    if status_filter:
        requirements = requirements.filter(is_applied=status_filter)
    
    if domain_filter:
        requirements = requirements.filter(objective__domain_id=domain_filter)
    
    # Paginacja
    paginator = Paginator(requirements, 25)
    page = request.GET.get('page')
    requirements = paginator.get_page(page)
    
    domains = ISODomain.objects.all()
    
    # Statystyki
    stats = {
        'total': ISORequirement.objects.count(),
        'applied': ISORequirement.objects.filter(is_applied='yes').count(),
        'not_applied': ISORequirement.objects.filter(is_applied='no').count(),
        'partial': ISORequirement.objects.filter(is_applied='partial').count(),
        'not_applicable': ISORequirement.objects.filter(is_applied='not_applicable').count(),
    }
    
    return render(request, 'dictionary/iso_requirement_list.html', {
        'requirements': requirements,
        'search': search,
        'status_filter': status_filter,
        'domain_filter': domain_filter,
        'domains': domains,
        'stats': stats,
        'status_choices': ISORequirement.STATUS_CHOICES,
    })


@login_required
@dictionary_permission_required
def iso_requirement_create(request, objective_pk=None):
    """Tworzenie nowego wymagania ISO"""
    initial = {}
    if objective_pk:
        initial['objective'] = get_object_or_404(ISOObjective, pk=objective_pk)
    
    if request.method == 'POST':
        form = ISORequirementForm(request.POST)
        attachment_form = ISOAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            iso_req = form.save(commit=False)
            iso_req.created_by = request.user
            iso_req.save()
            
            # Obsługa opcjonalnego załącznika
            if request.FILES.get('file'):
                if attachment_form.is_valid():
                    attachment = attachment_form.save(commit=False)
                    attachment.requirement = iso_req
                    attachment.uploaded_by = request.user
                    attachment.save()
                    log_activity(request, 'create', attachment,
                                f'Dodano załącznik "{attachment.title}" do {iso_req.iso_id}')
            
            log_activity(request, 'create', iso_req, 
                        f'Utworzono wymaganie ISO "{iso_req.iso_id}"')
            messages.success(request, f'Wymaganie ISO "{iso_req.iso_id}" zostało utworzone.')
            return redirect('dictionary:iso_requirement_detail', pk=iso_req.pk)
    else:
        form = ISORequirementForm(initial=initial)
        attachment_form = ISOAttachmentForm()
    
    return render(request, 'dictionary/iso_requirement_form.html', {
        'form': form,
        'attachment_form': attachment_form,
        'title': 'Dodaj wymaganie ISO',
        'is_edit': False,
    })


@login_required
@dictionary_permission_required
def iso_requirement_update(request, pk):
    """Edycja wymagania ISO"""
    iso_req = get_object_or_404(ISORequirement, pk=pk)
    
    if request.method == 'POST':
        form = ISORequirementForm(request.POST, instance=iso_req)
        if form.is_valid():
            iso_req = form.save(commit=False)
            iso_req.updated_by = request.user
            iso_req.save()
            log_activity(request, 'update', iso_req, 
                        f'Zaktualizowano wymaganie ISO "{iso_req.iso_id}"')
            messages.success(request, f'Wymaganie ISO "{iso_req.iso_id}" zostało zaktualizowane.')
            return redirect('dictionary:iso_requirement_detail', pk=iso_req.pk)
    else:
        form = ISORequirementForm(instance=iso_req)
    
    return render(request, 'dictionary/iso_requirement_form.html', {
        'form': form,
        'iso_req': iso_req,
        'title': f'Edytuj wymaganie: {iso_req.iso_id}',
        'is_edit': True,
    })


@login_required
@dictionary_permission_required
def iso_requirement_delete(request, pk):
    """Usuwanie wymagania ISO"""
    iso_req = get_object_or_404(ISORequirement, pk=pk)
    from core.views import get_related_objects, has_blocking_relations
    related = get_related_objects(iso_req)
    blocked = has_blocking_relations(related)
    
    if request.method == 'POST' and not blocked:
        iso_id = iso_req.iso_id
        req_id = iso_req.pk
        try:
            iso_req.delete()
            ActivityLog.log(
                user=request.user, action='delete', category='system',
                object_type='ISORequirement', object_id=req_id, object_repr=iso_id,
                description=f'Usunięto wymaganie ISO "{iso_id}"', request=request
            )
            messages.success(request, f'Wymaganie ISO "{iso_id}" zostało usunięte.')
        except Exception as e:
            messages.error(request, f'Nie można usunąć wymagania: {e}')
        return redirect('dictionary:iso_tree')
    
    return render(request, 'dictionary/iso_requirement_confirm_delete.html', {
        'iso_req': iso_req,
        'related': related,
        'blocked': blocked,
    })


@login_required
@dictionary_permission_required
def iso_requirement_detail(request, pk):
    """Szczegóły wymagania ISO wraz z powiązanymi dokumentami i załącznikami"""
    iso_req = get_object_or_404(
        ISORequirement.objects.select_related('objective__domain'),
        pk=pk
    )
    
    # Powiązane dokumenty
    document_mappings = iso_req.document_mappings.select_related('document', 'created_by').all()
    
    # Załączniki
    attachments = iso_req.attachments.all()
    
    # Formularz dodawania załącznika
    attachment_form = ISOAttachmentForm()
    
    return render(request, 'dictionary/iso_requirement_detail.html', {
        'iso_req': iso_req,
        'document_mappings': document_mappings,
        'attachments': attachments,
        'attachment_form': attachment_form,
    })


# =============================================================================
# ZAŁĄCZNIKI
# =============================================================================

@login_required
@dictionary_permission_required
def attachment_add(request, requirement_pk):
    """Dodawanie pliku do wymagania ISO"""
    iso_req = get_object_or_404(ISORequirement, pk=requirement_pk)
    
    if request.method == 'POST':
        form = ISOAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.requirement = iso_req
            attachment.uploaded_by = request.user
            attachment.save()
            log_activity(request, 'create', attachment,
                        f'Dodano załącznik "{attachment.title}" do {iso_req.iso_id}')
            messages.success(request, f'Plik "{attachment.title}" został dodany.')
            return redirect('dictionary:iso_requirement_detail', pk=iso_req.pk)
    else:
        form = ISOAttachmentForm()
    
    return render(request, 'dictionary/attachment_form.html', {
        'form': form,
        'iso_req': iso_req,
        'title': f'Dodaj plik do {iso_req.iso_id}',
    })


@login_required
@dictionary_permission_required
def attachment_delete(request, pk):
    """Usuwanie załącznika"""
    attachment = get_object_or_404(ISOAttachment, pk=pk)
    iso_req = attachment.requirement
    
    if request.method == 'POST':
        title = attachment.title
        attachment.file.delete(save=False)  # Usuń plik z dysku
        attachment.delete()
        log_activity(request, 'delete', iso_req,
                    f'Usunięto załącznik "{title}" z {iso_req.iso_id}')
        messages.success(request, f'Plik "{title}" został usunięty.')
        return redirect('dictionary:iso_requirement_detail', pk=iso_req.pk)
    
    return render(request, 'dictionary/attachment_confirm_delete.html', {
        'attachment': attachment,
        'iso_req': iso_req,
    })


@login_required
@dictionary_permission_required
def attachment_download(request, pk):
    """Pobieranie załącznika"""
    attachment = get_object_or_404(ISOAttachment, pk=pk)
    return FileResponse(
        attachment.file.open('rb'),
        as_attachment=True,
        filename=attachment.get_filename()
    )


