from django.db import models
from django.contrib.auth.models import User


class ISORequirement(models.Model):
    """Model wymagań ISO 27001 - zabezpieczenia"""
    
    STATUS_CHOICES = [
        ('yes', 'Tak'),
        ('no', 'Nie'),
        ('partial', 'Częściowo'),
        ('not_applicable', 'Nie dotyczy'),
    ]
    
    iso_id = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="ID zabezpieczenia",
        help_text="Identyfikator zgodny z ISO 27001, np. A.5.1.1"
    )
    name = models.CharField(
        max_length=500, 
        verbose_name="Nazwa zabezpieczenia"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Opis zabezpieczenia"
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
        help_text="Opis sposobu realizacji zabezpieczenia lub odniesienie do dokumentu"
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Kategoria",
        help_text="Kategoria zabezpieczenia, np. 'A.5 Polityki bezpieczeństwa'"
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
    
    def get_is_applied_display_class(self):
        """Zwraca klasę CSS dla statusu"""
        return {
            'yes': 'status-yes',
            'no': 'status-no',
            'partial': 'status-partial',
            'not_applicable': 'status-na',
        }.get(self.is_applied, '')
