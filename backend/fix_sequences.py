import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

def fix_sequences():
    load_dotenv()
    postgres_url = os.getenv("DATABASE_URL")
    
    if not postgres_url or not postgres_url.startswith("postgres"):
        print("Error: Invalid DATABASE_URL")
        return

    engine = create_engine(postgres_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    tables = ["users", "chats", "messages", "long_term_memories"]

    for table in tables:
        try:
            # Update the Postgres sequence to the maximum ID currently in the table
            query = text(f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id)+1 FROM {table}), 1), false);")
            db.execute(query)
            db.commit()
            print(f"Successfully fixed sequence for table: {table}")
        except Exception as e:
            print(f"Failed to fix sequence for {table}: {e}")
            db.rollback()
            
    db.close()
    print("All sequences fixed! You can now chat.")

if __name__ == "__main__":
    fix_sequences()
