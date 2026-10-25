import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal, engine, Base
from app.models.recipe import Recipe
from app.services.recipe_service import RecipeService
from app.schemas.recipe import RecipeSearchRequest

def run_tests():
    print("--- 1. Testing Database Seeding & Recipe Count ---")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        RecipeService.seed_initial_data(db)
        total_count = db.query(Recipe).count()
        print(f"Total recipes in database: {total_count}")
        assert total_count >= 100, f"Expected at least 100 recipes, got {total_count}"

        print("\n--- 2. Testing Regional Cuisines Coverage ---")
        cuisines = {r.cuisine for r in db.query(Recipe.cuisine).all()}
        print(f"Found {len(cuisines)} distinct cuisines: {sorted(list(cuisines))}")
        expected_cuisines = [
            "South Indian", "North Indian", "Andhra", "Telangana", "Tamil Nadu",
            "Kerala", "Karnataka", "Punjabi", "Gujarati", "Rajasthani",
            "Maharashtrian", "Bengali", "Kashmiri", "Odia", "Assamese", "Goan"
        ]
        for c in expected_cuisines:
            matching = [x for x in cuisines if c.lower() in x.lower()]
            print(f"Cuisine '{c}': {'Found (' + ', '.join(matching) + ')' if matching else 'MISSING'}")
            assert len(matching) > 0, f"Missing cuisine {c}"

        print("\n--- 3. Testing Meal Category Filtering ---")
        for cat in ["Breakfast", "Lunch", "Dinner", "Snacks", "All Meals"]:
            req = RecipeSearchRequest(meal_category=cat)
            res = RecipeService.match_and_filter(db, req)
            print(f"Meal category '{cat}': {len(res)} matching recipes")
            assert len(res) > 0, f"No recipes found for meal category '{cat}'"
            if cat != "All Meals":
                for r in res:
                    cats = [c.lower() for c in r.recipe.meal_categories]
                    assert cat.lower() in cats or r.recipe.category.lower() == cat.lower(), f"Recipe {r.recipe.title} does not match {cat}"

        print("\n--- 4. Testing Cooking Time Ranges ---")
        time_ranges = [
            ("under_15", lambda t: t <= 15),
            ("16_30", lambda t: 16 <= t <= 30),
            ("31_45", lambda t: 31 <= t <= 45),
            ("46_60", lambda t: 46 <= t <= 60),
            ("over_60", lambda t: t > 60),
            ("any", lambda t: True)
        ]
        for tr_name, validator in time_ranges:
            req = RecipeSearchRequest(time_range=tr_name)
            res = RecipeService.match_and_filter(db, req)
            print(f"Time range '{tr_name}': {len(res)} recipes")
            assert len(res) > 0, f"No recipes found for time range '{tr_name}'"
            for r in res:
                assert validator(r.recipe.total_time_minutes), f"Recipe {r.recipe.title} total time {r.recipe.total_time_minutes} invalid for {tr_name}"

        print("\n--- 5. Testing Indian Ingredient Synonym Matching ---")
        test_queries = [
            ("atta", "Whole Wheat"),
            ("besan", "Gram Flour"),
            ("curd", "Curd or Dahi"),
            ("poha", "Flattened Rice"),
            ("paneer", "Paneer"),
            ("mustard seeds", "Mustard")
        ]
        for user_ing, target_desc in test_queries:
            req = RecipeSearchRequest(ingredients=[user_ing])
            res = RecipeService.match_and_filter(db, req)
            top_matches = [r for r in res if r.match_percentage > 0]
            print(f"Input '{user_ing}' ({target_desc}): matched {len(top_matches)} recipes. Top: {res[0].recipe.title} ({res[0].match_percentage}%)")
            assert len(top_matches) > 0, f"Synonym matching failed for '{user_ing}'"

        print("\n--- 6. Testing Strict Dietary Restrictions ---")
        # Strict Vegetarian
        req_veg = RecipeSearchRequest(dietary_type="Vegetarian")
        res_veg = RecipeService.match_and_filter(db, req_veg)
        print(f"Vegetarian recipes count: {len(res_veg)}")
        for r in res_veg:
            tags = [t.lower() for t in r.recipe.dietary_tags]
            assert "non-vegetarian" not in tags and "egg-based" not in tags, f"Non-veg recipe leaked into vegetarian: {r.recipe.title}"

        # Strict Vegan
        req_vegan = RecipeSearchRequest(dietary_type="Vegan")
        res_vegan = RecipeService.match_and_filter(db, req_vegan)
        print(f"Vegan recipes count: {len(res_vegan)}")
        for r in res_vegan:
            tags = [t.lower() for t in r.recipe.dietary_tags]
            assert "vegan" in tags, f"Non-vegan recipe in vegan filter: {r.recipe.title}"

        # Strict Egg-based
        req_egg = RecipeSearchRequest(dietary_type="Egg-based")
        res_egg = RecipeService.match_and_filter(db, req_egg)
        print(f"Egg-based recipes count: {len(res_egg)}")
        for r in res_egg:
            tags = [t.lower() for t in r.recipe.dietary_tags]
            assert "egg-based" in tags, f"Non-egg recipe in egg filter: {r.recipe.title}"

        # Strict Non-Vegetarian
        req_nonveg = RecipeSearchRequest(dietary_type="Non-Vegetarian")
        res_nonveg = RecipeService.match_and_filter(db, req_nonveg)
        print(f"Non-Vegetarian recipes count: {len(res_nonveg)}")
        for r in res_nonveg:
            tags = [t.lower() for t in r.recipe.dietary_tags]
            assert "non-vegetarian" in tags, f"Veg recipe in non-veg filter: {r.recipe.title}"

        print("\n--- 7. Testing Budget in INR ---")
        req_budget = RecipeSearchRequest(budget_max=100.0)
        res_budget = RecipeService.match_and_filter(db, req_budget)
        print(f"Recipes under Rs. 100: {len(res_budget)}")
        assert len(res_budget) > 0
        for r in res_budget:
            assert r.recipe.estimated_cost <= 100.0, f"Recipe cost exceeds 100: {r.recipe.title} ({r.recipe.estimated_cost})"

        print("\nALL BACKEND UNIT TESTS PASSED SUCCESSFULLY!")
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
