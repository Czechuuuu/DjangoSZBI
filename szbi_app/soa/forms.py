from django import forms
from .models import SoADeclaration, SoAEntry
from dictionary.models import ISODomain, ISOObjective, ISORequirement


class SoADeclarationForm(forms.ModelForm):
    """Formularz tworzenia i edycji deklaracji stosowania"""
    
    class Meta:
        model = SoADeclaration
        fields = ['designation', 'name', 'description', 'version', 'effective_date']
        widgets = {
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. SOA-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa deklaracji'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Opis deklaracji'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class SoAEntryForm(forms.ModelForm):
    """Formularz dodawania/edycji pozycji w deklaracji"""
    
    # Pomocnicze pole do wyboru domeny
    domain = forms.ModelChoiceField(
        queryset=ISODomain.objects.all(),
        required=False,
        label="Domena ISO",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_domain'})
    )
    
    # Pomocnicze pole do wyboru celu
    objective = forms.ModelChoiceField(
        queryset=ISOObjective.objects.all(),
        required=False,
        label="Cel wymagań",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_objective'})
    )
    
    class Meta:
        model = SoAEntry
        fields = ['requirement', 'applicability', 'responsible_person', 
                  'related_documents', 'justification', 'additional_description']
        widgets = {
            'requirement': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_requirement'
            }),
            'applicability': forms.Select(attrs={
                'class': 'form-control'
            }),
            'responsible_person': forms.Select(attrs={
                'class': 'form-control'
            }),
            'related_documents': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5'
            }),
            'justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Uzasadnienie stosowania/niestosowania wymagania'
            }),
            'additional_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dodatkowy opis (opcjonalnie)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Jeśli edytujemy istniejący wpis, ustaw domyślne wartości domain i objective
        if self.instance and self.instance.pk:
            req = self.instance.requirement
            if req and req.objective:
                self.fields['objective'].initial = req.objective
                self.fields['domain'].initial = req.objective.domain


class SoAStatusForm(forms.Form):
    """Formularz zmiany statusu deklaracji"""
    
    STATUS_CHOICES = [
        ('draft', 'Wersja robocza'),
        ('review', 'W przeglądzie'),
        ('approved', 'Zatwierdzona'),
        ('current', 'Obowiązująca'),
        ('archived', 'Zarchiwizowana'),
    ]
    
    new_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Nowy status"
    )
