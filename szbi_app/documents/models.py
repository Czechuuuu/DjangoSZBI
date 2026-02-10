from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    STATUS = [
        ('draft', 'Szkic'),
        ('review', 'W przeglądzie'),
        ('approval', 'Oczekuje na zatwierdzenie'),
        ('published', 'Opublikowany'),
        ('archived', 'Zarchiwizowany'),
    ]

    DOCUMENT_TYPE_CHOICES = [
        ('policy', 'Polityka'),
        ('procedure', 'Procedura'),
        ('instruction', 'Instrukcja'),
        ('regulation', 'Regulamin'),
        ('plan', 'Plan'),
        ('report', 'Raport'),
        ('record', 'Zapis'),
        ('other', 'Inny'),
    ]

    # Dozwolone przejścia workflow
    WORKFLOW_TRANSITIONS = {
        'draft': ['review'],
        'review': ['draft', 'approval'],
        'approval': ['review', 'published'],
        'published': ['archived'],
        'archived': ['draft'],
    }

    designation = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Oznaczenie",
        help_text="Unikalne oznaczenie dokumentu, np. POL-001, PROC-003"
    )
    title = models.CharField(max_length=255, verbose_name="Tytuł")
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='other',
        verbose_name="Rodzaj dokumentu"
    )
    description = models.TextField(blank=True, verbose_name="Opis")
    owner = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        verbose_name="Właściciel"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS, 
        default='draft',
        verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Dokument"
        verbose_name_plural = "Dokumenty"
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.designation}] {self.title} ({self.get_status_display()})"
    
    def get_iso_requirements(self):
        """Zwraca listę powiązanych wymagań ISO"""
        return self.iso_mappings.select_related('iso_requirement').all()
    
    def get_iso_requirements_count(self):
        """Zwraca liczbę powiązanych wymagań ISO"""
        return self.iso_mappings.count()

    def get_current_version(self):
        """Zwraca aktualną (obowiązującą) wersję dokumentu"""
        return self.versions.filter(is_current=True).first()

    def get_allowed_transitions(self):
        """Zwraca dozwolone przejścia statusu dla bieżącego stanu"""
        return self.WORKFLOW_TRANSITIONS.get(self.status, [])

    def can_transition_to(self, new_status):
        """Sprawdza czy przejście do danego statusu jest dozwolone"""
        return new_status in self.get_allowed_transitions()


class DocumentVersion(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='versions',
        verbose_name="Dokument"
    )
    version_number = models.CharField(max_length=20, verbose_name="Numer wersji")
    file = models.FileField(upload_to='documents/', verbose_name="Plik")
    is_current = models.BooleanField(
        default=False,
        verbose_name="Wersja obowiązująca",
        help_text="Oznacza wersję jako aktualnie obowiązującą"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Utworzył"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    change_description = models.TextField(blank=True, verbose_name="Opis zmian")

    class Meta:
        verbose_name = "Wersja dokumentu"
        verbose_name_plural = "Wersje dokumentów"
        ordering = ['-created_at']

    def __str__(self):
        current = " [OBOWIĄZUJĄCA]" if self.is_current else ""
        return f"{self.document.title} v{self.version_number}{current}"

    def save(self, *args, **kwargs):
        # Jeśli ta wersja jest oznaczana jako obowiązująca, zdejmij flagę z innych
        if self.is_current:
            DocumentVersion.objects.filter(
                document=self.document, is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class DocumentLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Utworzono'),
        ('updated', 'Zaktualizowano'),
        ('status_changed', 'Zmieniono status'),
        ('version_added', 'Dodano wersję'),
        ('version_set_current', 'Ustawiono wersję obowiązującą'),
        ('access_granted', 'Nadano dostęp'),
        ('access_revoked', 'Cofnięto dostęp'),
        ('iso_linked', 'Powiązano z ISO'),
        ('iso_unlinked', 'Usunięto powiązanie ISO'),
        ('acknowledged', 'Potwierdzono zapoznanie'),
    ]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='logs',
        verbose_name="Dokument"
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Użytkownik")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Czas")
    action = models.CharField(
        max_length=30, choices=ACTION_CHOICES, verbose_name="Akcja"
    )
    description = models.TextField(verbose_name="Opis", blank=True)

    class Meta:
        verbose_name = "Log dokumentu"
        verbose_name_plural = "Logi dokumentów"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.document.title} - {self.get_action_display()} ({self.timestamp})"


class DocumentAccess(models.Model):
    """Model nadawania dostępu do dokumentu poprzez grupy uprawnień"""
    ACCESS_LEVEL_CHOICES = [
        ('view', 'Podgląd'),
        ('edit', 'Edycja'),
        ('manage', 'Zarządzanie'),
    ]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='access_entries',
        verbose_name="Dokument"
    )
    permission_group = models.ForeignKey(
        'core.PermissionGroup', on_delete=models.CASCADE,
        related_name='document_access',
        verbose_name="Grupa uprawnień"
    )
    access_level = models.CharField(
        max_length=10, choices=ACCESS_LEVEL_CHOICES, default='view',
        verbose_name="Poziom dostępu"
    )
    granted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='granted_document_access',
        verbose_name="Nadał"
    )
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name="Data nadania")

    class Meta:
        verbose_name = "Dostęp do dokumentu"
        verbose_name_plural = "Dostępy do dokumentów"
        unique_together = ['document', 'permission_group']
        ordering = ['document', 'permission_group']

    def __str__(self):
        return f"{self.permission_group.name} → {self.document.designation} ({self.get_access_level_display()})"


class DocumentAcknowledgement(models.Model):
    """Model potwierdzenia zapoznania się z dokumentem"""
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='acknowledgements',
        verbose_name="Dokument"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='document_acknowledgements',
        verbose_name="Użytkownik"
    )
    acknowledged_at = models.DateTimeField(auto_now_add=True, verbose_name="Data zapoznania")
    version = models.ForeignKey(
        'DocumentVersion', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Wersja dokumentu"
    )
    notes = models.TextField(blank=True, verbose_name="Uwagi")

    class Meta:
        verbose_name = "Potwierdzenie zapoznania"
        verbose_name_plural = "Potwierdzenia zapoznań"
        unique_together = ['document', 'user', 'version']
        ordering = ['-acknowledged_at']

    def __str__(self):
        return f"{self.user.username} zapoznał się z {self.document.designation}"


class DocumentISOMapping(models.Model):
    """Model powiązania dokumentu z wymaganiem ISO"""
    
    MAPPING_TYPE_CHOICES = [
        ('primary', 'Realizuje głównie'),
        ('supports', 'Wspiera realizację'),
        ('related', 'Powiązany'),
    ]
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='iso_mappings',
        verbose_name="Dokument"
    )
    iso_requirement = models.ForeignKey(
        'dictionary.ISORequirement',
        on_delete=models.CASCADE,
        related_name='document_mappings',
        verbose_name="Wymaganie ISO"
    )
    mapping_type = models.CharField(
        max_length=20,
        choices=MAPPING_TYPE_CHOICES,
        default='primary',
        verbose_name="Typ powiązania"
    )
    section_reference = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Sekcja dokumentu",
        help_text="Która sekcja/rozdział dokumentu odnosi się do wymagania"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Uwagi"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_iso_mappings',
        verbose_name="Utworzył"
    )

    class Meta:
        verbose_name = "Powiązanie dokument-ISO"
        verbose_name_plural = "Powiązania dokument-ISO"
        unique_together = ['document', 'iso_requirement']
        ordering = ['iso_requirement__iso_id']

    def __str__(self):
        return f"{self.document.title} → {self.iso_requirement.iso_id}"
