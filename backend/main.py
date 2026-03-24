import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Create DB tables
models.Base.metadata.create_all(bind=engine)

load_dotenv()

app = FastAPI(title="Vaivi AI Backend")

# Allow requests from Desktop (Tauri) and local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment")

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

# --- Page Routes ---
WEBSITE_DIR = os.path.join(os.path.dirname(__file__), "..", "website")

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

# --- Chat Storage Endpoints ---
@app.post("/api/chats")
async def create_chat(chat: ChatCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    new_chat = models.Chat(title=chat.title, user_id=current_user.id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@app.get("/api/chats")
async def get_chats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Chat).filter(models.Chat.user_id == current_user.id).order_by(models.Chat.updated_at.desc()).all()

@app.get("/api/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat.messages

# --- AI Endpoints ---
@app.post("/api/ask")
async def ask_assistant(request: AskRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing")
        
    prompt = f"You are Vaivi, a helpful AI assistant."
    if request.context:
        prompt += f" Context: {request.context}"
    
    # Store user message if chat_id provided
    if request.chat_id:
        chat = db.query(models.Chat).filter(models.Chat.id == request.chat_id, models.Chat.user_id == current_user.id).first()
        if chat:
            db.add(models.Message(chat_id=chat.id, role="user", content=request.query))
            db.commit()
            
            # Optionally fetch previous messages for contest
            recent_msgs = db.query(models.Message).filter(models.Message.chat_id == chat.id).order_by(models.Message.created_at.asc()).limit(10).all()
            for msg in recent_msgs:
                if msg.role == 'user':
                    prompt += f"\nUser: {msg.content}"
                else:
                    prompt += f"\nVaivi: {msg.content}"

    prompt += f"\nUser: {request.query}"
    
    try:
        response = text_model.generate_content(prompt)
        ai_text = response.text
        
        # Save AI response
        if request.chat_id and chat:
            db.add(models.Message(chat_id=chat.id, role="ai", content=ai_text))
            db.commit()
            
        return {"response": ai_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-screen")
async def analyze_screen(
    image: UploadFile = File(...),
    query: str = Form(None),
    chat_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing")
        
    try:
        if chat_id:
            chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id).first()
            if chat and query:
                db.add(models.Message(chat_id=chat.id, role="user", content=f"[Screen Shared] {query}"))
                db.commit()

        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        system_prompt = (
            "You are Vaivi, an AI assistant. Analyze this screen screenshot. "
            "Describe what is visible, detect UI elements, and suggest possible actions."
        )
        if query:
            system_prompt += f"\nUser Query: {query}"
            
        response = vision_model.generate_content([system_prompt, pil_image])
        ai_text = response.text

        if chat_id and chat:
            db.add(models.Message(chat_id=chat.id, role="ai", content=ai_text))
            db.commit()

        return {"response": ai_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files last to prevent masking API routes
app.mount("/", StaticFiles(directory=WEBSITE_DIR, html=True), name="website")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
