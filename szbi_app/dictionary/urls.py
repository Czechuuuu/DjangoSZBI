from django.urls import path
from . import views

app_name = 'dictionary'

urlpatterns = [
    # Drzewo ISO (widok główny)
    path('', views.iso_tree, name='iso_tree'),
    
    # Domeny
    path('domena/dodaj/', views.domain_create, name='domain_create'),
    path('domena/<int:pk>/edytuj/', views.domain_update, name='domain_update'),
    path('domena/<int:pk>/usun/', views.domain_delete, name='domain_delete'),
    
    # Cele wymagań
    path('cel/dodaj/', views.objective_create, name='objective_create'),
    path('cel/dodaj/<int:domain_pk>/', views.objective_create, name='objective_create_for_domain'),
    path('cel/<int:pk>/edytuj/', views.objective_update, name='objective_update'),
    path('cel/<int:pk>/usun/', views.objective_delete, name='objective_delete'),
    
    # Wymagania ISO
    path('wymagania/', views.iso_requirement_list, name='iso_requirement_list'),
    path('wymagania/dodaj/', views.iso_requirement_create, name='iso_requirement_create'),
    path('wymagania/dodaj/<int:objective_pk>/', views.iso_requirement_create, name='iso_requirement_create_for_objective'),
    path('wymagania/<int:pk>/', views.iso_requirement_detail, name='iso_requirement_detail'),
    path('wymagania/<int:pk>/edytuj/', views.iso_requirement_update, name='iso_requirement_update'),
    path('wymagania/<int:pk>/usun/', views.iso_requirement_delete, name='iso_requirement_delete'),
    
    # Załączniki
    path('wymagania/<int:requirement_pk>/plik/dodaj/', views.attachment_add, name='attachment_add'),
    path('plik/<int:pk>/usun/', views.attachment_delete, name='attachment_delete'),
    path('plik/<int:pk>/pobierz/', views.attachment_download, name='attachment_download'),
]
