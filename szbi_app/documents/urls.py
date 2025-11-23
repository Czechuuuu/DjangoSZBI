from django.urls import path
from .views import DocumentListView, DocumentCreateView

app_name = "documents"

urlpatterns = [
    path('', DocumentListView.as_view(), name='list'),
    path('new/', DocumentCreateView.as_view(), name='create'),
]
