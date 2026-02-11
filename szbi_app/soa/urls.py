from django.urls import path
from .views import (
    SoADeclarationListView, SoADeclarationCreateView, SoADeclarationDetailView,
    SoADeclarationUpdateView, SoADeclarationDeleteView,
    soa_change_status, soa_entry_add, soa_entry_edit, soa_entry_delete,
    api_objectives_by_domain, api_requirements_by_objective,
)

app_name = "soa"

urlpatterns = [
    # Lista i CRUD deklaracji
    path('', SoADeclarationListView.as_view(), name='list'),
    path('nowa/', SoADeclarationCreateView.as_view(), name='create'),
    path('<int:pk>/', SoADeclarationDetailView.as_view(), name='detail'),
    path('<int:pk>/edytuj/', SoADeclarationUpdateView.as_view(), name='update'),
    path('<int:pk>/usun/', SoADeclarationDeleteView.as_view(), name='delete'),
    
    # Status
    path('<int:pk>/status/', soa_change_status, name='change_status'),
    
    # Pozycje deklaracji
    path('<int:pk>/pozycja/dodaj/', soa_entry_add, name='entry_add'),
    path('<int:pk>/pozycja/<int:entry_pk>/edytuj/', soa_entry_edit, name='entry_edit'),
    path('<int:pk>/pozycja/<int:entry_pk>/usun/', soa_entry_delete, name='entry_delete'),
    
    # API
    path('api/objectives/<int:domain_id>/', api_objectives_by_domain, name='api_objectives'),
    path('api/requirements/<int:objective_id>/', api_requirements_by_objective, name='api_requirements'),
]
