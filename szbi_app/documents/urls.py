from django.urls import path
from .views import (
    DocumentListView, DocumentCreateView, DocumentDetailView, DocumentUpdateView,
    document_add_iso_mapping, document_remove_iso_mapping
)

app_name = "documents"

urlpatterns = [
    path('', DocumentListView.as_view(), name='list'),
    path('new/', DocumentCreateView.as_view(), name='create'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='detail'),
    path('<int:pk>/edytuj/', DocumentUpdateView.as_view(), name='update'),
    path('<int:pk>/iso/dodaj/', document_add_iso_mapping, name='add_iso_mapping'),
    path('<int:pk>/iso/<int:mapping_pk>/usun/', document_remove_iso_mapping, name='remove_iso_mapping'),
]
