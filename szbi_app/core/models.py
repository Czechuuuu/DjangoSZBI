from django.db import models
from django.contrib.auth.models import User


class Organization(models.Model):
    """Model organizacji/jednostki"""
    name = models.CharField(max_length=255, verbose_name="Nazwa organizacji")
    short_name = models.CharField(max_length=50, verbose_name="Skrót nazwy", blank=True)
    description = models.TextField(verbose_name="Opis", blank=True)
    address = models.TextField(verbose_name="Adres", blank=True)
    phone = models.CharField(max_length=50, verbose_name="Telefon", blank=True)
    email = models.EmailField(verbose_name="Email", blank=True)
    website = models.URLField(verbose_name="Strona WWW", blank=True)
    nip = models.CharField(max_length=20, verbose_name="NIP", blank=True)
    regon = models.CharField(max_length=20, verbose_name="REGON", blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name="Organizacja nadrzędna"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_organizations',
        verbose_name="Utworzył"
    )

    class Meta:
        verbose_name = "Organizacja"
        verbose_name_plural = "Organizacje"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Zwraca pełną ścieżkę organizacji w hierarchii"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class Department(models.Model):
    """Model działu/grupy w organizacji"""
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='departments',
        verbose_name="Organizacja"
    )
    name = models.CharField(max_length=255, verbose_name="Nazwa działu")
    description = models.TextField(verbose_name="Opis", blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subdepartments',
        verbose_name="Dział nadrzędny"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Dział"
        verbose_name_plural = "Działy"
        ordering = ['organization', 'name']

    def __str__(self):
        return f"{self.organization.short_name or self.organization.name} - {self.name}"


class Position(models.Model):
    """Model stanowiska w organizacji"""
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='positions',
        verbose_name="Organizacja"
    )
    name = models.CharField(max_length=255, verbose_name="Nazwa stanowiska")
    description = models.TextField(verbose_name="Opis", blank=True)
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='positions',
        verbose_name="Dział"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Stanowisko"
        verbose_name_plural = "Stanowiska"
        ordering = ['organization', 'name']

    def __str__(self):
        return f"{self.name} ({self.organization.short_name or self.organization.name})"


# ============== PRACOWNICY ==============

class Employee(models.Model):
    """Model pracownika"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee',
        verbose_name="Konto użytkownika"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name="Organizacja"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name="Dział"
    )
    positions = models.ManyToManyField(
        Position,
        blank=True,
        related_name='employees',
        verbose_name="Stanowiska"
    )
    first_name = models.CharField(max_length=100, verbose_name="Imię")
    last_name = models.CharField(max_length=100, verbose_name="Nazwisko")
    hire_date = models.DateField(verbose_name="Data zatrudnienia", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Aktywny")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Pracownik"
        verbose_name_plural = "Pracownicy"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_positions_display(self):
        """Zwraca listę stanowisk jako string"""
        return ", ".join([p.name for p in self.positions.all()])

    def get_permissions(self):
        """Zwraca wszystkie uprawnienia pracownika (z poziomu stanowisk, działu i bezpośrednio przypisanych grup)"""
        permissions = set()
        
        # Uprawnienia ze stanowisk
        for position in self.positions.all():
            for pa in position.permission_assignments.all():
                for perm in pa.permission_group.permissions.all():
                    permissions.add(perm)
        
        # Uprawnienia z działu
        if self.department:
            for da in self.department.permission_assignments.all():
                for perm in da.permission_group.permissions.all():
                    permissions.add(perm)
        
        # Uprawnienia z bezpośrednio przypisanych grup
        for epg in self.permission_group_assignments.all():
            for perm in epg.permission_group.permissions.all():
                permissions.add(perm)
        
        return permissions


class EmployeePermissionGroup(models.Model):
    """Bezpośrednie przypisanie grupy uprawnień do pracownika"""
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='permission_group_assignments',
        verbose_name="Pracownik"
    )
    permission_group = models.ForeignKey(
        'PermissionGroup',
        on_delete=models.CASCADE,
        related_name='employee_assignments',
        verbose_name="Grupa uprawnień"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data przypisania")

    class Meta:
        verbose_name = "Grupa uprawnień pracownika"
        verbose_name_plural = "Grupy uprawnień pracowników"
        unique_together = ['employee', 'permission_group']

    def __str__(self):
        return f"{self.employee} - {self.permission_group}"


# ============== UPRAWNIENIA ==============

class Permission(models.Model):
    """Model pojedynczego uprawnienia w systemie"""
    CATEGORY_CHOICES = [
        ('documents', 'Dokumenty'),
        ('assets', 'Aktywa'),
        ('incidents', 'Incydenty'),
        ('audits', 'Audyty'),
        ('organization', 'Organizacja'),
        ('system', 'System'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Nazwa uprawnienia")
    description = models.TextField(verbose_name="Opis", blank=True)
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default='system',
        verbose_name="Kategoria"
    )

    class Meta:
        verbose_name = "Uprawnienie"
        verbose_name_plural = "Uprawnienia"
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class PermissionGroup(models.Model):
    """Model grupy uprawnień"""
    name = models.CharField(max_length=255, verbose_name="Nazwa grupy")
    description = models.TextField(verbose_name="Opis", blank=True)
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='groups',
        verbose_name="Uprawnienia"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Grupa uprawnień"
        verbose_name_plural = "Grupy uprawnień"
        ordering = ['name']

    def __str__(self):
        return self.name


class PositionPermission(models.Model):
    """Przypisanie grupy uprawnień do stanowiska"""
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='permission_assignments',
        verbose_name="Stanowisko"
    )
    permission_group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name='position_assignments',
        verbose_name="Grupa uprawnień"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data przypisania")

    class Meta:
        verbose_name = "Uprawnienie stanowiska"
        verbose_name_plural = "Uprawnienia stanowisk"
        unique_together = ['position', 'permission_group']

    def __str__(self):
        return f"{self.position.name} - {self.permission_group.name}"


class DepartmentPermission(models.Model):
    """Przypisanie grupy uprawnień do działu (dziedziczone przez wszystkie stanowiska)"""
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='permission_assignments',
        verbose_name="Dział"
    )
    permission_group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name='department_assignments',
        verbose_name="Grupa uprawnień"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data przypisania")

    class Meta:
        verbose_name = "Uprawnienie działu"
        verbose_name_plural = "Uprawnienia działów"
        unique_together = ['department', 'permission_group']

    def __str__(self):
        return f"{self.department.name} - {self.permission_group.name}"
