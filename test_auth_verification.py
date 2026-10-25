import json
import urllib.request
import urllib.error
import time

BASE_URL = "http://127.0.0.1:8000/api"

def make_req(path, data=None, token=None, method=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = content
        return e.code, parsed

def run_tests():
    print("--- 1. Testing Demo User Login ---")
    status, res = make_req("/auth/login", {"email": "chef_arun@example.com", "password": "SecretPass123!"})
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert "access_token" in res, "Missing access_token"
    assert res["user"]["email"] == "chef_arun@example.com", f"Unexpected email: {res['user']['email']}"
    demo_token = res["access_token"]
    print("PASS: Demo login succeeded with valid token.")

    print("--- 2. Testing Invalid Password ---")
    status, res = make_req("/auth/login", {"email": "chef_arun@example.com", "password": "WrongPassword!"})
    assert status == 401, f"Expected 401, got {status}: {res}"
    assert "Invalid email or password" in res.get("detail", ""), f"Unexpected detail: {res}"
    print(f"PASS: Invalid password correctly rejected with 401: {res['detail']}")

    print("--- 3. Testing Non-existent User Login ---")
    status, res = make_req("/auth/login", {"email": "nobody@example.com", "password": "Password123!"})
    assert status == 401, f"Expected 401, got {status}: {res}"
    assert "Invalid email or password" in res.get("detail", ""), f"Unexpected detail: {res}"
    print(f"PASS: Non-existent user rejected with 401: {res['detail']}")

    print("--- 4. Testing User Registration ---")
    new_email = f"fresh_chef_{int(time.time())}@example.com"
    status, res = make_req("/auth/register", {"name": "Fresh Chef", "email": new_email, "password": "StrongPassword123!"})
    assert status == 201, f"Expected 201, got {status}: {res}"
    assert "access_token" in res, "Missing access_token in registration"
    assert res["user"]["name"] == "Fresh Chef"
    new_token = res["access_token"]
    print(f"PASS: Registered new user {new_email} successfully.")

    print("--- 5. Testing Duplicate Registration ---")
    status, res = make_req("/auth/register", {"name": "Fresh Chef", "email": new_email, "password": "StrongPassword123!"})
    assert status == 400, f"Expected 400, got {status}: {res}"
    assert "already exists" in res.get("detail", "")
    print(f"PASS: Duplicate registration rejected with 400: {res['detail']}")

    print("--- 6. Testing /auth/me with Valid Token ---")
    status, res = make_req("/auth/me", token=demo_token)
    assert status == 200, f"Expected 200, got {status}: {res}"
    assert res["email"] == "chef_arun@example.com"
    print("PASS: Verified session profile via /auth/me.")

    print("--- 7. Testing /auth/me with Invalid Token ---")
    status, res = make_req("/auth/me", token="invalid.token.here")
    assert status == 401, f"Expected 401, got {status}: {res}"
    print(f"PASS: Invalid token rejected with 401: {res['detail']}")

    print("--- 8. Testing Logout ---")
    status, res = make_req("/auth/logout", method="POST")
    assert status == 200, f"Expected 200, got {status}: {res}"
    print("PASS: Logout endpoint succeeded.")

    print("\nALL AUTH API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
