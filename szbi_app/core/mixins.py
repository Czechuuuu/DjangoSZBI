"""
Mixiny i dekoratory do sprawdzania uprawnień w systemie SZBI.
"""
from functools import wraps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def get_employee_from_user(user):
    """Pobiera obiekt Employee dla zalogowanego użytkownika"""
    if not user.is_authenticated:
        return None
    try:
        return user.employee
    except AttributeError:
        return None


def user_has_permission(user, permission_name):
    """Sprawdza czy użytkownik ma dane uprawnienie"""
    # Superuser ma wszystkie uprawnienia
    if user.is_superuser:
        return True
    
    employee = get_employee_from_user(user)
    if not employee:
        return False
    
    return employee.has_permission(permission_name)


def user_has_any_permission(user, permission_names):
    """Sprawdza czy użytkownik ma którekolwiek z podanych uprawnień"""
    # Superuser ma wszystkie uprawnienia
    if user.is_superuser:
        return True
    
    employee = get_employee_from_user(user)
    if not employee:
        return False
    
    return employee.has_any_permission(permission_names)


class SZBIPermissionRequiredMixin(LoginRequiredMixin):
    """
    Mixin sprawdzający uprawnienia SZBI dla widoków opartych na klasach.
    
    Użycie:
        class MyView(SZBIPermissionRequiredMixin, ListView):
            szbi_permission_required = 'Przeglądanie rejestru aktywów'
            # lub lista uprawnień (wystarczy jedno):
            szbi_permission_required = ['Przeglądanie rejestru aktywów', 'Administrator rejestru aktywów']
    """
    szbi_permission_required = None
    szbi_permission_denied_message = "Nie masz uprawnień do wykonania tej operacji."
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not self.has_szbi_permission():
            messages.error(request, self.szbi_permission_denied_message)
            return self.handle_permission_denied()
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_szbi_permission(self):
        """Sprawdza czy użytkownik ma wymagane uprawnienie"""
        if self.szbi_permission_required is None:
            return True
        
        # Superuser ma wszystkie uprawnienia
        if self.request.user.is_superuser:
            return True
        
        employee = get_employee_from_user(self.request.user)
        if not employee:
            return False
        
        # Jeśli to lista uprawnień - wystarczy jedno
        if isinstance(self.szbi_permission_required, (list, tuple)):
            return employee.has_any_permission(self.szbi_permission_required)
        
        # Pojedyncze uprawnienie
        return employee.has_permission(self.szbi_permission_required)
    
    def handle_permission_denied(self):
        """Obsługa braku uprawnień - domyślnie przekierowuje do dashboardu"""
        return redirect('core:dashboard')


class SZBIAllPermissionsRequiredMixin(LoginRequiredMixin):
    """
    Mixin wymagający WSZYSTKICH podanych uprawnień.
    
    Użycie:
        class MyView(SZBIAllPermissionsRequiredMixin, UpdateView):
            szbi_permissions_required = ['Właściciel dokumentów', 'Zatwierdzający dokumenty']
    """
    szbi_permissions_required = None
    szbi_permission_denied_message = "Nie masz wszystkich wymaganych uprawnień."
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not self.has_all_szbi_permissions():
            messages.error(request, self.szbi_permission_denied_message)
            return self.handle_permission_denied()
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_all_szbi_permissions(self):
        """Sprawdza czy użytkownik ma wszystkie wymagane uprawnienia"""
        if not self.szbi_permissions_required:
            return True
        
        if self.request.user.is_superuser:
            return True
        
        employee = get_employee_from_user(self.request.user)
        if not employee:
            return False
        
        return employee.has_all_permissions(self.szbi_permissions_required)
    
    def handle_permission_denied(self):
        return redirect('core:dashboard')


def szbi_permission_required(permission_name, login_url=None, raise_exception=False):
    """
    Dekorator dla widoków funkcyjnych wymagający uprawnienia SZBI.
    
    Użycie:
        @szbi_permission_required('Przeglądanie rejestru aktywów')
        def my_view(request):
            ...
        
        # Lub z listą (wystarczy jedno):
        @szbi_permission_required(['Przeglądanie rejestru aktywów', 'Administrator rejestru aktywów'])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path(), login_url)
            
            has_perm = False
            
            if request.user.is_superuser:
                has_perm = True
            else:
                employee = get_employee_from_user(request.user)
                if employee:
                    if isinstance(permission_name, (list, tuple)):
                        has_perm = employee.has_any_permission(permission_name)
                    else:
                        has_perm = employee.has_permission(permission_name)
            
            if has_perm:
                return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied("Nie masz uprawnień do wykonania tej operacji.")
            
            messages.error(request, "Nie masz uprawnień do wykonania tej operacji.")
            return redirect('core:dashboard')
        
        return _wrapped_view
    return decorator


# ============== STAŁE Z NAZWAMI UPRAWNIEŃ ==============
# Użyj tych stałych zamiast stringów dla lepszej kontroli nad błędami

# Dokumenty
PERM_DOCUMENTS_ADMIN = 'Administrator dokumentów'
PERM_DOCUMENTS_OWNER = 'Właściciel dokumentów'
PERM_DOCUMENTS_MANAGER = 'Menedżer dokumentów'
PERM_DOCUMENTS_APPROVER = 'Zatwierdzający dokumenty'
PERM_DOCUMENTS_SIGNER = 'Podpisujący dokumenty'
PERM_DOCUMENTS_VERIFY_SIGNATURES = 'Weryfikujący podpisy elektroniczne'

# Aktywa
PERM_ASSETS_ADMIN = 'Administrator rejestru aktywów'
PERM_ASSETS_OWNER = 'Właściciel rejestru aktywów'
PERM_ASSETS_VIEW = 'Przeglądanie rejestru aktywów'

# Incydenty
PERM_INCIDENTS_VIEW_ALL = 'Przeglądanie wszystkich incydentów bezpieczeństwa'
PERM_INCIDENTS_VIEW_OWN = 'Przeglądanie moich incydentów bezpieczeństwa'
PERM_INCIDENTS_ADMIN = 'Administrator incydentów bezpieczeństwa'
PERM_INCIDENTS_MANAGE = 'Zarządzanie przypisanymi incydentami bezpieczeństwa'

# Deklaracje zgodności (SoA)
PERM_COMPLIANCE_ADMIN = 'Administrator deklaracji zgodności'
PERM_COMPLIANCE_OWNER = 'Właściciel deklaracji zgodności'
PERM_COMPLIANCE_MANAGER = 'Menedżer deklaracji zgodności'
PERM_COMPLIANCE_APPROVER = 'Zatwierdzający deklaracje zgodności'

# Słownik
PERM_DICTIONARY_MANAGE = 'Zarządzanie słownikami wymagań norm i przepisów'

# Dziennik zdarzeń
PERM_ACTIVITY_LOG_VIEW = 'Przeglądanie dziennika zdarzeń'
