from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Organizacja (jedna główna)
    path('organizacja/', views.organization_structure, name='organization_structure'),
    path('organizacja/edytuj/', views.organization_edit, name='organization_edit'),
    
    # Działy
    path('dzial/dodaj/', views.department_create, name='department_create'),
    path('dzial/<int:pk>/edytuj/', views.department_update, name='department_update'),
    path('dzial/<int:pk>/usun/', views.department_delete, name='department_delete'),
    path('dzial/<int:pk>/uprawnienia/', views.department_permissions, name='department_permissions'),
    
    # Stanowiska
    path('dzial/<int:dept_pk>/stanowisko/dodaj/', views.position_create_in_dept, name='position_create_in_dept'),
    path('stanowisko/<int:pk>/edytuj/', views.position_update, name='position_update'),
    path('stanowisko/<int:pk>/usun/', views.position_delete, name='position_delete'),
    path('stanowisko/<int:pk>/uprawnienia/', views.position_permissions, name='position_permissions'),
    
    # Uprawnienia
    path('uprawnienia/', views.permission_list, name='permission_list'),
    path('uprawnienia/dodaj/', views.permission_create, name='permission_create'),
    path('uprawnienia/<int:pk>/edytuj/', views.permission_update, name='permission_update'),
    path('uprawnienia/<int:pk>/usun/', views.permission_delete, name='permission_delete'),
    
    # Grupy uprawnień
    path('uprawnienia/grupy/dodaj/', views.permission_group_create, name='permission_group_create'),
    path('uprawnienia/grupy/<int:pk>/edytuj/', views.permission_group_update, name='permission_group_update'),
    path('uprawnienia/grupy/<int:pk>/usun/', views.permission_group_delete, name='permission_group_delete'),
    
    # Pracownicy
    path('pracownicy/', views.employee_list, name='employee_list'),
    path('pracownicy/dodaj/', views.employee_create, name='employee_create'),
    path('pracownicy/<int:pk>/edytuj/', views.employee_update, name='employee_update'),
    path('pracownicy/<int:pk>/usun/', views.employee_delete, name='employee_delete'),
    path('pracownicy/<int:pk>/uprawnienia/', views.employee_permissions, name='employee_permissions'),
]
