from django import forms
from .models import Document, DocumentISOMapping
from dictionary.models import ISORequirement


class DocumentForm(forms.ModelForm):
    """Formularz do tworzenia i edycji dokumentów"""
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tytuł dokumentu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Opis dokumentu'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


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
