from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import requests
import traceback
import httpx
import json
import uuid
from datetime import datetime
from rag import search
from db import save_chat, init_db, conn

app = FastAPI(
    title="DevMate API",
    description="AI Developer Assistant"
)

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:1b"

# Initialiser la base de données
init_db()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class AnalyzeRequest(BaseModel):
    code: str
    language: str

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None

class CreateConversationResponse(BaseModel):
    conversation_id: str

@app.get("/")
async def root():
    return {
        "message": "DevMate API is running",
        "status": "online"
    }

# ========== ENDPOINTS CONVERSATIONS ==========

@app.post("/conversations", response_model=CreateConversationResponse)
def create_conversation():
    """Crée une nouvelle conversation"""
    conversation_id = str(uuid.uuid4())
    return {"conversation_id": conversation_id}

@app.get("/conversations")
def get_conversations():
    """Récupère la liste de toutes les conversations"""
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT conversation_id, MIN(created_at) as first_message
        FROM chats
        GROUP BY conversation_id
        ORDER BY first_message DESC
    """)
    
    rows = cur.fetchall()
    cur.close()
    
    return {
        "conversations": [
            {
                "id": row[0],
                "created_at": str(row[1]) if row[1] else None
            }
            for row in rows
        ]
    }

@app.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str):
    """Récupère tous les messages d'une conversation"""
    cur = conn.cursor()
    
    cur.execute("""
        SELECT question, answer, created_at
        FROM chats
        WHERE conversation_id = %s
        ORDER BY created_at ASC
    """, (conversation_id,))
    
    rows = cur.fetchall()
    cur.close()
    
    messages = []
    for row in rows:
        messages.append({"role": "user", "content": row[0], "created_at": str(row[2])})
        if row[1]:
            messages.append({"role": "assistant", "content": row[1], "created_at": str(row[2])})
    
    return {"messages": messages}

# ========== ENDPOINTS HISTORIQUE (legacy) ==========

@app.get("/history")
async def history():
    from db import conn
    
    cur = conn.cursor()

    cur.execute("""
    SELECT question, answer, created_at
    FROM chats
    ORDER BY created_at DESC
    LIMIT 20
    """)

    rows = cur.fetchall()

    cur.close()

    return {
        "history": [
            {
                "question": row[0],
                "answer": row[1],
                "created_at": str(row[2])
            }
            for row in rows
        ]
    }

# ========== ENDPOINTS CHAT ==========

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print("QUESTION:", request.message)

        # 1. Chercher contexte RAG
        docs = search(request.message)
        context_text = "\n".join(docs[:2]) if docs else "No additional context."

        # 2. Construire prompt
        full_prompt = f"""
You are DevMate, an AI developer assistant.

Use the provided context ONLY if relevant.

Context:
{context_text}

Question:
{request.message}

Answer clearly and briefly.
"""

        print("PROMPT READY")

        # 3. Appel Ollama avec timeout réduit
        async with httpx.AsyncClient(timeout=60.0) as client:
            ollama_response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": full_prompt[:2000],
                    "stream": False
                }
            )

        print("OLLAMA STATUS:", ollama_response.status_code)

        data = ollama_response.json()
        answer = data.get("response", "No response")

        print("OLLAMA RESPONSE OK")

        # 4. Sauvegarder la conversation
        conversation_id = request.conversation_id or str(uuid.uuid4())
        try:
            save_chat(conversation_id, request.message, answer)
            print("CHAT SAVED TO DATABASE")
        except Exception as db_error:
            print("WARNING: Could not save chat to database:", db_error)

        return {"response": answer, "conversation_id": conversation_id}

    except Exception as e:
        print("CHAT ERROR:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    # Générer ou utiliser un ID de conversation existant
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    async def event_generator():
        assistant_text = ""
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    OLLAMA_URL,
                    json={
                        "model": MODEL,
                        "prompt": request.message,
                        "stream": True
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        # Ollama envoie du JSON par ligne
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            
                            if token:
                                assistant_text += token
                                yield f"data: {token}\n\n"
                                
                                # Option: Sauvegarder le message utilisateur au début
                                if assistant_text == token and len(assistant_text) == len(token):
                                    # Premier token - sauvegarder la question utilisateur
                                    try:
                                        save_chat(conversation_id, request.message, "")
                                        print(f"USER MESSAGE SAVED (conversation_id: {conversation_id})")
                                    except Exception as db_error:
                                        print("WARNING: Could not save user message:", db_error)

                        except Exception:
                            continue
            
            # Sauvegarder la réponse complète de l'assistant à la fin
            if assistant_text:
                try:
                    # Mettre à jour le message assistant avec la réponse complète
                    # Note: Une meilleure approche serait d'avoir une fonction update_chat
                    # Pour l'instant, on sauvegarde un nouveau message assistant
                    save_chat(conversation_id, "", assistant_text)
                    print(f"ASSISTANT RESPONSE SAVED (conversation_id: {conversation_id})")
                except Exception as db_error:
                    print("WARNING: Could not save assistant response:", db_error)

        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Conversation-Id": conversation_id}
    )

@app.post("/analyze-code")
async def analyze_code(request: AnalyzeRequest):
    try:
        prompt = f"""
Analyze this {request.language} code:

{request.code}
"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )

        data = response.json()

        return {"analysis": data.get("response", "")}

    except Exception as e:
        print("ERROR ANALYZE:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
