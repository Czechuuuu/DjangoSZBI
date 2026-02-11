from django.contrib import admin
from .models import Incident, IncidentNote, IncidentLog


class IncidentNoteInline(admin.TabularInline):
    model = IncidentNote
    extra = 0
    fields = ['note_type', 'content', 'author', 'created_at']
    readonly_fields = ['author', 'created_at']


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'status', 'severity', 'category', 'is_serious', 
                    'involves_personal_data', 'reporter', 'assigned_to', 'created_at']
    list_filter = ['status', 'severity', 'category', 'is_serious', 'involves_personal_data']
    search_fields = ['title', 'description', 'circumstances']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'closed_at']
    filter_horizontal = ['affected_assets']
    inlines = [IncidentNoteInline]
    
    fieldsets = (
        ('Zgłoszenie', {
            'fields': ('title', 'description', 'occurred_at', 'circumstances', 
                       'affected_assets', 'reporter')
        }),
        ('Status', {
            'fields': ('status', 'assigned_to')
        }),
        ('Analiza', {
            'fields': ('is_serious', 'involves_personal_data', 'severity', 
                       'category', 'analysis_notes')
        }),
        ('Reakcja', {
            'fields': ('response_actions', 'response_notes')
        }),
        ('Działanie', {
            'fields': ('post_incident_actions',)
        }),
        ('Zakończenie', {
            'fields': ('conclusions', 'closed_at')
        }),
        ('Metadane', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(IncidentNote)
class IncidentNoteAdmin(admin.ModelAdmin):
    list_display = ['incident', 'note_type', 'author', 'created_at']
    list_filter = ['note_type', 'created_at']
    search_fields = ['incident__title', 'content']
    ordering = ['-created_at']


@admin.register(IncidentLog)
class IncidentLogAdmin(admin.ModelAdmin):
    list_display = ['incident', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['incident__title', 'description']
    ordering = ['-timestamp']
    readonly_fields = ['incident', 'user', 'action', 'description', 'timestamp']
