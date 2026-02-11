from django.db import models
from django.contrib.auth.models import User
from core.models import Employee
from assets.models import Asset


class Incident(models.Model):
    """Model incydentu bezpieczeństwa"""
    
    STATUS_CHOICES = [
        ('reported', 'Zgłoszony'),
        ('analysis', 'Analiza'),
        ('response', 'Reakcja'),
        ('action', 'Działanie'),
        ('closed', 'Zakończony'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Niski'),
        ('medium', 'Średni'),
        ('high', 'Wysoki'),
        ('critical', 'Krytyczny'),
    ]
    
    CATEGORY_CHOICES = [
        ('malware', 'Złośliwe oprogramowanie'),
        ('phishing', 'Phishing'),
        ('unauthorized_access', 'Nieautoryzowany dostęp'),
        ('data_leak', 'Wyciek danych'),
        ('hardware_failure', 'Awaria sprzętu'),
        ('software_failure', 'Awaria oprogramowania'),
        ('human_error', 'Błąd ludzki'),
        ('physical_security', 'Bezpieczeństwo fizyczne'),
        ('other', 'Inny'),
    ]
    
    # Podstawowe dane zgłoszenia
    title = models.CharField(
        max_length=255,
        verbose_name="Temat"
    )
    description = models.TextField(
        verbose_name="Opis incydentu"
    )
    occurred_at = models.DateTimeField(
        verbose_name="Data i czas wystąpienia"
    )
    circumstances = models.TextField(
        verbose_name="Okoliczności",
        help_text="Opis okoliczności w jakich doszło do incydentu"
    )
    
    # Powiązanie z aktywami
    affected_assets = models.ManyToManyField(
        Asset,
        blank=True,
        related_name='incidents',
        verbose_name="Dotknięte aktywa"
    )
    
    # Status workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='reported',
        verbose_name="Status"
    )
    
    # Analiza (wypełniane w fazie analizy)
    is_serious = models.BooleanField(
        default=False,
        verbose_name="Poważny incydent"
    )
    involves_personal_data = models.BooleanField(
        default=False,
        verbose_name="Dotyczy danych osobowych"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        null=True,
        blank=True,
        verbose_name="Klasyfikacja"
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        null=True,
        blank=True,
        verbose_name="Kategoria"
    )
    analysis_notes = models.TextField(
        blank=True,
        verbose_name="Notatki z analizy"
    )
    
    # Reakcja (wypełniane w fazie reakcji)
    response_actions = models.TextField(
        blank=True,
        verbose_name="Podjęte działania",
        help_text="Jakie akcje zostały podjęte w reakcji na incydent"
    )
    response_notes = models.TextField(
        blank=True,
        verbose_name="Notatki z reakcji"
    )
    
    # Działanie (wypełniane w fazie działania)
    post_incident_actions = models.TextField(
        blank=True,
        verbose_name="Działania po incydencie",
        help_text="Akcje podjęte po incydencie (naprawcze, zapobiegawcze)"
    )
    
    # Zakończenie
    conclusions = models.TextField(
        blank=True,
        verbose_name="Wnioski"
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data zamknięcia"
    )
    
    # Osoby
    reporter = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='reported_incidents',
        verbose_name="Zgłaszający"
    )
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents',
        verbose_name="Przypisany do"
    )
    
    # Metadane
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data zgłoszenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Incydent"
        verbose_name_plural = "Incydenty"
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} {self.title} ({self.get_status_display()})"
    
    def get_next_status(self):
        """Zwraca następny status w workflow"""
        workflow = ['reported', 'analysis', 'response', 'action', 'closed']
        try:
            idx = workflow.index(self.status)
            if idx < len(workflow) - 1:
                return workflow[idx + 1]
        except ValueError:
            pass
        return None


class IncidentNote(models.Model):
    """Notatki/komentarze do incydentu"""
    
    NOTE_TYPE_CHOICES = [
        ('comment', 'Komentarz'),
        ('analysis', 'Analiza'),
        ('response', 'Reakcja'),
        ('action', 'Działanie'),
        ('info', 'Dodatkowe informacje'),
    ]
    
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="Incydent"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Autor"
    )
    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPE_CHOICES,
        default='comment',
        verbose_name="Typ"
    )
    content = models.TextField(
        verbose_name="Treść"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Notatka do incydentu"
        verbose_name_plural = "Notatki do incydentów"
        ordering = ['-created_at']

    def __str__(self):
        return f"Notatka do #{self.incident.pk} ({self.get_note_type_display()})"


class IncidentLog(models.Model):
    """Historia zmian incydentu"""
    
    ACTION_CHOICES = [
        ('created', 'Zgłoszono'),
        ('updated', 'Zaktualizowano'),
        ('status_changed', 'Zmieniono status'),
        ('assigned', 'Przypisano'),
        ('note_added', 'Dodano notatkę'),
        ('closed', 'Zamknięto'),
    ]
    
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name="Incydent"
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
        verbose_name = "Dziennik incydentu"
        verbose_name_plural = "Dziennik incydentów"
        ordering = ['-timestamp']

    def __str__(self):
        return f"#{self.incident.pk}: {self.get_action_display()} ({self.timestamp})"
