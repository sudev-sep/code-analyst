from django.urls import path
from .views import RepositoryView,ChunkView

urlpatterns = [
    path('repositories/', RepositoryView.as_view()),
    path('repositories/<int:repo_id>/chunks/', ChunkView.as_view()),

]