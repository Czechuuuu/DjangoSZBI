from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import models as db_models

from .models import Organization, Department, Position, Permission, PermissionGroup, PositionPermission, DepartmentPermission, Employee, ActivityLog, EmployeePermissionGroup
from .forms import OrganizationForm, DepartmentForm, PositionForm, PermissionForm, PermissionGroupForm, EmployeeForm


def get_related_objects(obj):
    """
    Zbiera wszystkie powiązane obiekty, które blokują lub zostaną skasowane kaskadowo.
    Zwraca dict: {'protected': [...], 'cascade': [...], 'set_null': [...]}
    """
    result = {'protected': [], 'cascade': [], 'set_null': []}
    
    for related in obj._meta.get_fields():
        # Relacje odwrotne (ForeignKey, OneToOne) - tylko odwrotne, nie forward
        if related.one_to_many or related.one_to_one:
            if not hasattr(related, 'related_model'):
                continue
            # Pomijamy forward relations (np. Employee.user)
            if not hasattr(related, 'get_accessor_name'):
                continue
            accessor = related.get_accessor_name()
            try:
                manager = getattr(obj, accessor)
                if hasattr(manager, 'count'):
                    count = manager.count()
                else:
                    count = 1 if manager is not None else 0
            except Exception:
                continue
            
            if count == 0:
                continue
            
            on_delete = getattr(related, 'on_delete', None)
            model_name = related.related_model._meta.verbose_name_plural
            
            entry = {'model': model_name, 'count': count, 'accessor': accessor}
            
            if on_delete == db_models.PROTECT:
                result['protected'].append(entry)
            elif on_delete == db_models.CASCADE:
                result['cascade'].append(entry)
            elif on_delete == db_models.SET_NULL:
                result['set_null'].append(entry)
        
        # Relacje M2M - tylko odwrotne
        elif related.many_to_many:
            if not hasattr(related, 'get_accessor_name'):
                continue
            accessor = related.get_accessor_name()
            try:
                manager = getattr(obj, accessor)
                count = manager.count()
            except Exception:
                continue
            
            if count > 0:
                model_name = related.related_model._meta.verbose_name_plural
                result['cascade'].append({'model': model_name, 'count': count, 'accessor': accessor, 'm2m': True})
    
    return result


def has_blocking_relations(related_info):
    """Sprawdza czy są relacje PROTECT blokujące usunięcie"""
    return len(related_info['protected']) > 0


def is_admin(user):
    """Sprawdza czy użytkownik jest adminem"""
    return user.is_staff or user.is_superuser


def get_or_create_organization():
    """Pobiera lub tworzy główną organizację"""
    org, created = Organization.objects.get_or_create(
        pk=1,
        defaults={'name': 'Moja Organizacja', 'short_name': 'MO'}
    )
    return org


@login_required
def dashboard(request):
    """Główny dashboard po zalogowaniu"""
    # Pobierz imię pracownika jeśli istnieje
    display_name = request.user.username
    try:
        if hasattr(request.user, 'employee'):
            display_name = request.user.employee.first_name
    except Exception:
        pass
    
    context = {
        'is_admin': is_admin(request.user),
        'display_name': display_name,
    }
    return render(request, 'core/dashboard.html', context)


# ============== ORGANIZACJA (jedna główna) ==============

@login_required
@user_passes_test(is_admin)
def organization_structure(request):
    """Struktura organizacyjna - jedna główna organizacja"""
    organization = get_or_create_organization()
    departments = organization.departments.filter(parent__isnull=True)
    
    return render(request, 'core/organization_structure.html', {
        'organization': organization,
        'departments': departments,
    })


@login_required
@user_passes_test(is_admin)
def organization_edit(request):
    """Edycja głównej organizacji"""
    organization = get_or_create_organization()
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            log_activity(request, 'update', 'organization', organization, 
                        f'Zaktualizowano dane organizacji "{organization.name}"')
            messages.success(request, 'Dane organizacji zostały zaktualizowane.')
            return redirect('core:organization_structure')
    else:
        form = OrganizationForm(instance=organization)
    
    return render(request, 'core/organization_form.html', {
        'form': form,
        'organization': organization,
        'title': 'Edytuj dane organizacji'
    })


# ============== DZIAŁY ==============

@login_required
@user_passes_test(is_admin)
def department_create(request):
    """Tworzenie nowego działu"""
    organization = get_or_create_organization()
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, organization=organization)
        if form.is_valid():
            department = form.save(commit=False)
            department.organization = organization
            department.save()
            log_activity(request, 'create', 'department', department, 
                        f'Utworzono dział "{department.name}"')
            messages.success(request, f'Dział "{department.name}" został utworzony.')
            return redirect('core:organization_structure')
    else:
        form = DepartmentForm(organization=organization)
    
    return render(request, 'core/department_form.html', {
        'form': form,
        'organization': organization,
        'title': 'Dodaj dział'
    })


@login_required
@user_passes_test(is_admin)
def department_update(request, pk):
    """Edycja działu"""
    department = get_object_or_404(Department, pk=pk)
    organization = department.organization
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department, organization=organization)
        if form.is_valid():
            form.save()
            log_activity(request, 'update', 'department', department, 
                        f'Zaktualizowano dział "{department.name}"')
            messages.success(request, f'Dział "{department.name}" został zaktualizowany.')
            return redirect('core:organization_structure')
    else:
        form = DepartmentForm(instance=department, organization=organization)
    
    return render(request, 'core/department_form.html', {
        'form': form,
        'department': department,
        'organization': organization,
        'title': 'Edytuj dział'
    })


@login_required
@user_passes_test(is_admin)
def department_delete(request, pk):
    """Usuwanie działu"""
    department = get_object_or_404(Department, pk=pk)
    organization = department.organization
    related = get_related_objects(department)
    blocked = has_blocking_relations(related)
    
    if request.method == 'POST' and not blocked:
        name = department.name
        dept_id = department.pk
        try:
            department.delete()
            ActivityLog.log(
                user=request.user,
                action='delete',
                category='department',
                object_type='Department',
                object_id=dept_id,
                object_repr=name,
                description=f'Usunięto dział "{name}"',
                request=request
            )
            messages.success(request, f'Dział "{name}" został usunięty.')
            return redirect('core:organization_structure')
        except Exception as e:
            messages.error(request, f'Nie można usunąć działu: {e}')
            return redirect('core:organization_structure')
    
    return render(request, 'core/department_confirm_delete.html', {
        'department': department,
        'organization': organization,
        'related': related,
        'blocked': blocked,
    })


# ============== STANOWISKA ==============

@login_required
@user_passes_test(is_admin)
def position_create_in_dept(request, dept_pk):
    """Tworzenie nowego stanowiska w dziale"""
    department = get_object_or_404(Department, pk=dept_pk)
    organization = department.organization
    
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            position = form.save(commit=False)
            position.organization = organization
            position.department = department
            position.save()
            log_activity(request, 'create', 'position', position, 
                        f'Utworzono stanowisko "{position.name}" w dziale "{department.name}"')
            messages.success(request, f'Stanowisko "{position.name}" zostało utworzone w dziale "{department.name}".')
            return redirect('core:organization_structure')
    else:
        form = PositionForm()
    
    return render(request, 'core/position_form.html', {
        'form': form,
        'organization': organization,
        'department': department,
        'title': f'Dodaj stanowisko w dziale "{department.name}"'
    })


@login_required
@user_passes_test(is_admin)
def position_update(request, pk):
    """Edycja stanowiska"""
    position = get_object_or_404(Position, pk=pk)
    organization = position.organization
    
    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            log_activity(request, 'update', 'position', position, 
                        f'Zaktualizowano stanowisko "{position.name}"')
            messages.success(request, f'Stanowisko "{position.name}" zostało zaktualizowane.')
            return redirect('core:organization_structure')
    else:
        form = PositionForm(instance=position)
    
    return render(request, 'core/position_form.html', {
        'form': form,
        'position': position,
        'organization': organization,
        'title': 'Edytuj stanowisko'
    })


@login_required
@user_passes_test(is_admin)
def position_delete(request, pk):
    """Usuwanie stanowiska"""
    position = get_object_or_404(Position, pk=pk)
    organization = position.organization
    related = get_related_objects(position)
    blocked = has_blocking_relations(related)
    
    # Sprawdź pracowników z M2M
    employee_count = position.employees.count()
    
    if request.method == 'POST' and not blocked:
        name = position.name
        pos_id = position.pk
        try:
            position.delete()
            ActivityLog.log(
                user=request.user,
                action='delete',
                category='position',
                object_type='Position',
                object_id=pos_id,
                object_repr=name,
                description=f'Usunięto stanowisko "{name}"',
                request=request
            )
            messages.success(request, f'Stanowisko "{name}" zostało usunięte.')
            return redirect('core:organization_structure')
        except Exception as e:
            messages.error(request, f'Nie można usunąć stanowiska: {e}')
            return redirect('core:organization_structure')
    
    return render(request, 'core/position_confirm_delete.html', {
        'position': position,
        'organization': organization,
        'related': related,
        'blocked': blocked,
        'employee_count': employee_count,
    })


# ============== UPRAWNIENIA ==============

@login_required
@user_passes_test(is_admin)
def permission_list(request):
    """Lista uprawnień w systemie - uprawnienia są predefiniowane, tylko do odczytu"""
    permissions = Permission.objects.all().order_by('category', 'name')
    permission_groups = PermissionGroup.objects.prefetch_related('permissions').all()
    
    # Grupuj uprawnienia według kategorii
    permissions_by_category = {}
    for perm in permissions:
        cat = perm.category
        cat_display = perm.get_category_display()
        if cat not in permissions_by_category:
            permissions_by_category[cat] = {
                'label': cat_display,
                'permissions': []
            }
        permissions_by_category[cat]['permissions'].append(perm)
    
    return render(request, 'core/permission_list.html', {
        'permissions_by_category': permissions_by_category,
        'permission_groups': permission_groups,
        'total_permissions': permissions.count(),
    })


@login_required
@user_passes_test(is_admin)
def permission_create(request):
    """Tworzenie nowego uprawnienia"""
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            permission = form.save()
            log_activity(request, 'create', 'permission', permission, 
                        f'Utworzono uprawnienie "{permission.name}"')
            messages.success(request, f'Uprawnienie "{permission.name}" zostało utworzone.')
            return redirect('core:permission_list')
    else:
        form = PermissionForm()
    
    return render(request, 'core/permission_form.html', {
        'form': form,
        'title': 'Dodaj uprawnienie'
    })


@login_required
@user_passes_test(is_admin)
def permission_update(request, pk):
    """Edycja uprawnienia"""
    permission = get_object_or_404(Permission, pk=pk)
    
    if request.method == 'POST':
        form = PermissionForm(request.POST, instance=permission)
        if form.is_valid():
            form.save()
            log_activity(request, 'update', 'permission', permission, 
                        f'Zaktualizowano uprawnienie "{permission.name}"')
            messages.success(request, f'Uprawnienie "{permission.name}" zostało zaktualizowane.')
            return redirect('core:permission_list')
    else:
        form = PermissionForm(instance=permission)
    
    return render(request, 'core/permission_form.html', {
        'form': form,
        'permission': permission,
        'title': 'Edytuj uprawnienie'
    })


@login_required
@user_passes_test(is_admin)
def permission_delete(request, pk):
    """Usuwanie uprawnienia"""
    permission = get_object_or_404(Permission, pk=pk)
    related = get_related_objects(permission)
    blocked = has_blocking_relations(related)
    
    if request.method == 'POST' and not blocked:
        name = permission.name
        perm_id = permission.pk
        try:
            permission.delete()
            ActivityLog.log(
                user=request.user,
                action='delete',
                category='permission',
                object_type='Permission',
                object_id=perm_id,
                object_repr=name,
                description=f'Usunięto uprawnienie "{name}"',
                request=request
            )
            messages.success(request, f'Uprawnienie "{name}" zostało usunięte.')
            return redirect('core:permission_list')
        except Exception as e:
            messages.error(request, f'Nie można usunąć uprawnienia: {e}')
            return redirect('core:permission_list')
    
    return render(request, 'core/permission_confirm_delete.html', {
        'permission': permission,
        'related': related,
        'blocked': blocked,
    })


# ============== GRUPY UPRAWNIEŃ ==============

@login_required
@user_passes_test(is_admin)
def permission_group_create(request):
    """Tworzenie nowej grupy uprawnień"""
    if request.method == 'POST':
        form = PermissionGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            log_activity(request, 'create', 'permission', group, 
                        f'Utworzono grupę uprawnień "{group.name}"')
            messages.success(request, f'Grupa uprawnień "{group.name}" została utworzona.')
            return redirect('core:permission_list')
    else:
        form = PermissionGroupForm()
    
    return render(request, 'core/permission_group_form.html', {
        'form': form,
        'title': 'Dodaj grupę uprawnień'
    })


@login_required
@user_passes_test(is_admin)
def permission_group_update(request, pk):
    """Edycja grupy uprawnień"""
    group = get_object_or_404(PermissionGroup, pk=pk)
    
    if request.method == 'POST':
        form = PermissionGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            log_activity(request, 'update', 'permission', group, 
                        f'Zaktualizowano grupę uprawnień "{group.name}"')
            messages.success(request, f'Grupa uprawnień "{group.name}" została zaktualizowana.')
            return redirect('core:permission_list')
    else:
        form = PermissionGroupForm(instance=group)
    
    return render(request, 'core/permission_group_form.html', {
        'form': form,
        'group': group,
        'title': 'Edytuj grupę uprawnień'
    })


@login_required
@user_passes_test(is_admin)
def permission_group_delete(request, pk):
    """Usuwanie grupy uprawnień"""
    group = get_object_or_404(PermissionGroup, pk=pk)
    related = get_related_objects(group)
    blocked = has_blocking_relations(related)
    
    if request.method == 'POST' and not blocked:
        name = group.name
        group_id = group.pk
        try:
            group.delete()
            ActivityLog.log(
                user=request.user,
                action='delete',
                category='permission',
                object_type='PermissionGroup',
                object_id=group_id,
                object_repr=name,
                description=f'Usunięto grupę uprawnień "{name}"',
                request=request
            )
            messages.success(request, f'Grupa uprawnień "{name}" została usunięta.')
            return redirect('core:permission_list')
        except Exception as e:
            messages.error(request, f'Nie można usunąć grupy uprawnień: {e}')
            return redirect('core:permission_list')
    
    return render(request, 'core/permission_group_confirm_delete.html', {
        'group': group,
        'related': related,
        'blocked': blocked,
    })


# ============== PRZYPISYWANIE UPRAWNIEŃ ==============

@login_required
@user_passes_test(is_admin)
def position_permissions(request, pk):
    """Zarządzanie uprawnieniami stanowiska"""
    position = get_object_or_404(Position, pk=pk)
    all_groups = PermissionGroup.objects.all()
    assigned_groups = position.permission_assignments.all()
    assigned_group_ids = [pa.permission_group_id for pa in assigned_groups]
    
    if request.method == 'POST':
        selected_groups = request.POST.getlist('permission_groups')
        
        # Usuń stare przypisania
        PositionPermission.objects.filter(position=position).delete()
        
        # Dodaj nowe przypisania
        for group_id in selected_groups:
            PositionPermission.objects.create(
                position=position,
                permission_group_id=group_id
            )
        
        messages.success(request, f'Uprawnienia dla stanowiska "{position.name}" zostały zaktualizowane.')
        return redirect('core:organization_structure')
    
    return render(request, 'core/position_permissions.html', {
        'position': position,
        'all_groups': all_groups,
        'assigned_group_ids': assigned_group_ids,
    })


@login_required
@user_passes_test(is_admin)
def department_permissions(request, pk):
    """Zarządzanie uprawnieniami działu"""
    department = get_object_or_404(Department, pk=pk)
    all_groups = PermissionGroup.objects.all()
    assigned_groups = department.permission_assignments.all()
    assigned_group_ids = [da.permission_group_id for da in assigned_groups]
    
    if request.method == 'POST':
        selected_groups = request.POST.getlist('permission_groups')
        
        # Usuń stare przypisania
        DepartmentPermission.objects.filter(department=department).delete()
        
        # Dodaj nowe przypisania
        for group_id in selected_groups:
            DepartmentPermission.objects.create(
                department=department,
                permission_group_id=group_id
            )
        
        messages.success(request, f'Uprawnienia dla działu "{department.name}" zostały zaktualizowane.')
        return redirect('core:organization_structure')
    
    return render(request, 'core/department_permissions.html', {
        'department': department,
        'all_groups': all_groups,
        'assigned_group_ids': assigned_group_ids,
    })


# ============== PRACOWNICY ==============

@login_required
@user_passes_test(is_admin)
def employee_list(request):
    """Lista pracowników"""
    organization = get_or_create_organization()
    employees = Employee.objects.filter(organization=organization).select_related('department', 'user').prefetch_related('positions')
    
    return render(request, 'core/employee_list.html', {
        'employees': employees,
        'organization': organization,
    })


@login_required
@user_passes_test(is_admin)
def employee_create(request):
    """Tworzenie nowego pracownika"""
    organization = get_or_create_organization()
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, organization=organization)
        if form.is_valid():
            employee = form.save()
            log_activity(request, 'create', 'employee', employee, 
                        f'Utworzono pracownika "{employee.get_full_name()}"')
            messages.success(request, f'Pracownik "{form.cleaned_data["first_name"]} {form.cleaned_data["last_name"]}" został dodany.')
            return redirect('core:employee_list')
    else:
        form = EmployeeForm(organization=organization)
    
    return render(request, 'core/employee_form.html', {
        'form': form,
        'title': 'Dodaj pracownika',
    })


@login_required
@user_passes_test(is_admin)
def employee_update(request, pk):
    """Edycja pracownika"""
    employee = get_object_or_404(Employee, pk=pk)
    organization = employee.organization
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee, organization=organization)
        if form.is_valid():
            form.save()
            log_activity(request, 'update', 'employee', employee, 
                        f'Zaktualizowano dane pracownika "{employee.get_full_name()}"')
            messages.success(request, f'Dane pracownika "{employee.get_full_name()}" zostały zaktualizowane.')
            return redirect('core:employee_list')
    else:
        form = EmployeeForm(instance=employee, organization=organization)
    
    return render(request, 'core/employee_form.html', {
        'form': form,
        'employee': employee,
        'title': f'Edytuj pracownika: {employee.get_full_name()}',
    })


@login_required
@user_passes_test(is_admin)
def employee_delete(request, pk):
    """Usuwanie pracownika"""
    employee = get_object_or_404(Employee, pk=pk)
    related = get_related_objects(employee)
    # Sprawdź też powiązania user (PROTECT na DocumentLog, DocumentVersion itp.)
    user_related = get_related_objects(employee.user)
    blocked = has_blocking_relations(related) or has_blocking_relations(user_related)
    
    # Połącz informacje o powiązaniach
    all_protected = related['protected'] + user_related['protected']
    all_cascade = related['cascade'] + user_related['cascade']
    combined_related = {
        'protected': all_protected,
        'cascade': all_cascade,
        'set_null': related['set_null'] + user_related['set_null'],
    }
    
    if request.method == 'POST' and not blocked:
        user = employee.user
        name = employee.get_full_name()
        emp_id = employee.pk
        try:
            employee.delete()
            user.delete()
            ActivityLog.log(
                user=request.user,
                action='delete',
                category='employee',
                object_type='Employee',
                object_id=emp_id,
                object_repr=name,
                description=f'Usunięto pracownika "{name}"',
                request=request
            )
            messages.success(request, f'Pracownik "{name}" został usunięty.')
            return redirect('core:employee_list')
        except Exception as e:
            messages.error(request, f'Nie można usunąć pracownika: {e}')
            return redirect('core:employee_list')
    
    return render(request, 'core/employee_confirm_delete.html', {
        'employee': employee,
        'related': combined_related,
        'blocked': blocked,
    })


@login_required
@user_passes_test(is_admin)
def employee_permissions(request, pk):
    """Podgląd uprawnień pracownika (dziedziczone z działu i stanowiska)"""
    employee = get_object_or_404(Employee, pk=pk)
    permissions = employee.get_permissions()
    
    # Grupuj uprawnienia po kategorii
    permissions_by_category = {}
    for perm in permissions:
        category = perm.get_category_display()
        if category not in permissions_by_category:
            permissions_by_category[category] = []
        permissions_by_category[category].append(perm)
    
    return render(request, 'core/employee_permissions.html', {
        'employee': employee,
        'permissions_by_category': permissions_by_category,
    })


# ============== DZIENNIK ZDARZEŃ ==============

@login_required
@user_passes_test(is_admin)
def activity_log_list(request):
    """Lista zdarzeń w dzienniku z filtrowaniem i paginacją"""
    logs = ActivityLog.objects.select_related('user').all()
    
    # Filtrowanie po kategorii
    category = request.GET.get('category')
    if category:
        logs = logs.filter(category=category)
    
    # Filtrowanie po akcji
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    # Filtrowanie po użytkowniku
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Filtrowanie po dacie od
    date_from = request.GET.get('date_from')
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    
    # Filtrowanie po dacie do
    date_to = request.GET.get('date_to')
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    # Wyszukiwanie tekstowe
    search = request.GET.get('search')
    if search:
        logs = logs.filter(
            Q(object_repr__icontains=search) |
            Q(description__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # Paginacja
    paginator = Paginator(logs, 50)  # 50 zdarzeń na stronę
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Pobierz unikalne wartości do filtrów
    from django.contrib.auth.models import User
    users = User.objects.filter(activity_logs__isnull=False).distinct()
    
    return render(request, 'core/activity_log_list.html', {
        'page_obj': page_obj,
        'logs': page_obj,
        'categories': ActivityLog.CATEGORY_CHOICES,
        'actions': ActivityLog.ACTION_CHOICES,
        'users': users,
        'current_filters': {
            'category': category,
            'action': action,
            'user': user_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    })


# ============== FUNKCJE POMOCNICZE DO LOGOWANIA ==============

def log_activity(request, action, category, obj, description, details=None):
    """
    Funkcja pomocnicza do logowania zdarzeń.
    
    Args:
        request: Obiekt request
        action: Typ akcji (create, update, delete, itp.)
        category: Kategoria zdarzenia
        obj: Obiekt, którego dotyczy zdarzenie (lub None)
        description: Opis zdarzenia
        details: Dodatkowe szczegóły jako dict (opcjonalne)
    """
    if obj:
        object_type = obj.__class__.__name__
        object_id = obj.pk if hasattr(obj, 'pk') else None
        object_repr = str(obj)
    else:
        object_type = 'System'
        object_id = None
        object_repr = '-'
    
    ActivityLog.log(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        category=category,
        object_type=object_type,
        object_id=object_id,
        object_repr=object_repr,
        description=description,
        details=details,
        request=request
    )
