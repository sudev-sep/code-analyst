import os
from core.models import Repository, FileChunk

# These are the only file types we care about
SUPPORTED_EXTENSIONS = [
    '.py', '.js', '.ts', '.java', '.go',
    '.rb', '.php', '.cs', '.cpp', '.c',
    '.html', '.css', '.md', '.txt'
]

# These folders we always skip — they have no useful code
SKIP_FOLDERS = [
    'node_modules', 'venv', '.git', '__pycache__',
    'dist', 'build', '.idea', 'migrations'
]

# How many lines per chunk
# Think of it like cutting a book into pages of 60 lines each
CHUNK_SIZE = 60
CHUNK_OVERLAP = 10  # last 10 lines of one chunk repeat at start of next
                    # this way we don't lose context at the boundaries

def parse_repository(repo_id):
    repo = Repository.objects.get(id=repo_id)

    print(f"Starting to parse: {repo.name}")

    # Delete any old chunks if we're re-parsing
    FileChunk.objects.filter(repository=repo).delete()

    total_chunks = 0

    # os.walk goes through every folder and file in the repo
    # think of it like opening every drawer in a filing cabinet
    for root, dirs, files in os.walk(repo.local_path):

        # Remove skip folders so os.walk doesn't go inside them
        dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS]

        for filename in files:
            # Check if this file type is one we care about
            _, extension = os.path.splitext(filename)
            if extension.lower() not in SUPPORTED_EXTENSIONS:
                continue

            file_path = os.path.join(root, filename)

            # Get a shorter path for display
            # e.g. instead of C:\projects\repos\1\payment\service.py
            #      just show: payment\service.py
            relative_path = os.path.relpath(file_path, repo.local_path)

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                if not content.strip():
                    continue  # skip empty files

                print(f"  Reading: {relative_path}")

                # Cut the file into chunks and save each one
                chunks = split_into_chunks(content, relative_path)

                for index, chunk_text in enumerate(chunks):
                    FileChunk.objects.create(
                        repository=repo,
                        file_path=relative_path,
                        content=chunk_text,
                        chunk_index=index
                    )
                    total_chunks += 1

            except Exception as e:
                print(f"  Skipping {relative_path}: {e}")
                continue

    print(f"Done! Created {total_chunks} chunks from {repo.name}")
    return total_chunks


def split_into_chunks(content, file_path):
    """
    Splits a file's content into overlapping chunks.

    Example with CHUNK_SIZE=5 and CHUNK_OVERLAP=2:
    Lines: [1,2,3,4,5,6,7,8,9,10]
    Chunk 1: [1,2,3,4,5]
    Chunk 2: [4,5,6,7,8]   ← starts 2 lines back (overlap)
    Chunk 3: [7,8,9,10]
    """
    lines = content.split('\n')

    # If file is small enough, just return it as one chunk
    if len(lines) <= CHUNK_SIZE:
        return [f"File: {file_path}\n\n{content}"]

    chunks = []
    start = 0

    while start < len(lines):
        end = start + CHUNK_SIZE
        chunk_lines = lines[start:end]
        chunk_text = '\n'.join(chunk_lines)

        # Add the file path at the top of each chunk
        # so the AI always knows which file this came from
        chunk_with_context = f"File: {file_path}\nLines: {start+1}-{min(end, len(lines))}\n\n{chunk_text}"
        chunks.append(chunk_with_context)

        # Move forward, but step back by OVERLAP so chunks share some lines
        start += (CHUNK_SIZE - CHUNK_OVERLAP)

    return chunks