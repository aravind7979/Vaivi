import httpx
import json

client = httpx.Client(base_url="http://127.0.0.1:8000")

print("--- Testing JSON Request ---")
try:
    r = client.post("/api/login", json={"username": "aravindindrapally79@gmail.com", "password": "password"})
    print("Status:", r.status_code)
    print("Body:", r.text)
except Exception as e:
    print("Error:", e)

print("\n--- Testing Form Request ---")
try:
    r = client.post("/api/login", data={"username": "aravindindrapally79@gmail.com", "password": "password"})
    print("Status:", r.status_code)
    print("Body:", r.text)
except Exception as e:
    print("Error:", e)
