from django import forms
from .models import Incident, IncidentNote


class IncidentReportForm(forms.ModelForm):
    """Formularz zgłaszania incydentu (dla zwykłych użytkowników)"""
    
    class Meta:
        model = Incident
        fields = ['title', 'description', 'occurred_at', 'circumstances', 'affected_assets']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Krótki opis incydentu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Szczegółowy opis incydentu'
            }),
            'occurred_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'circumstances': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'W jakich okolicznościach doszło do incydentu?'
            }),
            'affected_assets': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5'
            }),
        }


class IncidentAnalysisForm(forms.ModelForm):
    """Formularz analizy incydentu"""
    
    class Meta:
        model = Incident
        fields = ['is_serious', 'involves_personal_data', 'severity', 'category', 'analysis_notes', 'assigned_to']
        widgets = {
            'is_serious': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'involves_personal_data': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'severity': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'analysis_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notatki z analizy'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class IncidentResponseForm(forms.ModelForm):
    """Formularz reakcji na incydent"""
    
    class Meta:
        model = Incident
        fields = ['response_actions', 'response_notes']
        widgets = {
            'response_actions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Jakie działania zostały podjęte?'
            }),
            'response_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dodatkowe notatki'
            }),
        }


class IncidentActionForm(forms.ModelForm):
    """Formularz działań po incydencie"""
    
    class Meta:
        model = Incident
        fields = ['post_incident_actions']
        widgets = {
            'post_incident_actions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Działania naprawcze i zapobiegawcze'
            }),
        }


class IncidentCloseForm(forms.ModelForm):
    """Formularz zamykania incydentu"""
    
    class Meta:
        model = Incident
        fields = ['conclusions']
        widgets = {
            'conclusions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Wnioski z incydentu'
            }),
        }


class IncidentNoteForm(forms.ModelForm):
    """Formularz dodawania notatki do incydentu"""
    
    class Meta:
        model = IncidentNote
        fields = ['note_type', 'content']
        widgets = {
            'note_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Treść notatki'
            }),
        }
