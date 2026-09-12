import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
from typing import Annotated, TypedDict, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
import shutil
from pydantic import BaseModel, Field

from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

# Import chat history functions
from chat_history import (
    create_session, get_sessions, get_session, get_messages,
    add_message, delete_session, update_session_title,
    update_session_document, touch_session
)

# 1. Initialize Groq LLM
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
    max_tokens=4096
)

# 2. Import Graph
from graph.graph import create_graph
app_brain = create_graph(llm)


# --- FASTAPI SERVER ---

app = FastAPI()

# Enable CORS so Next.js (port 3000) can talk to FastAPI (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "Backend is running", "pinecone_index": os.getenv("PINECONE_INDEX_NAME")}

# ==========================================
# CHAT HISTORY / SESSION ENDPOINTS
# ==========================================

@app.get("/sessions")
async def list_sessions(user_id: str):
    """List all chat sessions for a user."""
    sessions = get_sessions(user_id)
    return {"sessions": sessions}

@app.post("/sessions")
async def create_new_session(
    user_id: str = Form(...),
    title: str = Form("New Chat"),
    active_document: str = Form("")
):
    """Create a new chat session."""
    session = create_session(user_id, title, active_document)
    return session

@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get all messages for a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = get_messages(session_id)
    return {"session": session, "messages": messages}

@app.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session and all its messages."""
    delete_session(session_id)
    return {"status": "deleted"}

@app.patch("/sessions/{session_id}")
async def update_chat_session(
    session_id: str,
    title: str = Form(None),
    active_document: str = Form(None)
):
    """Update session title or active document."""
    if title is not None:
        update_session_title(session_id, title)
    if active_document is not None:
        update_session_document(session_id, active_document)
    return {"status": "updated"}

# ==========================================
# CHAT ENDPOINT (with history saving)
# ==========================================

@app.post("/chat")
async def chat_endpoint(
    user_id: str = Form(...),
    thread_id: str = Form(...),
    message: str = Form(...),
    active_document: str = Form(""),
    session_id: str = Form("")  # Link to a chat session
):
    try:
        # Setup config for memory persistence
        config = {"configurable": {"thread_id": thread_id}}
        
        print(f"CHAT: user={user_id}, session={session_id}, active_doc='{active_document}', msg='{message[:50]}...'")
        
        # Save user message to chat history
        if session_id:
            add_message(session_id, "user", message)
            # Auto-title the session with the first message if it's still "New Chat"
            session = get_session(session_id)
            if session and session["title"] == "New Chat":
                # Use first 50 chars of the first message as title
                auto_title = message[:50] + ("..." if len(message) > 50 else "")
                update_session_title(session_id, auto_title)
        
        # Run the graph
        inputs = {
            "messages": [HumanMessage(content=message)], 
            "user_id": user_id,
            "file_context": "",
            "intent": "",
            "safety_level": "",
            "active_document": active_document
        }
        result = app_brain.invoke(inputs, config=config)
        
        ai_response = result["messages"][-1].content
        
        # Save AI response to chat history
        if session_id:
            add_message(session_id, "ai", ai_response)
        
        return {"response": ai_response}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"CHAT ERROR: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# UPLOAD ENDPOINT
# ==========================================

from ingest_data import ingest_pdf 

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    session_id: str = Form("")  # Link upload to a session
):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
        # 1. Create a safe place to store the uploaded file temporarily
        upload_dir = "uploaded_files"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        
        # 2. Save the file to your backend folder
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. Process the file into Pinecone!
        print(f"File received from user {user_id}. Starting ingestion...")
        result = ingest_pdf(file_path, user_id=user_id)
        
        # 4. Update session with document info
        if session_id:
            update_session_document(session_id, file.filename)
            # Update title to include document name
            update_session_title(session_id, f"📄 {file.filename}")
            # Add a system message to the chat history
            add_message(
                session_id, "ai",
                f"📄 {file.filename} uploaded successfully!\n📊 {result['total_pages']} pages → {result['total_chunks']} chunks processed and stored in Pinecone.\n\n🔍 All your questions will now be answered from this document."
            )
        
        return {
            "status": "success",
            "message": f"✅ {file.filename} uploaded successfully!",
            "filename": file.filename,
            "total_pages": result["total_pages"],
            "total_chunks": result["total_chunks"],
            "chunk_previews": result["chunk_previews"]
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"UPLOAD ERROR: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))