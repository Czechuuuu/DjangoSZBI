from django.contrib import admin
from .models import AssetCategory, Asset, AssetLog


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'created_at']
    list_filter = ['parent']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['designation', 'name', 'category', 'status', 'criticality', 'owner', 'department']
    list_filter = ['category', 'status', 'criticality', 'department']
    search_fields = ['designation', 'name', 'description']
    ordering = ['designation']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Dane identyfikacyjne', {
            'fields': ('designation', 'name', 'description')
        }),
        ('Klasyfikacja', {
            'fields': ('category', 'status', 'criticality')
        }),
        ('Właściciel i lokalizacja', {
            'fields': ('owner', 'department', 'location')
        }),
        ('Daty i wartość', {
            'fields': ('acquisition_date', 'warranty_expiry', 'value')
        }),
        ('Metadane', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AssetLog)
class AssetLogAdmin(admin.ModelAdmin):
    list_display = ['asset', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['asset__designation', 'asset__name', 'description']
    ordering = ['-timestamp']
    readonly_fields = ['asset', 'user', 'action', 'description', 'timestamp']
