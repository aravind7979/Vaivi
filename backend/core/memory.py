import json
import models

def get_recent_memory(db, chat_id, user_id, limit=10):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == user_id).first()
    if not chat:
        return []
    messages = db.query(models.Message).filter(models.Message.chat_id == chat_id).order_by(models.Message.created_at.desc()).limit(limit).all()
    return messages[::-1]

def save_message(db, chat_id, user_id, role, content):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == user_id).first()
    if not chat:
        return None
    new_msg = models.Message(chat_id=chat_id, role=role, content=content)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

def build_chat_history(recent_msgs):
    """
    Extracts standard chat history.
    recent_msgs is a list of SQLAlchemy Message models.
    """
    history_text = ""
    for msg in recent_msgs:
        role = "User" if msg.role == 'user' else "Vaivi"
        history_text += f"{role}: {msg.content}\n"
    return history_text
