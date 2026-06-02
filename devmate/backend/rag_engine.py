import os
from typing import List, Dict, Any
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from sqlalchemy import create_engine, text

# Connection string for PostgreSQL with pgvector
CONNECTION_STRING = "postgresql://devmate:devmate123@localhost:5432/devmate"

class CodeVectorStore:
    def __init__(self):
        # Use Ollama for embeddings (free, local)
        self.embeddings = OllamaEmbeddings(
            model="phi4-mini",
            base_url="http://localhost:11434"
        )
        
        # Initialize PGVector collection
        self.vector_store = PGVector(
            connection_string=CONNECTION_STRING,
            embedding_function=self.embeddings,
            collection_name="code_embeddings"
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\nclass ", "\ndef ", "\nimport ", "\nfrom ", "\n\n", " "]
        )
    
    def index_codebase(self, directory_path: str):
        """Index all code files in a directory"""
        # Load all Python files
        loader = DirectoryLoader(
            directory_path,
            glob="**/*.py",
            loader_cls=TextLoader,
            recursive=True
        )
        documents = loader.load()
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Store in PostgreSQL with pgvector
        self.vector_store.add_documents(chunks)
        
        return len(chunks)
    
    def search_similar(self, query: str, k: int = 5) -> List[Dict]:
        """Search for code chunks relevant to the query"""
        results = self.vector_store.similarity_search(query, k=k)
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in results]
    
    def get_repo_context(self, github_url: str) -> Dict:
        """Clone and index a GitHub repository"""
        import subprocess
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Clone repository
            subprocess.run(["git", "clone", github_url, tmpdir], check=True)
            
            # Index the code
            chunks_indexed = self.index_codebase(tmpdir)
            
            return {
                "status": "success",
                "chunks_indexed": chunks_indexed,
                "repository": github_url
            }
