from django.contrib import admin
from .models import SoADeclaration, SoAEntry, SoALog


class SoAEntryInline(admin.TabularInline):
    model = SoAEntry
    extra = 0
    fields = ['requirement', 'applicability', 'responsible_person', 'justification']
    raw_id_fields = ['requirement', 'responsible_person']


@admin.register(SoADeclaration)
class SoADeclarationAdmin(admin.ModelAdmin):
    list_display = ['designation', 'name', 'version', 'status', 'owner', 'updated_at']
    list_filter = ['status', 'owner']
    search_fields = ['designation', 'name', 'description']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [SoAEntryInline]
    
    fieldsets = (
        ('Dane podstawowe', {
            'fields': ('designation', 'name', 'description', 'version')
        }),
        ('Status', {
            'fields': ('status', 'effective_date')
        }),
        ('Właściciel', {
            'fields': ('owner',)
        }),
        ('Metadane', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SoAEntry)
class SoAEntryAdmin(admin.ModelAdmin):
    list_display = ['declaration', 'requirement', 'applicability', 'responsible_person']
    list_filter = ['declaration', 'applicability']
    search_fields = ['requirement__iso_id', 'requirement__name', 'justification']
    raw_id_fields = ['declaration', 'requirement', 'responsible_person']


@admin.register(SoALog)
class SoALogAdmin(admin.ModelAdmin):
    list_display = ['declaration', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['declaration__designation', 'description']
    ordering = ['-timestamp']
    readonly_fields = ['declaration', 'user', 'action', 'description', 'timestamp']
