from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse

from .models import Organization, Department, Position, Permission, PermissionGroup, PositionPermission, DepartmentPermission, Employee
from .forms import OrganizationForm, DepartmentForm, PositionForm, PermissionForm, PermissionGroupForm, EmployeeForm


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
    context = {
        'is_admin': is_admin(request.user),
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
    
    if request.method == 'POST':
        name = department.name
        department.delete()
        messages.success(request, f'Dział "{name}" został usunięty.')
        return redirect('core:organization_structure')
    
    return render(request, 'core/department_confirm_delete.html', {
        'department': department,
        'organization': organization
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
    
    if request.method == 'POST':
        name = position.name
        position.delete()
        messages.success(request, f'Stanowisko "{name}" zostało usunięte.')
        return redirect('core:organization_structure')
    
    return render(request, 'core/position_confirm_delete.html', {
        'position': position,
        'organization': organization
    })


# ============== UPRAWNIENIA ==============

@login_required
@user_passes_test(is_admin)
def permission_list(request):
    """Lista uprawnień w systemie"""
    permissions = Permission.objects.all()
    permission_groups = PermissionGroup.objects.all()
    
    return render(request, 'core/permission_list.html', {
        'permissions': permissions,
        'permission_groups': permission_groups,
    })


@login_required
@user_passes_test(is_admin)
def permission_create(request):
    """Tworzenie nowego uprawnienia"""
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            permission = form.save()
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
    
    if request.method == 'POST':
        name = permission.name
        permission.delete()
        messages.success(request, f'Uprawnienie "{name}" zostało usunięte.')
        return redirect('core:permission_list')
    
    return render(request, 'core/permission_confirm_delete.html', {
        'permission': permission
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
    
    if request.method == 'POST':
        name = group.name
        group.delete()
        messages.success(request, f'Grupa uprawnień "{name}" została usunięta.')
        return redirect('core:permission_list')
    
    return render(request, 'core/permission_group_confirm_delete.html', {
        'group': group
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
            form.save()
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
    
    if request.method == 'POST':
        user = employee.user
        name = employee.get_full_name()
        employee.delete()
        user.delete()  # Usuń też konto użytkownika
        messages.success(request, f'Pracownik "{name}" został usunięty.')
        return redirect('core:employee_list')
    
    return render(request, 'core/employee_confirm_delete.html', {
        'employee': employee,
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
