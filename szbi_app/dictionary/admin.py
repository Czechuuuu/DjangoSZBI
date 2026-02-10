from django.contrib import admin
from .models import ISODomain, ISOObjective, ISORequirement, ISOAttachment


@admin.register(ISODomain)
class ISODomainAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    ordering = ['code']


@admin.register(ISOObjective)
class ISOObjectiveAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'domain']
    list_filter = ['domain']
    ordering = ['code']


class ISOAttachmentInline(admin.TabularInline):
    model = ISOAttachment
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']


@admin.register(ISORequirement)
class ISORequirementAdmin(admin.ModelAdmin):
    list_display = ['iso_id', 'name', 'objective', 'is_applied', 'updated_at']
    list_filter = ['is_applied', 'objective__domain', 'created_at', 'updated_at']
    search_fields = ['iso_id', 'name', 'description', 'implementation_method']
    ordering = ['iso_id']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [ISOAttachmentInline]
    
    fieldsets = (
        ('Identyfikacja', {
            'fields': ('iso_id', 'name', 'objective', 'description')
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
