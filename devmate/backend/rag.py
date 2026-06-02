import requests
import psycopg2
from psycopg2.extensions import register_adapter, AsIs
import numpy as np

DB = "postgresql://devmate_user:devmate_1234@localhost:5433/devmate"

# Adapter les listes Python pour PostgreSQL
def adapt_vector(v):
    return AsIs("'[" + ",".join(map(str, v)) + "]'::vector")

register_adapter(list, adapt_vector)
register_adapter(np.ndarray, adapt_vector)

# 1. Embedding via Ollama
def embed(text):
    r = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": "nomic-embed-text",
            "prompt": text
        },
        timeout=30
    )
    return r.json()["embedding"]

# 2. Save document
def save_document(content, metadata=None):
    emb = embed(content)
    
    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    
    # Stocker le contenu et l'embedding
    cur.execute(
        "INSERT INTO documents (content, embedding) VALUES (%s, %s)",
        (content, emb)
    )
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Document saved (length: {len(content)} chars)")

# 3. Search similar docs avec score de pertinence (version avancée)
def search(query, k=5):
    """
    Recherche les k documents les plus pertinents pour la requête.
    Retourne une liste de contenus (sans les scores).
    """
    emb = embed(query)
    
    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    
    # Récupérer les documents avec leur score de similarité
    cur.execute("""
        SELECT content, 1 - (embedding <-> (%s::vector)) as score
        FROM documents
        ORDER BY embedding <-> (%s::vector)
        LIMIT %s
    """, (emb, emb, k))
    
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Afficher les scores pour debug (optionnel)
    for content, score in results:
        print(f"Relevance score: {score:.4f} - Content preview: {content[:100]}...")
    
    # Retourner uniquement les contenus
    return [r[0] for r in results]

# 4. Version simple pour la compatibilité (sans score)
def search_simple(query, k=3):
    """
    Version simple sans score de pertinence.
    """
    emb = embed(query)
    
    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT content
        FROM documents
        ORDER BY embedding <-> (%s::vector)
        LIMIT %s
    """, (emb, k))
    
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return [r[0] for r in results]

# 5. Version avec scores pour utilisation avancée
def search_with_scores(query, k=3):
    """
    Retourne les documents avec leurs scores de pertinence.
    """
    emb = embed(query)
    
    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT content, 1 - (embedding <-> (%s::vector)) as score
        FROM documents
        ORDER BY embedding <-> (%s::vector)
        LIMIT %s
    """, (emb, emb, k))
    
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return [(content, score) for content, score in results]
