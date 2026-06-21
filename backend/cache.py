import os
import redis
from dotenv import load_dotenv

load_dotenv()

# We expect a standard Redis connection string: rediss://default:password@hostname:port
REDIS_URL = os.getenv("REDIS_URL")

redis_client = None

if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        redis_client.ping()
        print("Connected to Redis Cache successfully.")
    except Exception as e:
        print(f"Warning: Failed to connect to Redis. Error: {e}")
        redis_client = None
else:
    print("Warning: REDIS_URL not found in .env. Caching will be disabled.")
