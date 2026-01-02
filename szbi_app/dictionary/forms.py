from django import forms
from .models import ISORequirement


class ISORequirementForm(forms.ModelForm):
    """Formularz do tworzenia i edycji wymagań ISO"""
    
    class Meta:
        model = ISORequirement
        fields = [
            'iso_id',
            'name',
            'description',
            'category',
            'is_applied',
            'implementation_method',
            'notes',
        ]
        widgets = {
            'iso_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. A.5.1.1'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa zabezpieczenia'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Opis zabezpieczenia'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. A.5 Polityki bezpieczeństwa'
            }),
            'is_applied': forms.Select(attrs={
                'class': 'form-control'
            }),
            'implementation_method': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Sposób realizacji lub odniesienie do dokumentu referencyjnego'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Dodatkowe uwagi'
            }),
        }
