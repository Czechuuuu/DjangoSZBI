from django import forms
from django.contrib.auth.models import User
from .models import Organization, Department, Position, Permission, PermissionGroup, Employee, EmployeePermissionGroup


class OrganizationForm(forms.ModelForm):
    """Formularz organizacji"""
    
    class Meta:
        model = Organization
        fields = ['name', 'short_name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class DepartmentForm(forms.ModelForm):
    """Formularz działu"""
    
    class Meta:
        model = Department
        fields = ['name', 'description', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        
        if organization:
            # Filtruj tylko działy z tej samej organizacji
            self.fields['parent'].queryset = Department.objects.filter(
                organization=organization
            )
            if self.instance.pk:
                self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
                    pk=self.instance.pk
                )


class PositionForm(forms.ModelForm):
    """Formularz stanowiska"""
    
    class Meta:
        model = Position
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PermissionForm(forms.ModelForm):
    """Formularz uprawnienia"""
    
    class Meta:
        model = Permission
        fields = ['name', 'description', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PermissionGroupForm(forms.ModelForm):
    """Formularz grupy uprawnień"""
    
    class Meta:
        model = PermissionGroup
        fields = ['name', 'description', 'permissions']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'permissions': forms.CheckboxSelectMultiple(),
        }


class EmployeeForm(forms.ModelForm):
    """Formularz pracownika z tworzeniem konta użytkownika"""
    
    username = forms.CharField(
        max_length=150, 
        label="Nazwa użytkownika",
        help_text="Login do systemu (bez spacji i polskich znaków)"
    )
    password = forms.CharField(
        widget=forms.PasswordInput, 
        label="Hasło",
        required=False,
        help_text="Pozostaw puste, aby nie zmieniać hasła przy edycji"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, 
        label="Powtórz hasło",
        required=False
    )
    is_admin = forms.BooleanField(
        required=False, 
        label="Administrator systemu",
        help_text="Administrator ma dostęp do wszystkich funkcji zarządzania"
    )
    
    permission_groups = forms.ModelMultipleChoiceField(
        queryset=PermissionGroup.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Grupy uprawnień",
        help_text="Dodatkowe uprawnienia przypisane bezpośrednio do pracownika"
    )
    
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'department', 'positions', 'hire_date', 'is_active']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'positions': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        
        # Ustaw queryset dla grup uprawnień
        self.fields['permission_groups'].queryset = PermissionGroup.objects.all()
        
        if organization:
            # Filtruj działy i stanowiska z tej organizacji
            self.fields['department'].queryset = Department.objects.filter(organization=organization)
            self.fields['positions'].queryset = Position.objects.filter(organization=organization)
        
        # Przy edycji - wypełnij przypisane grupy uprawnień
        if self.instance and self.instance.pk:
            assigned_groups = self.instance.permission_group_assignments.values_list('permission_group_id', flat=True)
            self.fields['permission_groups'].initial = assigned_groups
        
        # Przy edycji - wypełnij pola użytkownika
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['is_admin'].initial = self.instance.user.is_staff
            self.fields['password'].required = False
        else:
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True

    def save(self, commit=True):
        employee = super().save(commit=False)
        
        if self.instance.pk and hasattr(self.instance, 'user'):
            # Edycja istniejącego pracownika
            user = self.instance.user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.is_staff = self.cleaned_data['is_admin']
            user.is_active = self.cleaned_data['is_active']
            
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
            
            user.save()
            employee.user = user
        else:
            # Nowy pracownik - utwórz konto
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                is_staff=self.cleaned_data['is_admin'],
                is_active=self.cleaned_data['is_active']
            )
            employee.user = user
        
        employee.organization = self.organization
        
        if commit:
            employee.save()
            self.save_m2m()  # Zapisz relacje M2M (positions)
            
            # Zapisz grupy uprawnień
            EmployeePermissionGroup.objects.filter(employee=employee).delete()
            for group in self.cleaned_data.get('permission_groups', []):
                EmployeePermissionGroup.objects.create(employee=employee, permission_group=group)
        
        return employee

    def clean_username(self):
        username = self.cleaned_data['username']
        # Sprawdź czy username już istnieje (ale nie dla aktualnego użytkownika)
        user_query = User.objects.filter(username=username)
        if self.instance and self.instance.pk:
            user_query = user_query.exclude(pk=self.instance.user.pk)
        if user_query.exists():
            raise forms.ValidationError("Ta nazwa użytkownika jest już zajęta.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        # Przy nowym pracowniku hasło jest wymagane
        if not self.instance.pk and not password:
            self.add_error('password', 'Hasło jest wymagane przy tworzeniu nowego pracownika.')
        
        # Sprawdź zgodność haseł
        if password and password != password_confirm:
            self.add_error('password_confirm', 'Hasła nie są zgodne.')
        
        return cleaned_data


