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


# ============== DZIENNIK ZDARZEŃ ==============

class ActivityLog(models.Model):
    """Model dziennika zdarzeń - rejestruje wszystkie operacje w systemie"""
    ACTION_CHOICES = [
        ('create', 'Utworzenie'),
        ('update', 'Modyfikacja'),
        ('delete', 'Usunięcie'),
        ('assign', 'Przypisanie'),
        ('unassign', 'Cofnięcie przypisania'),
        ('login', 'Logowanie'),
        ('logout', 'Wylogowanie'),
        ('view', 'Wyświetlenie'),
        ('export', 'Eksport'),
        ('import', 'Import'),
        ('other', 'Inne'),
    ]
    
    CATEGORY_CHOICES = [
        ('organization', 'Organizacja'),
        ('department', 'Dział'),
        ('position', 'Stanowisko'),
        ('employee', 'Pracownik'),
        ('permission', 'Uprawnienia'),
        ('document', 'Dokument'),
        ('asset', 'Aktywo'),
        ('incident', 'Incydent'),
        ('audit', 'Audyt'),
        ('system', 'System'),
        ('auth', 'Autoryzacja'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name="Użytkownik"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="Akcja"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Kategoria"
    )
    object_type = models.CharField(
        max_length=100,
        verbose_name="Typ obiektu",
        help_text="Nazwa modelu, np. 'Employee', 'Department'"
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID obiektu"
    )
    object_repr = models.CharField(
        max_length=255,
        verbose_name="Reprezentacja obiektu",
        help_text="Tekstowa reprezentacja obiektu, np. nazwa pracownika"
    )
    description = models.TextField(
        verbose_name="Opis zdarzenia"
    )
    details = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Szczegóły",
        help_text="Dodatkowe informacje w formacie JSON"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adres IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data zdarzenia"
    )

    class Meta:
        verbose_name = "Zdarzenie"
        verbose_name_plural = "Dziennik zdarzeń"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {user_str}: {self.get_action_display()} - {self.object_repr}"

    @classmethod
    def log(cls, user, action, category, object_type, object_repr, description, 
            object_id=None, details=None, request=None):
        """
        Metoda pomocnicza do tworzenia wpisów w dzienniku zdarzeń.
        
        Args:
            user: Użytkownik wykonujący akcję
            action: Typ akcji (create, update, delete, itp.)
            category: Kategoria zdarzenia (employee, department, itp.)
            object_type: Nazwa typu/modelu obiektu
            object_repr: Tekstowa reprezentacja obiektu
            description: Opis zdarzenia
            object_id: ID obiektu (opcjonalne)
            details: Dodatkowe szczegóły jako dict (opcjonalne)
            request: Obiekt request do pobrania IP i User-Agent (opcjonalne)
        """
        ip_address = None
        user_agent = ''
        
        if request:
            # Pobierz IP (uwzględniając proxy)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return cls.objects.create(
            user=user,
            action=action,
            category=category,
            object_type=object_type,
            object_id=object_id,
            object_repr=object_repr,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
