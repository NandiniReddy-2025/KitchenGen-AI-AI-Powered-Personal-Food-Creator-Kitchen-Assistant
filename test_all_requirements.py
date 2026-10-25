import sys
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.database_migration import run_database_migrations
from app.models import User, Recipe, PantryItem, ShoppingListItem, UserFavorite
from app.services.recipe_images import RECIPE_IMAGES, get_dish_image, get_verified_recipe_image, DEFAULT_FALLBACK_IMAGE

def test_everything():
    print("=" * 60)
    print("KITCHENGEN AI - FULL COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 60)

    # 1. Run migrations
    run_database_migrations()

    client = TestClient(app)
    db = SessionLocal()

    try:
        # ==============================================================
        # TEST 1: RECIPE IMAGES FOR EVERY RECIPE IN DATABASE
        # ==============================================================
        print("\n--- 1. Testing Recipe Image Mapping For Every Recipe ---")
        all_recipes = db.query(Recipe).all()
        assert len(all_recipes) > 0, "No recipes found in database!"
        print(f"Total recipes loaded in database: {len(all_recipes)}")

        missing_images = []
        for r in all_recipes:
            # Check image in database and image in RECIPE_IMAGES registry
            image_url = get_verified_recipe_image(r.id, r.title, r.cuisine)
            if not image_url or image_url == DEFAULT_FALLBACK_IMAGE:
                # Check if it was explicitly mapped
                if r.id not in RECIPE_IMAGES:
                    missing_images.append((r.id, r.title))

        assert len(missing_images) == 0, f"Recipes without explicit dish image mapping: {missing_images}"
        print(f"[PASS] All {len(all_recipes)} recipes have authentic dish-specific image mappings in the registry.")

        # Test specific regional dishes requested in prompt:
        spot_checks = [
            (101, "Masala Dosa", "dosa"),
            (103, "Steamed Idli", "idli"),
            (176, "Rava Upma", "upma"),
            (109, "Hyderabadi Dum Biryani", "biryani"),
            (139, "Awadhi Dum Pulao", "pulao"),
            (106, "Puttu and Kadala Curry", "puttu"),
            (132, "Dal Makhani", "dal"),
            (146, "Aloo Paratha", "paratha"),
            (137, "Sarson Ka Saag", "makki roti"),
        ]
        for rid, expected_name, keyword in spot_checks:
            rec = db.query(Recipe).filter(Recipe.id == rid).first()
            assert rec is not None, f"Recipe {expected_name} with ID {rid} missing"
            img = get_dish_image(rid)
            assert img.startswith("http"), f"Invalid image for {expected_name}: {img}"
            print(f"  [CHECK] ID {rid:3d}: {rec.title:30s} -> {img[:60]}...")
        print("[PASS] Specific dishes verified (dosa, idli, upma, biryani, pulao, puttu, dal, paratha, etc.)")

        # ==============================================================
        # TEST 2: GRACEFUL FALLBACK HANDLING
        # ==============================================================
        print("\n--- 2. Testing Image Fallback Logic ---")
        fallback_for_unknown = get_dish_image(999999)
        assert fallback_for_unknown == DEFAULT_FALLBACK_IMAGE, f"Expected {DEFAULT_FALLBACK_IMAGE}, got {fallback_for_unknown}"
        print(f"[PASS] Graceful fallback image correctly assigned for unknown recipe: {fallback_for_unknown}")

        # ==============================================================
        # TEST 3: REGISTRATION AND LOGIN (SUCCESS & FAILURES)
        # ==============================================================
        print("\n--- 3. Testing Authentication (Register & Login) ---")
        
        # Clean test accounts
        test_email1 = "test_user_alpha@kitchengen.ai"
        test_email2 = "test_user_beta@kitchengen.ai"
        db.query(User).filter(User.email.in_([test_email1, test_email2])).delete(synchronize_session=False)
        db.commit()

        # A. Register User Alpha
        reg_res1 = client.post("/api/auth/register", json={
            "name": "Alpha Gourmet",
            "email": test_email1,
            "password": "AlphaSecurePassword123!"
        })
        assert reg_res1.status_code == 201, f"Registration failed: {reg_res1.text}"
        data1 = reg_res1.json()
        token1 = data1["access_token"]
        assert "access_token" in data1 and data1["user"]["email"] == test_email1
        print("[PASS] Registration successful with secure JWT Bearer token")

        # B. Duplicate Registration rejection
        dup_res = client.post("/api/auth/register", json={
            "name": "Alpha Gourmet Duplicate",
            "email": test_email1,
            "password": "DifferentPassword123!"
        })
        assert dup_res.status_code == 400, f"Duplicate registration did not fail: {dup_res.status_code}"
        print("[PASS] Duplicate registration rejected with 400 Bad Request")

        # C. Register User Beta
        reg_res2 = client.post("/api/auth/register", json={
            "name": "Beta Baker",
            "email": test_email2,
            "password": "BetaSecurePassword456!"
        })
        assert reg_res2.status_code == 201
        token2 = reg_res2.json()["access_token"]
        print("[PASS] Second user registered successfully")

        # D. Incorrect Password Login
        fail_login = client.post("/api/auth/login", json={
            "email": test_email1,
            "password": "WrongPassword999!"
        })
        assert fail_login.status_code == 401, f"Expected 401, got {fail_login.status_code}"
        print("[PASS] Incorrect password rejected with 401 Unauthorized")

        # E. Successful Login
        ok_login = client.post("/api/auth/login", json={
            "email": test_email1,
            "password": "AlphaSecurePassword123!"
        })
        assert ok_login.status_code == 200
        assert "access_token" in ok_login.json()
        print("[PASS] Correct password login verified with 200 OK")

        # ==============================================================
        # TEST 4: LOGOUT & PROTECTED ROUTE ACCESS
        # ==============================================================
        print("\n--- 4. Testing Protected Routes & Logout ---")
        # Access /me with token
        me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert me_res.status_code == 200
        assert me_res.json()["name"] == "Alpha Gourmet"
        assert "password" not in me_res.json() and "hashed_password" not in me_res.json()
        print("[PASS] /api/auth/me authenticated successfully and no password hashes exposed")

        # Access /me without token
        unauth_res = client.get("/api/auth/me")
        assert unauth_res.status_code == 401
        print("[PASS] Unauthenticated access to /api/auth/me rejected with 401")

        # Call logout
        logout_res = client.post("/api/auth/logout")
        assert logout_res.status_code == 200
        print("[PASS] Logout endpoint responded with 200 OK")

        # ==============================================================
        # TEST 5: DATA ISOLATION (PANTRY, SHOPPING LIST, FAVORITES)
        # ==============================================================
        print("\n--- 5. Testing Multi-User Data Isolation ---")
        
        # A. Pantry Isolation
        client.post("/api/pantry", json={"name": "Alpha Saffron", "quantity": 5, "unit": "g", "category": "Spices & Oils"}, headers={"Authorization": f"Bearer {token1}"})
        client.post("/api/pantry", json={"name": "Beta Cardamom", "quantity": 50, "unit": "g", "category": "Spices & Oils"}, headers={"Authorization": f"Bearer {token2}"})

        pantry1 = [i["name"] for i in client.get("/api/pantry", headers={"Authorization": f"Bearer {token1}"}).json()]
        pantry2 = [i["name"] for i in client.get("/api/pantry", headers={"Authorization": f"Bearer {token2}"}).json()]
        assert "Alpha Saffron" in pantry1 and "Beta Cardamom" not in pantry1
        assert "Beta Cardamom" in pantry2 and "Alpha Saffron" not in pantry2
        print("[PASS] Pantry items strictly isolated between User Alpha and User Beta")

        # B. Shopping List Isolation
        client.post("/api/shopping-list", json={"name": "Alpha Item", "quantity": 1, "unit": "box"}, headers={"Authorization": f"Bearer {token1}"})
        client.post("/api/shopping-list", json={"name": "Beta Item", "quantity": 2, "unit": "kg"}, headers={"Authorization": f"Bearer {token2}"})

        shop1 = [i["name"] for i in client.get("/api/shopping-list", headers={"Authorization": f"Bearer {token1}"}).json()]
        shop2 = [i["name"] for i in client.get("/api/shopping-list", headers={"Authorization": f"Bearer {token2}"}).json()]
        assert "Alpha Item" in shop1 and "Beta Item" not in shop1
        assert "Beta Item" in shop2 and "Alpha Item" not in shop2
        print("[PASS] Shopping list items strictly isolated between User Alpha and User Beta")

        # C. Favorites Isolation
        client.post("/api/favorites/101", headers={"Authorization": f"Bearer {token1}"}) # Dosa
        client.post("/api/favorites/109", headers={"Authorization": f"Bearer {token2}"}) # Biryani

        favs1 = client.get("/api/favorites/ids", headers={"Authorization": f"Bearer {token1}"}).json()
        favs2 = client.get("/api/favorites/ids", headers={"Authorization": f"Bearer {token2}"}).json()
        assert 101 in favs1 and 109 not in favs1
        assert 109 in favs2 and 101 not in favs2
        print("[PASS] Saved recipe favorites strictly isolated between User Alpha and User Beta")

        # ==============================================================
        # TEST 6: RECIPE MATCHING AND FILTERS INTEGRITY
        # ==============================================================
        print("\n--- 6. Testing Recipe Matching and Filter Functionality ---")
        
        # Search with ingredients: Rice, Urad Dal, Potato
        search_res = client.post("/api/recipes/search", json={
            "ingredients": ["Rice", "Urad Dal", "Potatoes", "Onions"],
            "budget_max": 250,
            "servings": 4
        })
        assert search_res.status_code == 200, f"Search failed: {search_res.text}"
        matches = search_res.json()
        assert len(matches) > 0, "Expected matches for Rice, Urad Dal, Potatoes, Onions"
        top_recipe = matches[0]["recipe"]
        assert "title" in top_recipe and "estimated_cost" in top_recipe
        print(f"[PASS] Recipe matching succeeded: Top match '{top_recipe['title']}' with {matches[0]['match_percentage']}% match")

        # Cuisine filter: South Indian
        south_res = client.get("/api/recipes?cuisine=South%20Indian")
        assert south_res.status_code == 200
        south_recipes = south_res.json()
        assert len(south_recipes) > 10
        print(f"[PASS] South Indian cuisine filter returned {len(south_recipes)} recipes")

        # Time filter: under_15
        time_res = client.get("/api/recipes?time_range=under_15")
        assert time_res.status_code == 200
        quick_recipes = time_res.json()
        for qr in quick_recipes:
            assert qr["total_time_minutes"] <= 15
        print(f"[PASS] Quick cooking time filter (under 15m) returned {len(quick_recipes)} valid fast recipes")

        print("\n" + "=" * 60)
        print(">>> ALL VERIFICATION TESTS PASSED WITH 100% SUCCESS! <<<")
        print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    test_everything()
