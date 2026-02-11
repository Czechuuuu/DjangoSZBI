from django import forms
from .models import Asset, AssetCategory


class AssetCategoryForm(forms.ModelForm):
    """Formularz kategorii aktywów"""
    
    class Meta:
        model = AssetCategory
        fields = ['code', 'name', 'description', 'parent']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. HW, SW, DATA'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa kategorii'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Opis kategorii'
            }),
            'parent': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class AssetForm(forms.ModelForm):
    """Formularz tworzenia i edycji aktywów"""
    
    class Meta:
        model = Asset
        fields = [
            'designation', 'name', 'description', 'category',
            'status', 'criticality',
            'owner', 'department', 'location',
            'acquisition_date', 'warranty_expiry', 'value',
        ]
        widgets = {
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. HW-001, SW-015'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa aktywa'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Opis aktywa'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'criticality': forms.Select(attrs={
                'class': 'form-control'
            }),
            'owner': forms.Select(attrs={
                'class': 'form-control'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'np. Budynek A, Pokój 101'
            }),
            'acquisition_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
        }
