import json

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
