import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base, User, Chat, Message, LongTermMemory

def migrate_database():
    load_dotenv()
    
    # 1. Connect to both databases
    # Check if vaivi.db is mounted in the root (like on EC2) or inside data/
    if os.path.exists("vaivi.db"):
        sqlite_url = "sqlite:///vaivi.db"
    else:
        sqlite_url = "sqlite:///./data/vaivi.db"
        
    postgres_url = os.getenv("DATABASE_URL")
    
    if not postgres_url or not postgres_url.startswith("postgres"):
        print("Error: DATABASE_URL is not set or not a valid postgres string in .env")
        return

    print(f"Connecting to Postgres: {postgres_url.split('@')[-1]}")
    
    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_engine(postgres_url)
    
    # 2. Create tables in Postgres
    print("Creating tables in Postgres...")
    Base.metadata.create_all(postgres_engine)
    
    # 3. Create sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    # 4. Copy data table by table to preserve foreign keys
    tables_to_migrate = [User, Chat, Message, LongTermMemory]
    
    for model in tables_to_migrate:
        print(f"Migrating {model.__tablename__}...")
        records = sqlite_session.query(model).all()
        
        # Detach from sqlite session
        for record in records:
            sqlite_session.expunge(record)
            postgres_session.merge(record)
            
        postgres_session.commit()
        print(f"Successfully migrated {len(records)} records for {model.__tablename__}.")

    print("Migration complete!")
    sqlite_session.close()
    postgres_session.close()

if __name__ == "__main__":
    migrate_database()
