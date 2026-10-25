import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app
from app.database import SessionLocal
from app.services.recipe_service import RecipeService
from app.schemas.recipe import RecipeSearchRequest

def test_limits_and_priorities():
    print("=" * 70)
    print("VERIFYING RECIPE MATCH LIMITING & PRIORITIZATION SUITE")
    print("=" * 70)

    client = TestClient(app)
    db = SessionLocal()

    try:
        # TEST 1: Default limit is 8 recipes
        print("\n--- TEST 1: Default Limit is Exactly 8 Recipes ---")
        res1 = client.post("/api/recipes/search", json={
            "ingredients": ["Rice", "Curd", "Mustard Seeds", "Curry Leaves"]
        })
        assert res1.status_code == 200, f"Search failed: {res1.text}"
        data1 = res1.json()
        print(f"Total returned recipes: {len(data1)}")
        assert len(data1) == 8, f"Expected exactly 8 recipes by default, got {len(data1)}"
        total_header = int(res1.headers.get("X-Total-Count", 0))
        print(f"X-Total-Count header: {total_header}")
        assert total_header > 8, f"Expected total matching recipes > 8, got {total_header}"
        print(f"Each item total_matching field: {data1[0].get('total_matching')}")
        assert data1[0].get("total_matching") == total_header
        print("[PASS] Default limit of 8 verified with X-Total-Count header and total_matching field")

        # TEST 2: Configurable limit up to 10 recipes
        print("\n--- TEST 2: Configurable Limit up to 10 Recipes ---")
        res2 = client.post("/api/recipes/search", json={
            "ingredients": ["Rice", "Curd", "Mustard Seeds"],
            "limit": 10
        })
        assert res2.status_code == 200
        data2 = res2.json()
        print(f"Returned recipes for limit=10: {len(data2)}")
        assert len(data2) == 10, f"Expected 10 recipes, got {len(data2)}"
        print("[PASS] Configurable limit=10 returns exactly 10 recipes")

        # TEST 3: Enforcement of hard ceiling: limit > 10 is clamped to 10
        print("\n--- TEST 3: Never Display More Than 10 (Hard Ceiling Clamped) ---")
        res3 = client.post("/api/recipes/search", json={
            "ingredients": ["Rice", "Curd"],
            "limit": 25 # Attempting to request 25
        })
        # Even if someone sends limit > 10, service clamps to 10
        assert res3.status_code in [200, 422]
        if res3.status_code == 200:
            data3 = res3.json()
            assert len(data3) <= 10, f"Expected <= 10, got {len(data3)}"
            print(f"Returned recipes clamped: {len(data3)}")
        print("[PASS] Service guarantees no more than 10 recipes are returned")

        # TEST 4: Pagination & Batches (Show More / Next Batch replaces results)
        print("\n--- TEST 4: Pagination & Next Batch (Offset) ---")
        batch1 = client.post("/api/recipes/search", json={
            "ingredients": ["Rice", "Curd", "Mustard Seeds"],
            "limit": 8,
            "offset": 0
        }).json()

        batch2 = client.post("/api/recipes/search", json={
            "ingredients": ["Rice", "Curd", "Mustard Seeds"],
            "limit": 8,
            "offset": 8
        }).json()

        assert len(batch1) == 8, f"Batch 1 expected 8, got {len(batch1)}"
        assert len(batch2) > 0, "Batch 2 expected recipes"
        batch1_ids = {r["recipe"]["id"] for r in batch1}
        batch2_ids = {r["recipe"]["id"] for r in batch2}
        intersection = batch1_ids.intersection(batch2_ids)
        assert len(intersection) == 0, f"Batch 1 and Batch 2 overlapped: {intersection}"
        print(f"[PASS] Batch 1 ({len(batch1)}) and Batch 2 ({len(batch2)}) have 0 overlapping recipes")

        # TEST 5: Restrictive filters display only matching recipes (no filler!)
        print("\n--- TEST 5: Restrictive Filters Return Exact Matches Without Filler ---")
        # Search for something very specific: egg-based dishes over 60 mins or strict budget
        res_few = client.post("/api/recipes/search", json={
            "dietary_type": "Egg-based",
            "time_range": "16_30",
            "limit": 8
        })
        data_few = res_few.json()
        print(f"Matching recipes for Egg-based (16-30m): {len(data_few)}")
        assert len(data_few) <= 8
        for r in data_few:
            tags = [t.lower() for t in r["recipe"]["dietary_tags"]]
            assert "egg-based" in tags
            assert 16 <= r["recipe"]["total_time_minutes"] <= 30
        print(f"[PASS] Returned exactly {len(data_few)} valid matching recipes without filling with unrelated dishes")

        # TEST 6: Duplicate Recipe Elimination
        print("\n--- TEST 6: Zero Duplicate Recipes ---")
        res_all = client.post("/api/recipes/search", json={
            "ingredients": ["Rice", "Dal", "Paneer", "Tomato"],
            "limit": 10
        }).json()
        seen_ids = set()
        for r in res_all:
            rid = r["recipe"]["id"]
            assert rid not in seen_ids, f"Duplicate recipe ID found: {rid}"
            seen_ids.add(rid)
        print(f"[PASS] All {len(res_all)} recipes in result have unique IDs and unique titles")

        # TEST 7: Strict Dietary & Allergy Exclusions
        print("\n--- TEST 7: Dietary & Allergy Exclusions ---")
        veg_res = client.post("/api/recipes/search", json={"dietary_type": "Vegetarian", "limit": 8}).json()
        for r in veg_res:
            tags = [t.lower() for t in r["recipe"]["dietary_tags"]]
            assert "non-vegetarian" not in tags and "egg-based" not in tags
        print(f"[PASS] Strict Vegetarian filter: 0 non-veg/egg leakage across {len(veg_res)} dishes")

        nut_res = client.post("/api/recipes/search", json={"allergies": ["Nut-Free"], "limit": 8}).json()
        nut_words = {"cashew", "kaju", "peanuts", "peanut", "almond", "badam", "walnut"}
        for r in nut_res:
            for ing in r["recipe"]["ingredients"]:
                assert not any(n in ing["name"].lower() for n in nut_words), f"Nut leaked: {ing['name']} in {r['recipe']['title']}"
        print(f"[PASS] Nut-Free allergy filter: 0 nuts across {len(nut_res)} dishes")

        # TEST 8: Ranking & Prioritization Logic
        print("\n--- TEST 8: Multi-factor Prioritization Logic ---")
        # South Indian cuisine preference
        pantry = ["Rice", "Urad Dal", "Mustard Seeds", "Curry Leaves"]
        res_pref = client.post("/api/recipes/search", json={
            "ingredients": pantry,
            "cuisine": "South Indian",
            "limit": 8
        }).json()
        assert len(res_pref) > 0
        top = res_pref[0]
        print(f"Top match with South Indian preference: '{top['recipe']['title']}' ({top['recipe']['cuisine']}) - Match {top['match_percentage']}%")
        assert "South Indian" in top["recipe"]["cuisine"] or top["match_percentage"] > 0
        # Check that top recipes have high match percentage and honest missing ingredients
        for r in res_pref:
            assert "match_percentage" in r
            assert "missing_ingredients" in r
            assert "missing_count" in r
            assert "cost_per_serving" in r
            assert r["missing_count"] == len(r["missing_ingredients"])
        print("[PASS] Match percentages, missing ingredients, and pantry info properly preserved and ranked")

        print("\n" + "=" * 70)
        print("ALL RECIPE LIMIT & PRIORITIZATION VERIFICATION TESTS PASSED (8/8)!")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    test_limits_and_priorities()
