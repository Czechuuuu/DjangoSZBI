from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from functools import wraps

from .models import ISORequirement
from .forms import ISORequirementForm
from core.models import ActivityLog


def has_dictionary_permission(user):
    """
    Sprawdza czy użytkownik ma uprawnienia do modułu słownika ISO.
    Admin/superuser zawsze ma dostęp.
    Pracownik musi mieć uprawnienie z kategorii 'dictionary'.
    """
    if user.is_superuser or user.is_staff:
        return True
    
    # Sprawdź czy użytkownik ma przypisanego pracownika
    if hasattr(user, 'employee'):
        employee = user.employee
        permissions = employee.get_permissions()
        # Sprawdź czy którekolwiek uprawnienie jest z kategorii 'dictionary'
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


def log_activity(request, action, iso_req, description):
    """Pomocnicza funkcja do logowania aktywności"""
    ActivityLog.log(
        user=request.user,
        action=action,
        category='system',  # Można później dodać kategorię 'dictionary'
        object_type='ISORequirement',
        object_id=iso_req.pk if iso_req.pk else None,
        object_repr=str(iso_req),
        description=description,
        request=request
    )


@login_required
@dictionary_permission_required
def iso_requirement_list(request):
    """Lista wymagań ISO z filtrowaniem i paginacją"""
    requirements = ISORequirement.objects.all()
    
    # Filtrowanie
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    
    if search:
        requirements = requirements.filter(
            Q(iso_id__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(implementation_method__icontains=search)
        )
    
    if status_filter:
        requirements = requirements.filter(is_applied=status_filter)
    
    if category_filter:
        requirements = requirements.filter(category__icontains=category_filter)
    
    # Pobierz unikalne kategorie do filtra
    categories = ISORequirement.objects.values_list('category', flat=True).distinct().order_by('category')
    categories = [c for c in categories if c]  # Usuń puste
    
    # Paginacja
    paginator = Paginator(requirements, 20)
    page = request.GET.get('page')
    requirements = paginator.get_page(page)
    
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
        'category_filter': category_filter,
        'categories': categories,
        'stats': stats,
        'status_choices': ISORequirement.STATUS_CHOICES,
    })


@login_required
@dictionary_permission_required
def iso_requirement_create(request):
    """Tworzenie nowego wymagania ISO"""
    if request.method == 'POST':
        form = ISORequirementForm(request.POST)
        if form.is_valid():
            iso_req = form.save(commit=False)
            iso_req.created_by = request.user
            iso_req.save()
            log_activity(request, 'create', iso_req, 
                        f'Utworzono wymaganie ISO "{iso_req.iso_id}"')
            messages.success(request, f'Wymaganie ISO "{iso_req.iso_id}" zostało utworzone.')
            return redirect('dictionary:iso_requirement_list')
    else:
        form = ISORequirementForm()
    
    return render(request, 'dictionary/iso_requirement_form.html', {
        'form': form,
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
            return redirect('dictionary:iso_requirement_list')
    else:
        form = ISORequirementForm(instance=iso_req)
    
    return render(request, 'dictionary/iso_requirement_form.html', {
        'form': form,
        'iso_req': iso_req,
        'title': f'Edytuj wymaganie ISO: {iso_req.iso_id}',
        'is_edit': True,
    })


@login_required
@dictionary_permission_required
def iso_requirement_delete(request, pk):
    """Usuwanie wymagania ISO"""
    iso_req = get_object_or_404(ISORequirement, pk=pk)
    
    if request.method == 'POST':
        iso_id = iso_req.iso_id
        log_activity(request, 'delete', iso_req, 
                    f'Usunięto wymaganie ISO "{iso_id}"')
        iso_req.delete()
        messages.success(request, f'Wymaganie ISO "{iso_id}" zostało usunięte.')
        return redirect('dictionary:iso_requirement_list')
    
    return render(request, 'dictionary/iso_requirement_confirm_delete.html', {
        'iso_req': iso_req,
    })


@login_required
@dictionary_permission_required
def iso_requirement_detail(request, pk):
    """Szczegóły wymagania ISO wraz z powiązanymi dokumentami"""
    iso_req = get_object_or_404(ISORequirement, pk=pk)
    
    # Pobierz powiązane dokumenty
    document_mappings = iso_req.document_mappings.select_related('document', 'created_by').all()
    
    return render(request, 'dictionary/iso_requirement_detail.html', {
        'iso_req': iso_req,
        'document_mappings': document_mappings,
    })


@login_required
@dictionary_permission_required
def compliance_matrix(request):
    """Macierz zgodności - pełna mapa dokumenty ↔ wymagania ISO"""
    from documents.models import Document, DocumentISOMapping
    
    # Pobierz wszystkie wymagania i dokumenty
    requirements = ISORequirement.objects.all().order_by('iso_id')
    documents = Document.objects.filter(status='published').order_by('title')
    
    # Pobierz wszystkie mapowania i utwórz macierz
    mappings = DocumentISOMapping.objects.select_related('document', 'iso_requirement').all()
    
    # Utwórz słownik mapowań: (doc_id, req_id) -> mapping_type
    mapping_dict = {}
    for m in mappings:
        mapping_dict[(m.document_id, m.iso_requirement_id)] = m.mapping_type
    
    # Przygotuj dane dla szablonu - lista wymagań z informacjami o dokumentach
    matrix_data = []
    for req in requirements:
        row = {
            'requirement': req,
            'documents': []
        }
        for doc in documents:
            key = (doc.pk, req.pk)
            mapping_type = mapping_dict.get(key, None)
            row['documents'].append({
                'document': doc,
                'mapping_type': mapping_type,
            })
        matrix_data.append(row)
    
    # Statystyki
    covered_req_ids = set(m.iso_requirement_id for m in mappings)
    stats = {
        'total_requirements': requirements.count(),
        'covered_requirements': len(covered_req_ids),
        'total_documents': documents.count(),
        'total_mappings': mappings.count(),
    }
    stats['uncovered_requirements'] = stats['total_requirements'] - stats['covered_requirements']
    stats['coverage_percent'] = round(
        (stats['covered_requirements'] / stats['total_requirements'] * 100) 
        if stats['total_requirements'] > 0 else 0, 1
    )
    
    # Określ kolor paska postępu
    if stats['coverage_percent'] >= 80:
        stats['progress_color'] = '#28a745'
    elif stats['coverage_percent'] >= 50:
        stats['progress_color'] = '#ffc107'
    else:
        stats['progress_color'] = '#dc3545'
    
    return render(request, 'dictionary/compliance_matrix.html', {
        'matrix_data': matrix_data,
        'documents': documents,
        'stats': stats,
    })

