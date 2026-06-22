import os
from celery_app import celery_app
from database import SessionLocal
import models
from core.title_generator import generate_title
from core.memory import extract_and_save_memory_local
from dotenv import load_dotenv

load_dotenv()

@celery_app.task(name="tasks.generate_chat_title_task", max_retries=3, default_retry_delay=5)
def generate_chat_title_task(chat_id: int, query: str):
    """
    Asynchronously generates a title for a new chat based on the first query.
    Updates the chat in PostgreSQL/SQLite.
    """
    print(f"[Celery Worker] Starting title generation for Chat ID: {chat_id}")
    db = SessionLocal()
    try:
        chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            print(f"[Celery Worker] Chat {chat_id} not found. Skipping.")
            return

        # Check if the title is still the default "New Chat"
        if chat.title == "New Chat":
            new_title = generate_title(query)
            chat.title = new_title
            db.commit()
            print(f"[Celery Worker] Chat {chat_id} title successfully set to: '{new_title}'")
        else:
            print(f"[Celery Worker] Chat {chat_id} already has title '{chat.title}'. Skipping.")
    except Exception as e:
        db.rollback()
        print(f"[Celery Worker] Error in generate_chat_title_task: {e}")
        raise generate_chat_title_task.retry(exc=e)
    finally:
        db.close()

@celery_app.task(name="tasks.extract_memory_task", max_retries=3, default_retry_delay=10)
def extract_memory_task(user_id: int, query: str):
    """
    Asynchronously parses user messages for memory facts, saves to PostgreSQL/SQLite,
    and indexes them in the local FAISS vector store.
    """
    print(f"[Celery Worker] Starting memory extraction for User ID: {user_id}")
    db = SessionLocal()
    try:
        # Call the existing memory extraction logic with the worker's dedicated session
        extract_and_save_memory_local(db, user_id, query)
        print(f"[Celery Worker] Memory extraction complete for User ID: {user_id}")
    except Exception as e:
        db.rollback()
        print(f"[Celery Worker] Error in extract_memory_task: {e}")
        raise extract_memory_task.retry(exc=e)
    finally:
        db.close()
