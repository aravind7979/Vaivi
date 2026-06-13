import json
import re
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

def get_long_term_memories(db, user_id):
    memories = db.query(models.LongTermMemory).filter(models.LongTermMemory.user_id == user_id).order_by(models.LongTermMemory.created_at.desc()).all()
    return [m.memory_text for m in memories]

def extract_and_save_memory_local(db, user_id, user_message):
    """
    A lightning-fast local rule-based memory extractor.
    Uses zero API tokens.
    """
    if not user_message:
        return
        
    msg = user_message.lower()
    extracted = []
    
    # 1. Name
    name_match = re.search(r"my name is ([a-z\s]+)", msg)
    if name_match:
        extracted.append({"text": f"User's name is {name_match.group(1).strip().title()}", "type": "profile"})
        
    # 2. Preferences
    pref_match = re.search(r"i prefer (.+)", msg)
    if pref_match:
        extracted.append({"text": f"User prefers {pref_match.group(1).strip()}", "type": "preference"})
        
    # 3. Projects/Building
    build_match = re.search(r"i am building (.+)", msg)
    if build_match:
        extracted.append({"text": f"User is building {build_match.group(1).strip()}", "type": "project"})
        
    # 4. Goals/Wants
    goal_match = re.search(r"i want to become (?:a |an )?(.+)", msg)
    if goal_match:
        extracted.append({"text": f"User's goal is to become {goal_match.group(1).strip()}", "type": "goal"})
        
    # Save to SQLite
    for mem in extracted:
        # Check if already exists to avoid duplicates
        existing = db.query(models.LongTermMemory).filter(
            models.LongTermMemory.user_id == user_id,
            models.LongTermMemory.memory_text == mem["text"]
        ).first()
        
        if not existing:
            new_mem = models.LongTermMemory(
                user_id=user_id,
                memory_text=mem["text"],
                memory_type=mem["type"]
            )
            db.add(new_mem)
            
    try:
        db.commit()
    except Exception as e:
        db.rollback()

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
