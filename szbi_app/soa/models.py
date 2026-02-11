from django.db import models
from django.contrib.auth.models import User
from core.models import Employee
from dictionary.models import ISORequirement
from documents.models import Document


class SoADeclaration(models.Model):
    """Deklaracja Stosowania (Statement of Applicability)"""
    
    STATUS_CHOICES = [
        ('draft', 'Wersja robocza'),
        ('review', 'W przeglądzie'),
        ('approved', 'Zatwierdzona'),
        ('current', 'Obowiązująca'),
        ('archived', 'Zarchiwizowana'),
    ]
    
    designation = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Oznaczenie",
        help_text="Unikalne oznaczenie deklaracji, np. SOA-001"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Nazwa"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Opis"
    )
    version = models.CharField(
        max_length=20,
        default="1.0",
        verbose_name="Wersja"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Status"
    )
    
    # Właściciel i daty
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_soa_declarations',
        verbose_name="Właściciel"
    )
    effective_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data obowiązywania"
    )
    
    # Metadane
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_soa_declarations',
        verbose_name="Utworzył"
    )

    class Meta:
        verbose_name = "Deklaracja Stosowania"
        verbose_name_plural = "Deklaracje Stosowania"
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.designation}] {self.name} ({self.get_status_display()})"
    
    def get_entries_count(self):
        """Zwraca liczbę pozycji w deklaracji"""
        return self.entries.count()
    
    def get_applicable_count(self):
        """Zwraca liczbę stosowanych wymagań"""
        return self.entries.filter(applicability='yes').count()


class SoAEntry(models.Model):
    """Pozycja w Deklaracji Stosowania - pojedyncze wymaganie ISO"""
    
    APPLICABILITY_CHOICES = [
        ('yes', 'Tak - stosowane'),
        ('no', 'Nie - niestosowane'),
        ('partial', 'Częściowo stosowane'),
        ('not_applicable', 'Nie dotyczy'),
    ]
    
    declaration = models.ForeignKey(
        SoADeclaration,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name="Deklaracja"
    )
    requirement = models.ForeignKey(
        ISORequirement,
        on_delete=models.PROTECT,
        related_name='soa_entries',
        verbose_name="Wymaganie ISO"
    )
    
    # Status stosowania
    applicability = models.CharField(
        max_length=20,
        choices=APPLICABILITY_CHOICES,
        default='yes',
        verbose_name="Stosowanie"
    )
    
    # Osoba odpowiedzialna
    responsible_person = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='soa_responsibilities',
        verbose_name="Osoba odpowiedzialna"
    )
    
    # Powiązane dokumenty
    related_documents = models.ManyToManyField(
        Document,
        blank=True,
        related_name='soa_entries',
        verbose_name="Powiązane dokumenty"
    )
    
    # Uzasadnienie i opis
    justification = models.TextField(
        verbose_name="Uzasadnienie",
        help_text="Uzasadnienie stosowania lub niestosowania wymagania"
    )
    additional_description = models.TextField(
        blank=True,
        verbose_name="Dodatkowy opis"
    )
    
    # Metadane
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Pozycja Deklaracji Stosowania"
        verbose_name_plural = "Pozycje Deklaracji Stosowania"
        ordering = ['requirement__iso_id']
        unique_together = ['declaration', 'requirement']

    def __str__(self):
        return f"{self.declaration.designation}: {self.requirement.iso_id}"


class SoALog(models.Model):
    """Historia zmian w deklaracjach stosowania"""
    
    ACTION_CHOICES = [
        ('created', 'Utworzono'),
        ('updated', 'Zaktualizowano'),
        ('status_changed', 'Zmieniono status'),
        ('entry_added', 'Dodano pozycję'),
        ('entry_updated', 'Zaktualizowano pozycję'),
        ('entry_removed', 'Usunięto pozycję'),
    ]
    
    declaration = models.ForeignKey(
        SoADeclaration,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name="Deklaracja"
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
        verbose_name = "Dziennik Deklaracji Stosowania"
        verbose_name_plural = "Dziennik Deklaracji Stosowania"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.declaration.designation}: {self.get_action_display()} ({self.timestamp})"
