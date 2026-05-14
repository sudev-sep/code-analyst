from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Repository, FileChunk
from .services.clone_service import clone_repository

class RepositoryView(APIView):

    def post(self, request):
        github_url = request.data.get('github_url')

        if not github_url:
            return Response({'error': 'github_url is required'}, status=400)

        # Extract the repo name from the URL
        # e.g. https://github.com/django/django → "django"
        repo_name = github_url.rstrip('/').split('/')[-1]

        # Save to database
        repo = Repository.objects.create(
            github_url=github_url,
            name=repo_name,
        )

        # Clone it right now (we'll make this background later)
        clone_repository(repo.id)

        # Refresh from database to get updated status
        repo.refresh_from_db()

        return Response({
            'id': repo.id,
            'name': repo.name,
            'status': repo.status,
            'message': f'Repository "{repo.name}" has been cloned successfully!'
        })

    def get(self, request):
        repos = Repository.objects.all().values('id', 'name', 'status', 'github_url', 'created_at')
        return Response(list(repos))
    





class ChunkView(APIView):

    def get(self, request, repo_id):
        chunks = FileChunk.objects.filter(
            repository_id=repo_id
        ).values('id', 'file_path', 'chunk_index', 'content')[:20] 

        total = FileChunk.objects.filter(repository_id=repo_id).count()

        return Response({
            'total_chunks': total,
            'showing': len(chunks),
            'chunks': list(chunks)
        })