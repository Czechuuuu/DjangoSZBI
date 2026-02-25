from django import forms
from .models import ISOCategory, ISORequirement, ISODomain, ISOObjective, ISOAttachment


class ISOCategoryForm(forms.ModelForm):
    """Formularz kategorii ISO (A, B, C, D)"""
    class Meta:
        model = ISOCategory
        fields = ['code', 'name', 'description']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. A, B, C'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa kategorii'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Opcjonalny opis kategorii'
            }),
        }


class ISODomainForm(forms.ModelForm):
    """Formularz domeny ISO"""
    class Meta:
        model = ISODomain
        fields = ['category', 'code', 'name']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. A.5'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa domeny'
            }),
        }


class ISOObjectiveForm(forms.ModelForm):
    """Formularz celu wymagań ISO"""
    class Meta:
        model = ISOObjective
        fields = ['domain', 'code', 'name', 'objective_text']
        widgets = {
            'domain': forms.Select(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. A.5.1'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa celu wymagań'
            }),
            'objective_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Cel stosowania wymagań...'
            }),
        }


class ISORequirementForm(forms.ModelForm):
    """Formularz do tworzenia i edycji wymagań ISO"""
    
    class Meta:
        model = ISORequirement
        fields = [
            'objective',
            'iso_id',
            'name',
            'description',
            'is_applied',
            'implementation_method',
            'notes',
        ]
        widgets = {
            'objective': forms.Select(attrs={'class': 'form-control'}),
            'iso_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. A.5.1.1'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa wymagania'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Opis wymagania'
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


class ISOAttachmentForm(forms.ModelForm):
    """Formularz dodawania pliku do wymagania ISO"""
    class Meta:
        model = ISOAttachment
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tytuł lub opis pliku'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
