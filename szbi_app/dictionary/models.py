from django.db import models
from django.contrib.auth.models import User


class ISODomain(models.Model):
    """
    Domena ISO 27001 Załącznik A.
    Np. A.5 'Polityki bezpieczeństwa informacji', A.6 'Organizacja bezpieczeństwa informacji'
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Kod domeny",
        help_text="Np. A.5, A.6, A.7"
    )
    name = models.CharField(
        max_length=300,
        verbose_name="Nazwa domeny"
    )
    
    class Meta:
        verbose_name = "Domena ISO"
        verbose_name_plural = "Domeny ISO"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} {self.name}"


class ISOObjective(models.Model):
    """
    Cel stosowania wymagań w ramach domeny.
    Np. A.5.1 'Kierunki bezpieczeństwa informacji określane przez kierownictwo'
    z celem: 'Zapewnienie przez kierownictwo wytycznych i wsparcia...'
    """
    domain = models.ForeignKey(
        ISODomain,
        on_delete=models.CASCADE,
        related_name='objectives',
        verbose_name="Domena"
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Kod celu",
        help_text="Np. A.5.1, A.6.1"
    )
    name = models.CharField(
        max_length=500,
        verbose_name="Nazwa celu"
    )
    objective_text = models.TextField(
        blank=True,
        verbose_name="Cel stosowania wymagań",
        help_text="Treść celu opisującego dlaczego stosujemy wymagania z tej grupy"
    )
    
    class Meta:
        verbose_name = "Cel wymagań ISO"
        verbose_name_plural = "Cele wymagań ISO"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} {self.name}"


class ISORequirement(models.Model):
    """
    Pojedyncze wymaganie ISO 27001.
    Np. A.5.1.1 'Polityki bezpieczeństwa informacji'
    """
    
    STATUS_CHOICES = [
        ('yes', 'Tak'),
        ('no', 'Nie'),
        ('partial', 'Częściowo'),
        ('not_applicable', 'Nie dotyczy'),
    ]
    
    objective = models.ForeignKey(
        ISOObjective,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name="Cel wymagań",
        null=True,
        blank=True,
    )
    iso_id = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="ID wymagania",
        help_text="Identyfikator zgodny z ISO 27001, np. A.5.1.1"
    )
    name = models.CharField(
        max_length=500, 
        verbose_name="Nazwa wymagania"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Opis wymagania"
    )
    is_applied = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='no',
        verbose_name="Czy stosujemy?"
    )
    implementation_method = models.TextField(
        blank=True,
        verbose_name="Sposób realizacji / Dokument referencyjny",
        help_text="Opis sposobu realizacji wymagania lub odniesienie do dokumentu"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Uwagi"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Data utworzenia"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Data modyfikacji"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_iso_requirements',
        verbose_name="Utworzył"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_iso_requirements',
        verbose_name="Zmodyfikował"
    )

    class Meta:
        verbose_name = "Wymaganie ISO"
        verbose_name_plural = "Wymagania ISO"
        ordering = ['iso_id']

    def __str__(self):
        return f"{self.iso_id} - {self.name}"
    
    def get_domain(self):
        """Zwraca domenę, jeśli przypisano cel"""
        if self.objective:
            return self.objective.domain
        return None


class ISOAttachment(models.Model):
    """Plik załącznika powiązany z wymaganiem ISO"""
    requirement = models.ForeignKey(
        ISORequirement,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="Wymaganie"
    )
    file = models.FileField(
        upload_to='iso_attachments/%Y/%m/',
        verbose_name="Plik"
    )
    title = models.CharField(
        max_length=300,
        verbose_name="Tytuł / opis pliku"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data dodania"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Dodał"
    )
    
    class Meta:
        verbose_name = "Załącznik ISO"
        verbose_name_plural = "Załączniki ISO"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title
    
    def get_filename(self):
        import os
        return os.path.basename(self.file.name)
