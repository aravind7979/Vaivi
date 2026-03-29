import sys
import traceback
from fastapi.testclient import TestClient
from main import app

try:
    print("Testing TestClient without raise_server_exceptions=False")
    # newer Starlette might raise exceptions directly or we can catch them here
    client = TestClient(app, raise_server_exceptions=False)
except TypeError:
    client = TestClient(app)

try:
    response = client.post("/api/login", data={"username": "aravindindrapally79@gmail.com", "password": "hello"})
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
except Exception as e:
    print("EXCEPTION CAUGHT:")
    traceback.print_exc()
