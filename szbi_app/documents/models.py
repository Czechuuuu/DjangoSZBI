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

    title = models.CharField(max_length=255, verbose_name="Tytuł")
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
        return f"{self.title} ({self.get_status_display()})"
    
    def get_iso_requirements(self):
        """Zwraca listę powiązanych wymagań ISO"""
        return self.iso_mappings.select_related('iso_requirement').all()
    
    def get_iso_requirements_count(self):
        """Zwraca liczbę powiązanych wymagań ISO"""
        return self.iso_mappings.count()


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20)
    file = models.FileField(upload_to='documents/')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    change_description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"


class DocumentLog(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return f"{self.document.title} - {self.action}"


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
