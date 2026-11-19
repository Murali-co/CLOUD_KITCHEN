import sys
import os
import json

# Ensure backend directory is in path and working directory is backend
sys.path.insert(0, "/home/murali/Desktop/SEM 5 /DBMS/PROJECT/backend")
os.chdir("/home/murali/Desktop/SEM 5 /DBMS/PROJECT/backend")

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db, engine
from sqlalchemy import text

client = TestClient(app)

print("=== 1. ENGINE CONNECTIVITY & SESSION CREATION ===")
with engine.connect() as conn:
    val = conn.execute(text("SELECT 1")).scalar()
    print("Direct SQLAlchemy engine test SELECT 1:", val)

print("\n=== 2. MENU ENDPOINT TEST (GET /api/v1/menu) ===")
# Test GET /api/v1/menu or /api/v1/menu/
resp_menu = client.get("/api/v1/menu")
print(f"GET /api/v1/menu Status: {resp_menu.status_code}")
try:
    print(f"GET /api/v1/menu Response: {json.dumps(resp_menu.json(), indent=2)[:300]}")
except Exception:
    print(f"GET /api/v1/menu Text: {resp_menu.text[:200]}")

print("\n=== 3. LOGIN ENDPOINT TEST (POST /api/v1/auth/login) ===")
# Test with dummy credentials that should return 401 Unauthorized or 400 (without modifying DB)
resp_login = client.post("/api/v1/auth/login", json={"email": "nonexistent@example.com", "password": "WrongPassword123!"})
print(f"POST /api/v1/auth/login Status: {resp_login.status_code}")
try:
    print(f"POST /api/v1/auth/login Response: {resp_login.json()}")
except Exception:
    print(f"POST /api/v1/auth/login Text: {resp_login.text[:200]}")

print("\n=== 4. REGISTRATION ENDPOINT VALIDATION (POST /api/v1/auth/register) ===")
# Test registration endpoint validation with invalid data to verify endpoint routing and validation logic
# without inserting fake users into the empty database
resp_reg_invalid = client.post("/api/v1/auth/register", json={})
print(f"POST /api/v1/auth/register (empty payload) Status: {resp_reg_invalid.status_code}")
try:
    print(f"POST /api/v1/auth/register Validation Response: {resp_reg_invalid.json()}")
except Exception:
    print(f"POST /api/v1/auth/register Text: {resp_reg_invalid.text[:200]}")

print("\n=== 5. HEALTH CHECK ENDPOINT (GET /health) ===")
resp_health = client.get("/health")
print(f"GET /health Status: {resp_health.status_code}")
try:
    print(f"GET /health Response: {resp_health.json()}")
except Exception:
    print(f"GET /health Text: {resp_health.text[:200]}")

print("\n=== BACKEND ENDPOINT VERIFICATION COMPLETE ===")
