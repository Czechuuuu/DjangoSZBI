from django import forms
from django.contrib.auth.models import User
from .models import Document, DocumentISOMapping, DocumentVersion, DocumentAccess
from dictionary.models import ISORequirement
from core.models import PermissionGroup


class DocumentForm(forms.ModelForm):
    """Formularz do tworzenia i edycji dokumentów"""
    
    class Meta:
        model = Document
        fields = ['designation', 'title', 'document_type', 'description']
        widgets = {
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. POL-001, PROC-003'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tytuł dokumentu'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Opis dokumentu'
            }),
        }


class DocumentVersionForm(forms.ModelForm):
    """Formularz dodawania nowej wersji dokumentu"""
    
    mark_as_current = forms.BooleanField(
        required=False,
        initial=False,
        label="Oznacz jako wersję obowiązującą",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = DocumentVersion
        fields = ['version_number', 'file', 'change_description']
        widgets = {
            'version_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. 1.0, 2.1'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'change_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Opis zmian w tej wersji'
            }),
        }


class DocumentAccessForm(forms.ModelForm):
    """Formularz nadawania dostępu do dokumentu przez grupę uprawnień"""
    
    permission_group = forms.ModelChoiceField(
        queryset=PermissionGroup.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Grupa uprawnień",
        empty_label="-- Wybierz grupę uprawnień --"
    )
    
    class Meta:
        model = DocumentAccess
        fields = ['permission_group', 'access_level']
        widgets = {
            'access_level': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class WorkflowTransitionForm(forms.Form):
    """Formularz zmiany statusu dokumentu (workflow)"""
    
    new_status = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Nowy status"
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Komentarz do zmiany statusu (opcjonalnie)'
        }),
        label="Komentarz"
    )
    
    def __init__(self, *args, document=None, **kwargs):
        super().__init__(*args, **kwargs)
        if document:
            allowed = document.get_allowed_transitions()
            self.fields['new_status'].choices = [
                (s, dict(Document.STATUS).get(s, s)) for s in allowed
            ]


class DocumentISOMappingForm(forms.ModelForm):
    """Formularz do powiązania dokumentu z wymaganiem ISO"""
    
    iso_requirement = forms.ModelChoiceField(
        queryset=ISORequirement.objects.all().order_by('iso_id'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Wymaganie ISO",
        empty_label="-- Wybierz wymaganie ISO --"
    )
    
    class Meta:
        model = DocumentISOMapping
        fields = ['iso_requirement', 'mapping_type', 'section_reference', 'notes']
        widgets = {
            'mapping_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'section_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. Rozdział 3.2, Sekcja A'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Dodatkowe uwagi dotyczące powiązania'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zmień wyświetlanie wymagań ISO na bardziej czytelne
        self.fields['iso_requirement'].label_from_instance = lambda obj: f"{obj.iso_id} - {obj.name[:60]}{'...' if len(obj.name) > 60 else ''}"
