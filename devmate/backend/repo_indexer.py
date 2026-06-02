import os
import tempfile
from git import Repo
from rag import save_document

SUPPORTED_EXTENSIONS = [".py"]

IGNORE_FOLDERS = [
    "tests",
    "docs",
    ".github",
    "__pycache__"
]

MAX_CHUNK = 1000

def index_repository(repo_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        print("Cloning repo...")
        Repo.clone_from(repo_url, tmpdir)

        indexed = 0

        for root, dirs, files in os.walk(tmpdir):
            # Ignorer les dossiers spécifiques
            if any(folder in root for folder in IGNORE_FOLDERS):
                continue
                
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'tests', 'docs']]

            for file in files:
                if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    path = os.path.join(root, file)

                    # Ignorer les fichiers de test
                    if 'test' in file.lower():
                        print("Skipping test file:", file)
                        continue

                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Ignorer fichiers trop gros
                        if len(content) > 20000:
                            print(f"File too large: {file} ({len(content)} chars)")
                            continue

                        # Découper en chunks
                        for i in range(0, len(content), MAX_CHUNK):
                            chunk = content[i:i+MAX_CHUNK]

                            if len(chunk.strip()) > 50:
                                save_document(
                                    chunk,
                                    metadata={
                                        "file": path,
                                        "chunk": i
                                    }
                                )
                                indexed += 1
                                print(f"Indexed chunk {i} from {file}")

                    except Exception as e:
                        print("Skipped:", file, e)

        return indexed
