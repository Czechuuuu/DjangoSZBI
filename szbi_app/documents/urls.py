from django.urls import path
from .views import (
    DocumentListView, DocumentCreateView, DocumentDetailView, DocumentUpdateView,
    SharedWithMeListView,
    document_add_iso_mapping, document_remove_iso_mapping,
    document_add_version, document_set_current_version, document_download_version,
    document_workflow_transition,
    document_grant_access, document_revoke_access,
    document_acknowledge,
)

app_name = "documents"

urlpatterns = [
    # Lista i CRUD
    path('', DocumentListView.as_view(), name='list'),
    path('new/', DocumentCreateView.as_view(), name='create'),
    path('udostepnione/', SharedWithMeListView.as_view(), name='shared_with_me'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='detail'),
    path('<int:pk>/edytuj/', DocumentUpdateView.as_view(), name='update'),
    
    # Wersje
    path('<int:pk>/wersja/dodaj/', document_add_version, name='add_version'),
    path('<int:pk>/wersja/<int:version_pk>/ustaw/', document_set_current_version, name='set_current_version'),
    path('<int:pk>/wersja/<int:version_pk>/pobierz/', document_download_version, name='download_version'),
    
    # Workflow
    path('<int:pk>/workflow/', document_workflow_transition, name='workflow_transition'),
    
    # Dostęp
    path('<int:pk>/dostep/nadaj/', document_grant_access, name='grant_access'),
    path('<int:pk>/dostep/<int:access_pk>/cofnij/', document_revoke_access, name='revoke_access'),
    
    # Zapoznanie
    path('<int:pk>/zapoznanie/', document_acknowledge, name='acknowledge'),
    
    # Powiązania ISO
    path('<int:pk>/iso/dodaj/', document_add_iso_mapping, name='add_iso_mapping'),
    path('<int:pk>/iso/<int:mapping_pk>/usun/', document_remove_iso_mapping, name='remove_iso_mapping'),
]
