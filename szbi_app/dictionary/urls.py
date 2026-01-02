from django.urls import path
from . import views

app_name = 'dictionary'

urlpatterns = [
    # Wymagania ISO
    path('', views.iso_requirement_list, name='iso_requirement_list'),
    path('dodaj/', views.iso_requirement_create, name='iso_requirement_create'),
    path('macierz/', views.compliance_matrix, name='compliance_matrix'),
    path('<int:pk>/', views.iso_requirement_detail, name='iso_requirement_detail'),
    path('<int:pk>/edytuj/', views.iso_requirement_update, name='iso_requirement_update'),
    path('<int:pk>/usun/', views.iso_requirement_delete, name='iso_requirement_delete'),
]
