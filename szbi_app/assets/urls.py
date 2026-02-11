from django.urls import path
from .views import (
    AssetListView, AssetCreateView, AssetDetailView, AssetUpdateView, AssetDeleteView,
    AssetCategoryListView, AssetCategoryCreateView, AssetCategoryUpdateView, AssetCategoryDeleteView,
)

app_name = "assets"

urlpatterns = [
    # Lista aktywów
    path('', AssetListView.as_view(), name='list'),
    path('nowy/', AssetCreateView.as_view(), name='create'),
    path('<int:pk>/', AssetDetailView.as_view(), name='detail'),
    path('<int:pk>/edytuj/', AssetUpdateView.as_view(), name='update'),
    path('<int:pk>/usun/', AssetDeleteView.as_view(), name='delete'),
    
    # Kategorie
    path('kategorie/', AssetCategoryListView.as_view(), name='category_list'),
    path('kategorie/nowa/', AssetCategoryCreateView.as_view(), name='category_create'),
    path('kategorie/<int:pk>/edytuj/', AssetCategoryUpdateView.as_view(), name='category_update'),
    path('kategorie/<int:pk>/usun/', AssetCategoryDeleteView.as_view(), name='category_delete'),
]
