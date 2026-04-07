import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io
from sqlalchemy.orm import Session
from datetime import timedelta

from database import engine, get_db
import models
import auth
from core.orchestrator import route_and_answer
from core.memory import get_recent_memory, save_message
import time

# Create DB tables
models.Base.metadata.create_all(bind=engine)

load_dotenv()

app = FastAPI(title="Vaivi AI Backend")

# 🔥 CORS (IMPORTANT for frontend later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later (e.g., Vercel domain)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment")

genai.configure(api_key=GEMINI_API_KEY)

vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')
text_model = genai.GenerativeModel('gemini-2.5-flash-lite')

# --- Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str

class AskRequest(BaseModel):
    query: str
    context: str | None = None
    chat_id: int | None = None

class ChatCreate(BaseModel):
    title: str

# --- Auth Endpoints ---
@app.post("/api/signup")
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me")
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "email": current_user.email,
        "shortcut_keys": current_user.shortcut_keys
    }

# --- Chat Storage ---
@app.post("/api/chats")
async def create_chat(chat: ChatCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    new_chat = models.Chat(title=chat.title, user_id=current_user.id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@app.get("/api/chats")
async def get_chats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Chat)\
        .filter(models.Chat.user_id == current_user.id)\
        .order_by(models.Chat.updated_at.desc())\
        .all()

@app.get("/api/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    chat = db.query(models.Chat)\
        .filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id)\
        .first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return chat.messages

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    chat = db.query(models.Chat)\
        .filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id)\
        .first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(chat)
    db.commit()
    return {"status": "deleted"}

# --- AI Endpoints (Refactored to Copilot Orchestrator) ---
from core.orchestrator import route_and_answer

@app.post("/api/ask")
async def ask_assistant(request: AskRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing")

    chat = None
    if request.chat_id:
        chat = db.query(models.Chat)\
            .filter(models.Chat.id == request.chat_id, models.Chat.user_id == current_user.id)\
            .first()

    recent_msgs = []
    if chat:
        db.add(models.Message(chat_id=chat.id, role="user", content=request.query))
        db.commit()
        recent_msgs = db.query(models.Message)\
            .filter(models.Message.chat_id == chat.id)\
            .order_by(models.Message.created_at.asc())\
            .limit(10)\
            .all()

    try:
        # Pass to the Orchestrator
        result = route_and_answer(request.query, screenshot_base64=None, db_messages=recent_msgs)
        ai_text = result["response"]

        if chat:
            db.add(models.Message(chat_id=chat.id, role="ai", content=ai_text))
            db.commit()

        return {"response": ai_text, "debug_metrics": result.get("debug_metrics")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat-with-media")
async def chat_with_media(
    files: list[UploadFile] = File(...),
    query: str = Form(None),
    chat_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing")

    try:
        chat = None
        if chat_id:
            chat = db.query(models.Chat)\
                .filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id)\
                .first()

            if chat and query:
                db.add(models.Message(chat_id=chat.id, role="user", content=f"[Screen Context] {query}"))
                db.commit()

        recent_msgs = []
        if chat:
            recent_msgs = db.query(models.Message)\
                .filter(models.Message.chat_id == chat.id)\
                .order_by(models.Message.created_at.asc())\
                .limit(10)\
                .all()

        # Extract strictly first file as base64 string
        screenshot_base64 = None
        if files:
            image_bytes = await files[0].read()
            import base64
            screenshot_base64 = base64.b64encode(image_bytes).decode('utf-8')

        result = route_and_answer(query or "Analyze this screen", screenshot_base64=screenshot_base64, db_messages=recent_msgs)
        ai_text = result["response"]

        if chat:
            db.add(models.Message(chat_id=chat.id, role="ai", content=ai_text))
            db.commit()

        return {"response": ai_text, "debug_metrics": result.get("debug_metrics")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def unified_copilot_query(
    files: list[UploadFile] | None = None,
    query: str = Form(""),
    chat_id: int = Form(None),
    mode: str = Form("assist"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Unified Copilot Route:
    Perception -> Planning -> Context Fusion -> Orchestrator -> Result
    """
    start_time = time.time()
    
    pil_images = []
    if files:
        for file in files:
            image_bytes = await file.read()
            pil_images.append(Image.open(io.BytesIO(image_bytes)))
            
    # Load memory 
    chat_history = get_recent_memory(db, chat_id, current_user.id, limit=10)
    
    # Save user query
    if chat_id:
        db_msg = f"[Screen] {query}" if pil_images else query
        save_message(db, chat_id, current_user.id, "user", db_msg)

    # Route and Answer
    result = route_and_answer(query, pil_images, chat_history)
    ai_response = result["response"]
    
    # Save Assistant Response
    if chat_id:
        save_message(db, chat_id, current_user.id, "ai", ai_response)

    elapsed_ms = int((time.time() - start_time) * 1000)
    result["debug_info"]["latency_ms"] = elapsed_ms
    
    return {
        "response": ai_response,
        "debug_info": result["debug_info"]
    }