import httpx

client = httpx.Client(base_url="http://51.21.31.101:8000")

print("Signing up...")
client.post("/api/signup", json={"email": "newuser1_aws@test.com", "password": "password"})
print("Logging in...")
login_res = client.post("/api/login", data={"username": "newuser1_aws@test.com", "password": "password"})
if login_res.status_code == 200:
    token = login_res.json()["access_token"]
    print("Got token. Asking...")
    ask_res = client.post("/api/ask", json={"query": "Hello", "chat_id": None}, headers={"Authorization": f"Bearer {token}"})
    print("Ask response:", ask_res.status_code, ask_res.text)
else:
    print("Login failed:", login_res.status_code, login_res.text)
