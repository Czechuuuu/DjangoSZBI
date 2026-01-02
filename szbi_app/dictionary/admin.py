from django.contrib import admin
from .models import ISORequirement


@admin.register(ISORequirement)
class ISORequirementAdmin(admin.ModelAdmin):
    list_display = ['iso_id', 'name', 'category', 'is_applied', 'updated_at']
    list_filter = ['is_applied', 'category', 'created_at', 'updated_at']
    search_fields = ['iso_id', 'name', 'description', 'implementation_method']
    ordering = ['iso_id']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Identyfikacja', {
            'fields': ('iso_id', 'name', 'category', 'description')
        }),
        ('Status realizacji', {
            'fields': ('is_applied', 'implementation_method', 'notes')
        }),
        ('Metadane', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
