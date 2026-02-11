from django.db import models
from django.contrib.auth.models import User
from core.models import Department, Employee


class AssetCategory(models.Model):
    """Kategoria/Grupa aktywów - np. Sprzęt IT, Oprogramowanie, Dane, Usługi"""
    name = models.CharField(
        max_length=100,
        verbose_name="Nazwa kategorii"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Kod kategorii",
        help_text="Krótki kod, np. HW, SW, DATA, SVC"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Opis"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Kategoria nadrzędna"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Kategoria aktywów"
        verbose_name_plural = "Kategorie aktywów"
        ordering = ['code']

    def __str__(self):
        return f"[{self.code}] {self.name}"
    
    def get_full_path(self):
        """Zwraca pełną ścieżkę kategorii w hierarchii"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class Asset(models.Model):
    """Model pojedynczego aktywa w rejestrze"""
    
    STATUS_CHOICES = [
        ('active', 'Aktywny'),
        ('inactive', 'Nieaktywny'),
        ('in_repair', 'W naprawie'),
        ('disposed', 'Zlikwidowany'),
        ('planned', 'Planowany'),
    ]
    
    CRITICALITY_CHOICES = [
        ('low', 'Niska'),
        ('medium', 'Średnia'),
        ('high', 'Wysoka'),
        ('critical', 'Krytyczna'),
    ]
    
    # Podstawowe dane identyfikacyjne
    designation = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Oznaczenie",
        help_text="Unikalne oznaczenie aktywa, np. HW-001, SW-015"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Nazwa"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Opis"
    )
    
    # Klasyfikacja
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.PROTECT,
        related_name='assets',
        verbose_name="Kategoria"
    )
    
    # Status i krytyczność
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Status"
    )
    criticality = models.CharField(
        max_length=20,
        choices=CRITICALITY_CHOICES,
        default='medium',
        verbose_name="Krytyczność"
    )
    
    # Właściciel i lokalizacja
    owner = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='owned_assets',
        verbose_name="Właściciel"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        verbose_name="Dział"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Lokalizacja",
        help_text="Fizyczna lokalizacja aktywa (budynek, pokój, etc.)"
    )
    
    # Daty
    acquisition_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data nabycia"
    )
    warranty_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data wygaśnięcia gwarancji"
    )
    
    # Wartość
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Wartość (PLN)"
    )
    
    # Metadane
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assets',
        verbose_name="Utworzył"
    )

    class Meta:
        verbose_name = "Aktywo"
        verbose_name_plural = "Aktywa"
        ordering = ['designation']

    def __str__(self):
        return f"[{self.designation}] {self.name}"


class AssetLog(models.Model):
    """Historia zmian w aktywach"""
    
    ACTION_CHOICES = [
        ('created', 'Utworzono'),
        ('updated', 'Zaktualizowano'),
        ('status_changed', 'Zmieniono status'),
        ('owner_changed', 'Zmieniono właściciela'),
        ('disposed', 'Zlikwidowano'),
    ]
    
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name="Aktywo"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Użytkownik"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="Akcja"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Opis"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data i czas")

    class Meta:
        verbose_name = "Dziennik aktywów"
        verbose_name_plural = "Dziennik aktywów"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.asset.designation}: {self.get_action_display()} ({self.timestamp})"
