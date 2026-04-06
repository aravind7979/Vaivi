import models

def get_recent_memory(db_session, chat_id, user_id, limit=10):
    """
    Fetches the `limit` most recent messages for the given chat/user
    as a list of dictionaries.
    """
    if not chat_id:
        return []
        
    chat = db_session.query(models.Chat)\
        .filter(models.Chat.id == chat_id, models.Chat.user_id == user_id)\
        .first()

    if not chat:
        return []

    recent_msgs = db_session.query(models.Message)\
        .filter(models.Message.chat_id == chat.id)\
        .order_by(models.Message.created_at.asc())\
        .limit(limit)\
        .all()
        
    memory_messages = []
    for msg in recent_msgs:
        memory_messages.append({
            "role": msg.role,
            "content": msg.content
        })
        
    return memory_messages

def save_message(db_session, chat_id, user_id, role, content):
    """
    Convenience method to save a new message to the database.
    """
    if not chat_id:
        return
        
    chat = db_session.query(models.Chat)\
        .filter(models.Chat.id == chat_id, models.Chat.user_id == user_id)\
        .first()

    if chat:
        db_session.add(models.Message(chat_id=chat.id, role=role, content=content))
        db_session.commit()
