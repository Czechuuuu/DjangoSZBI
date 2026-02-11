from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count

from .models import Asset, AssetCategory, AssetLog
from .forms import AssetForm, AssetCategoryForm
from core.mixins import (
    SZBIPermissionRequiredMixin,
    PERM_ASSETS_ADMIN, PERM_ASSETS_OWNER, PERM_ASSETS_VIEW
)

# Uprawnienia do przeglądania aktywów
ASSETS_VIEW_PERMISSIONS = [PERM_ASSETS_ADMIN, PERM_ASSETS_OWNER, PERM_ASSETS_VIEW]
# Uprawnienia do edycji aktywów
ASSETS_EDIT_PERMISSIONS = [PERM_ASSETS_ADMIN, PERM_ASSETS_OWNER]


def _log_action(asset, user, action, description=""):
    """Helper do logowania akcji na aktywie"""
    AssetLog.objects.create(
        asset=asset,
        user=user,
        action=action,
        description=description
    )


# ============== KATEGORIE AKTYWÓW ==============

class AssetCategoryListView(SZBIPermissionRequiredMixin, ListView):
    model = AssetCategory
    template_name = "assets/category_list.html"
    context_object_name = "categories"
    szbi_permission_required = ASSETS_VIEW_PERMISSIONS
    
    def get_queryset(self):
        return AssetCategory.objects.annotate(
            assets_count=Count('assets')
        ).select_related('parent').all()


class AssetCategoryCreateView(SZBIPermissionRequiredMixin, CreateView):
    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = "assets/category_form.html"
    success_url = reverse_lazy('assets:category_list')
    szbi_permission_required = [PERM_ASSETS_ADMIN]

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Kategoria "{self.object.name}" została utworzona.')
        return response


class AssetCategoryUpdateView(SZBIPermissionRequiredMixin, UpdateView):
    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = "assets/category_form.html"
    success_url = reverse_lazy('assets:category_list')
    szbi_permission_required = [PERM_ASSETS_ADMIN]

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Kategoria "{self.object.name}" została zaktualizowana.')
        return response


class AssetCategoryDeleteView(SZBIPermissionRequiredMixin, DeleteView):
    model = AssetCategory
    template_name = "assets/category_confirm_delete.html"
    success_url = reverse_lazy('assets:category_list')
    szbi_permission_required = [PERM_ASSETS_ADMIN]

    def form_valid(self, form):
        category_name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f'Kategoria "{category_name}" została usunięta.')
        return response


# ============== AKTYWA ==============

class AssetListView(SZBIPermissionRequiredMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    szbi_permission_required = ASSETS_VIEW_PERMISSIONS
    
    def get_queryset(self):
        qs = Asset.objects.select_related('category', 'owner', 'department').all()
        
        # Filtrowanie
        category = self.request.GET.get('category')
        status = self.request.GET.get('status')
        criticality = self.request.GET.get('criticality')
        search = self.request.GET.get('q')
        
        if category:
            qs = qs.filter(category_id=category)
        if status:
            qs = qs.filter(status=status)
        if criticality:
            qs = qs.filter(criticality=criticality)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(designation__icontains=search) |
                Q(description__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(inventory_number__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = AssetCategory.objects.all()
        context['status_choices'] = Asset.STATUS_CHOICES
        context['criticality_choices'] = Asset.CRITICALITY_CHOICES
        context['current_category'] = self.request.GET.get('category', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_criticality'] = self.request.GET.get('criticality', '')
        context['current_search'] = self.request.GET.get('q', '')
        return context


class AssetCreateView(SZBIPermissionRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"
    success_url = reverse_lazy('assets:list')
    szbi_permission_required = ASSETS_EDIT_PERMISSIONS

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        _log_action(self.object, self.request.user, 'created',
                    f'Utworzono aktywo [{self.object.designation}] {self.object.name}')
        messages.success(self.request, f'Aktywo "{self.object.designation}" zostało utworzone.')
        return response


class AssetDetailView(SZBIPermissionRequiredMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"
    szbi_permission_required = ASSETS_VIEW_PERMISSIONS
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = self.object.logs.select_related('user').all()[:20]
        return context


class AssetUpdateView(SZBIPermissionRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = "assets/asset_form.html"
    szbi_permission_required = ASSETS_EDIT_PERMISSIONS

    def get_success_url(self):
        return reverse_lazy('assets:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        old_status = Asset.objects.get(pk=self.object.pk).status
        response = super().form_valid(form)
        
        if old_status != self.object.status:
            _log_action(self.object, self.request.user, 'status_changed',
                        f'Zmieniono status z "{old_status}" na "{self.object.status}"')
        else:
            _log_action(self.object, self.request.user, 'updated',
                        f'Zaktualizowano aktywo [{self.object.designation}]')
        
        messages.success(self.request, f'Aktywo "{self.object.designation}" zostało zaktualizowane.')
        return response


class AssetDeleteView(SZBIPermissionRequiredMixin, DeleteView):
    model = Asset
    template_name = "assets/asset_confirm_delete.html"
    success_url = reverse_lazy('assets:list')
    szbi_permission_required = [PERM_ASSETS_ADMIN]

    def form_valid(self, form):
        asset_designation = self.object.designation
        response = super().form_valid(form)
        messages.success(self.request, f'Aktywo "{asset_designation}" zostało usunięte.')
        return response
