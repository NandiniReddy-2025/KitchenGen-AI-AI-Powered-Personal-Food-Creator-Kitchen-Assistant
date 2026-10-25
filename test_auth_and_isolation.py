import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import User, PantryItem, ShoppingListItem, UserFavorite

from app.database_migration import run_database_migrations

def run_tests():
    print("=== STARTING AUTH & USER ISOLATION TESTS ===")

    # Run migrations first
    run_database_migrations()

    # 1. Clean test users if they exist from previous runs
    db = SessionLocal()
    try:
        db.query(User).filter(User.email.in_(["chef_arun@example.com", "priya_bakes@example.com"])).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    # 2. Test User 1 Registration
    res1 = client.post("/api/auth/register", json={
        "name": "Chef Arun",
        "email": "chef_arun@example.com",
        "password": "SecretPass123!"
    })
    assert res1.status_code == 201, f"User 1 registration failed: {res1.text}"
    user1_data = res1.json()
    assert "access_token" in user1_data, "access_token missing"
    assert user1_data["user"]["email"] == "chef_arun@example.com"
    token1 = user1_data["access_token"]
    user1_id = user1_data["user"]["id"]
    print("[PASS] User 1 registered successfully (ID:", user1_id, ")")

    # 3. Test Duplicate Registration Handling
    res_dup = client.post("/api/auth/register", json={
        "name": "Chef Arun Duplicate",
        "email": "chef_arun@example.com",
        "password": "AnotherPassword999!"
    })
    assert res_dup.status_code == 400, f"Duplicate registration should fail with 400, got: {res_dup.status_code}"
    print("[PASS] Duplicate email rejection verified (400 Bad Request)")

    # 4. Test User 2 Registration
    res2 = client.post("/api/auth/register", json={
        "name": "Priya Bakes",
        "email": "priya_bakes@example.com",
        "password": "PriyaPass456!"
    })
    assert res2.status_code == 201, f"User 2 registration failed: {res2.text}"
    user2_data = res2.json()
    token2 = user2_data["access_token"]
    user2_id = user2_data["user"]["id"]
    print("[PASS] User 2 registered successfully (ID:", user2_id, ")")

    # 5. Test Invalid Login Credentials
    res_fail = client.post("/api/auth/login", json={
        "email": "chef_arun@example.com",
        "password": "WrongPassword!"
    })
    assert res_fail.status_code == 401, f"Invalid login should return 401, got: {res_fail.status_code}"
    print("[PASS] Invalid password rejection verified (401 Unauthorized)")

    # 6. Test Successful Login
    res_login = client.post("/api/auth/login", json={
        "email": "chef_arun@example.com",
        "password": "SecretPass123!"
    })
    assert res_login.status_code == 200, f"Valid login failed: {res_login.text}"
    assert "access_token" in res_login.json()
    print("[PASS] Valid login verified (200 OK with Bearer token)")

    # 7. Test Current User Profile (/api/auth/me)
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
    assert res_me.status_code == 200, f"Get /me failed: {res_me.text}"
    assert res_me.json()["email"] == "chef_arun@example.com"
    print("[PASS] Current user profile endpoint verified (/api/auth/me)")

    # 8. Test Pantry Isolation
    # Add item to User 1 pantry
    res_p1 = client.post(
        "/api/pantry",
        json={"name": "Fresh Coriander", "quantity": 1, "unit": "bunch", "category": "Produce"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert res_p1.status_code == 201, f"Pantry add user 1 failed: {res_p1.text}"

    # Add item to User 2 pantry
    res_p2 = client.post(
        "/api/pantry",
        json={"name": "Dark Cocoa Powder", "quantity": 250, "unit": "g", "category": "Baking"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert res_p2.status_code == 201, f"Pantry add user 2 failed: {res_p2.text}"

    # Verify User 1 pantry only has User 1's items
    res_pantry1 = client.get("/api/pantry", headers={"Authorization": f"Bearer {token1}"})
    items1 = [item["name"] for item in res_pantry1.json()]
    assert "Fresh Coriander" in items1, "User 1 should see Fresh Coriander"
    assert "Dark Cocoa Powder" not in items1, "User 1 should NOT see User 2's Cocoa Powder"

    # Verify User 2 pantry only has User 2's items
    res_pantry2 = client.get("/api/pantry", headers={"Authorization": f"Bearer {token2}"})
    items2 = [item["name"] for item in res_pantry2.json()]
    assert "Dark Cocoa Powder" in items2, "User 2 should see Dark Cocoa Powder"
    assert "Fresh Coriander" not in items2, "User 2 should NOT see User 1's Coriander"
    print("[PASS] Pantry data isolation between users verified")

    # 9. Test Shopping List Isolation
    res_s1 = client.post(
        "/api/shopping-list",
        json={"name": "Basmati Rice 5kg", "quantity": 1, "unit": "bag", "category": "Pantry Staples"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert res_s1.status_code == 201

    res_s2 = client.post(
        "/api/shopping-list",
        json={"name": "Vanilla Extract", "quantity": 1, "unit": "bottle", "category": "Baking"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert res_s2.status_code == 201

    list1 = [i["name"] for i in client.get("/api/shopping-list", headers={"Authorization": f"Bearer {token1}"}).json()]
    list2 = [i["name"] for i in client.get("/api/shopping-list", headers={"Authorization": f"Bearer {token2}"}).json()]
    assert "Basmati Rice 5kg" in list1 and "Vanilla Extract" not in list1
    assert "Vanilla Extract" in list2 and "Basmati Rice 5kg" not in list2
    print("[PASS] Shopping list isolation between users verified")

    # 10. Test Favorites Isolation
    # Add Recipe 1 to User 1 favorites
    res_fav1 = client.post("/api/favorites/1", headers={"Authorization": f"Bearer {token1}"})
    assert res_fav1.status_code == 201

    # Add Recipe 2 to User 2 favorites
    res_fav2 = client.post("/api/favorites/2", headers={"Authorization": f"Bearer {token2}"})
    assert res_fav2.status_code == 201

    favs1 = client.get("/api/favorites/ids", headers={"Authorization": f"Bearer {token1}"}).json()
    favs2 = client.get("/api/favorites/ids", headers={"Authorization": f"Bearer {token2}"}).json()
    assert 1 in favs1 and 2 not in favs1, f"User 1 favorites: {favs1}"
    assert 2 in favs2 and 1 not in favs2, f"User 2 favorites: {favs2}"
    print("[PASS] Favorites isolation between users verified")

    # 11. Test Unauthenticated Access to Protected Endpoints
    res_no_auth = client.get("/api/auth/me")
    assert res_no_auth.status_code == 401
    print("[PASS] Protected route rejection for unauthenticated users verified (401)")

    # 12. Test Public Recipe Browsing Still Works
    res_recipes = client.get("/api/recipes?cuisine=South%20Indian")
    assert res_recipes.status_code == 200
    assert len(res_recipes.json()) > 0
    print("[PASS] Public recipe browsing preserved for guests & all users (200 OK)")

    print("\n>>> ALL BACKEND AUTH & ISOLATION TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
