from django.urls import path
from .views import (
    MyIncidentsListView, AllIncidentsListView, IncidentReportView, IncidentDetailView,
    IncidentDeleteView,
    incident_advance_status, incident_update_analysis, incident_update_response,
    incident_update_action, incident_close, incident_add_note,
)

app_name = "incidents"

urlpatterns = [
    # Listy
    path('', AllIncidentsListView.as_view(), name='list'),
    path('moje/', MyIncidentsListView.as_view(), name='my_list'),
    
    # Zgłaszanie
    path('zglos/', IncidentReportView.as_view(), name='report'),
    
    # Szczegóły
    path('<int:pk>/', IncidentDetailView.as_view(), name='detail'),
    path('<int:pk>/usun/', IncidentDeleteView.as_view(), name='delete'),
    
    # Workflow
    path('<int:pk>/dalej/', incident_advance_status, name='advance_status'),
    
    # Aktualizacje faz
    path('<int:pk>/analiza/', incident_update_analysis, name='update_analysis'),
    path('<int:pk>/reakcja/', incident_update_response, name='update_response'),
    path('<int:pk>/dzialanie/', incident_update_action, name='update_action'),
    path('<int:pk>/zamknij/', incident_close, name='close'),
    
    # Notatki
    path('<int:pk>/notatka/', incident_add_note, name='add_note'),
]
