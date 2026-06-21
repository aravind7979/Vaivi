import json
import re
import models
from rag.rag_retriever import get_retriever

from cache import redis_client

class CachedMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content

def get_recent_memory(db, chat_id, user_id, limit=10):
    cache_key = f"chat:{chat_id}:messages"
    
    # 1. Try Redis Cache
    if redis_client:
        cached_msgs = redis_client.lrange(cache_key, 0, limit - 1)
        if cached_msgs:
            print(f"[CACHE HIT] Loaded {len(cached_msgs)} messages from Redis for chat {chat_id}")
            return [CachedMessage(**json.loads(m)) for m in cached_msgs]
            
    # 2. Fallback to Postgres
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == user_id).first()
    if not chat:
        return []
    messages = db.query(models.Message).filter(models.Message.chat_id == chat_id).order_by(models.Message.created_at.desc()).limit(limit).all()
    messages = messages[::-1]
    
    # 3. Populate Redis Cache
    if redis_client and messages:
        redis_client.delete(cache_key)
        for msg in messages:
            redis_client.rpush(cache_key, json.dumps({"role": msg.role, "content": msg.content}))
        redis_client.expire(cache_key, 3600) # Expire in 1 hour
        print(f"[CACHE MISS] Loaded {len(messages)} messages from Postgres and populated Redis")
        
    return messages

def save_message(db, chat_id, user_id, role, content):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == user_id).first()
    if not chat:
        return None
    new_msg = models.Message(chat_id=chat_id, role=role, content=content)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    # Push new message to Redis Cache
    if redis_client:
        cache_key = f"chat:{chat_id}:messages"
        redis_client.rpush(cache_key, json.dumps({"role": role, "content": content}))
        redis_client.expire(cache_key, 3600)
        
    return new_msg

def get_long_term_memories(db, user_id, user_query=None):
    """
    Hybrid Retrieval:
    1. Always load Core Identity Facts (Importance >= 9) via SQLite.
    2. Load Contextual Facts via FAISS Semantic Search if user_query is provided.
    """
    # 1. SQLite Direct Lookup for Core Facts
    core_memories = db.query(models.LongTermMemory).filter(
        models.LongTermMemory.user_id == user_id,
        models.LongTermMemory.importance >= 9
    ).all()
    
    memory_texts = [m.memory_text for m in core_memories]
    
    # 2. FAISS Semantic Search for Contextual Facts
    if user_query:
        retriever = get_retriever()
        semantic_results = retriever.retrieve(user_query, top_k=3, threshold=1.5, filter_type="memory")
        for res in semantic_results:
            text = res["text"]
            if text not in memory_texts: # Deduplicate
                memory_texts.append(text)
                
    return memory_texts

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
        extracted.append({"text": f"User's name is {name_match.group(1).strip().title()}", "type": "profile_name", "importance": 10})
        
    # 2. Preferences
    pref_match = re.search(r"i prefer (.+)", msg)
    if pref_match:
        extracted.append({"text": f"User prefers {pref_match.group(1).strip()}", "type": "preference", "importance": 7})
        
    # 3. Projects/Building
    build_match = re.search(r"i am building (.+)", msg)
    if build_match:
        extracted.append({"text": f"User is building {build_match.group(1).strip()}", "type": "project", "importance": 9})
        
    # 4. Goals/Wants
    goal_match = re.search(r"i want to become (?:a |an )?(.+)", msg)
    if goal_match:
        extracted.append({"text": f"User's goal is to become {goal_match.group(1).strip()}", "type": "goal", "importance": 10})
        
    # Save to SQLite with Contradiction Resolution
    for mem in extracted:
        # For Profile and Goal, we UPDATE if it exists (Contradiction Resolution)
        if mem["type"] in ["profile_name", "goal"]:
            existing_type = db.query(models.LongTermMemory).filter(
                models.LongTermMemory.user_id == user_id,
                models.LongTermMemory.memory_type == mem["type"]
            ).first()
            
            if existing_type:
                existing_type.memory_text = mem["text"]
                existing_type.importance = mem["importance"]
                continue # Skip to next memory
                
        # For others (Preferences, Projects), we INSERT but prevent exact duplicates
        existing_text = db.query(models.LongTermMemory).filter(
            models.LongTermMemory.user_id == user_id,
            models.LongTermMemory.memory_text == mem["text"]
        ).first()
        
        if not existing_text:
            new_mem = models.LongTermMemory(
                user_id=user_id,
                memory_text=mem["text"],
                memory_type=mem["type"],
                importance=mem["importance"]
            )
            db.add(new_mem)
            
            
            # Add to FAISS Vector Store for Semantic Search
            try:
                retriever = get_retriever()
                retriever.add_to_index(mem["text"], {"type": "memory", "user_id": user_id, "memory_type": mem["type"]})
            except Exception as faiss_err:
                print(f"FAISS add failed: {faiss_err}")
            
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
