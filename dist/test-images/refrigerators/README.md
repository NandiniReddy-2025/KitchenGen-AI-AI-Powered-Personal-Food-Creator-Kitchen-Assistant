# Refrigerator Test Images Dataset — KitchenGen AI

This collection of authentic, high-resolution refrigerator photographs is designed for evaluating and benchmarking visual ingredient recognition in **KitchenGen AI** (Stage 3 & Stage 4).

## Directory Contents & Scenarios (15 Real Test Images)

| # | Filename | Scenario Tested | Purpose & Key Characteristics | Expected Visible Ingredients |
|---|---|---|---|---|
| 1 | `indian-fridge.jpg` | Traditional Indian household refrigerator | Tests recognition of essential Indian pantry items in domestic shelves | Tomatoes, Onions, Green chillies, Coriander, Lemons, Ginger, Paneer, Curd, Milk, Ghee |
| 2 | `vegetable-fridge.jpg` | Vegetable-heavy fresh produce crisper | Tests multi-produce segmentation and crisp vegetable recognition | Cabbage, Cauliflower, Carrots, Capsicum, Tomatoes, Spinach, Cucumbers, Green beans, Broccoli |
| 3 | `nearly-empty-fridge.jpg` | Nearly empty bachelor refrigerator | Tests low ingredient count without hallucinating missing items | Milk, Eggs, Tomato, Onion, Butter, Cabbage, Pickles |
| 4 | `full-fridge.jpg` | Fully stocked family refrigerator | Tests high-density multi-shelf ingredient detection | Eggs, Milk, Capsicum, Carrots, Tomatoes, Cucumbers, Spinach, Celery, Strawberries, Blueberries, Yogurt, Cheese, Butter, Pickles, Orange juice |
| 5 | `indian-ingredients-fridge.jpg` | Core Indian cooking ingredients | Tests staple Indian curry bases and herbs | Paneer, Curd, Green chillies, Ginger, Coriander, Tomatoes, Lemons, Carrots, Capsicum, Onion |
| 6 | `breakfast-fridge.jpg` | Breakfast ingredients | Tests recognition of dairy, eggs, spreads, and breakfast staples | Eggs, Bread, Milk, Butter, Cheese, Strawberries, Orange, Yogurt |
| 7 | `fruit-fridge.jpg` | Fruit-heavy refrigerator | Tests distinct colorful fruit varieties | Apples, Oranges, Bananas, Grapes, Strawberries, Blueberries, Watermelon |
| 8 | `healthy-fridge.jpg` | Healthy-food / fitness refrigerator | Tests greens, clean protein, and berries | Spinach, Broccoli, Carrots, Cucumber, Greek yogurt, Blueberries, Kiwi, Eggs, Almond butter |
| 9 | `messy-fridge.jpg` | Messy / disorganized refrigerator | Tests rotated, tilted, loose, and partially wrapped items | Onion, Milk, Lemons, Green chillies, Carrots, Cheddar cheese, Pickles, Butter, Eggs, Garlic |
| 10 | `organized-fridge.jpg` | Organized acrylic bin refrigerator | Tests clear containerized and separated items | Tomatoes, Cucumbers, Capsicum, Limes, Eggs, Milk, Orange juice, Lemons, Butter, Yogurt |
| 11 | `low-light-fridge.jpg` | Low-light / dim refrigerator | Tests vision performance under subdued domestic bulb illumination | Milk, Olives, Cheese, Tomato, Eggs, Orange juice |
| 12 | `obstructed-fridge.jpg` | Partially obstructed ingredients | Tests robustness when foreground items partially occlude background ingredients | Milk, Red capsicum, Cucumbers, Spinach, Carrots, Pickles, Eggs |
| 13 | `containers-fridge.jpg` | Food containers with visible ingredients | Tests steel dabbas and transparent containers holding prepped items | Paneer, Green peas, Coriander, Tomatoes, Lemons, Yogurt |
| 14 | `small-fridge.jpg` | Small compact / mini refrigerator | Tests single-compartment apartment fridge with core essentials | Milk, Eggs, Tomato, Onion, Butter |
| 15 | `mixed-indian-fridge.jpg` | Mixed Indian household refrigerator | Tests combination of cooked dishes, fresh dairy, and raw produce | Tomato, Paneer, Peas, Coriander, Lemon, Ghee, Curd |

## Ground-Truth Data

The ground-truth expected ingredients for every test photograph are stored in [`expected-ingredients.json`](./expected-ingredients.json).

```json
{
  "indian-fridge.jpg": [
    "tomatoes",
    "onions",
    "green chillies",
    "coriander",
    "lemons",
    "ginger",
    "paneer",
    "curd",
    "milk",
    "ghee"
  ]
}
```

## Image Source & License

- **License**: Royalty-Free, permissive project use.
- **Characteristics**: Realistic domestic smartphone perspectives without artificial text labels superimposed on food items, enabling true multimodal computer vision testing.
- **Integrity**: Every file is a valid, high-resolution JPEG image that can be opened, inspected, and uploaded.

## How to Upload the Image into KitchenGen AI

1. Start the backend and frontend:
   - Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` (run from `backend/`)
   - Frontend: `npm run dev` (run from `frontend/`, accessible at `http://localhost:5173`)
2. Sign in or register in KitchenGen AI.
3. Navigate to **Pantry** (or click **📸 Upload Refrigerator Photo**).
4. Click **Select Refrigerator Image** to open your file manager.
5. In the file picker, browse to `public/test-images/refrigerators/` (or `frontend/public/test-images/refrigerators/`) and select any test image, for example `indian-fridge.jpg`.
6. Preview the selected image on screen.
7. Click **Analyze Image**.
8. In the **Review Detected Ingredients** section:
   - Review detected items with their confidence ratings.
   - Edit ingredient names if needed.
   - Remove any incorrect items using the remove button.
   - Add any missing ingredients using the "+ Add Missing Ingredient" field.
9. Click **Confirm & Add to Pantry** to add all reviewed ingredients to your pantry inventory.
10. Notice the Pantry Inventory count updates immediately and AI Chef recommendations are refreshed with matches for your new pantry items!

## How to Compare Detected Ingredients with Expected Ingredients

1. Open `public/test-images/refrigerators/expected-ingredients.json`.
2. Find the entry corresponding to the uploaded image file name (e.g., `"indian-fridge.jpg"`).
3. Compare the list of returned ingredients under **Review Detected Ingredients** with the expected list.
4. Verify that:
   - Primary visible ingredients are correctly recognized with high confidence.
   - Non-existent or completely hidden ingredients are not hallucinated.
   - Ingredient names are normalized (e.g., "tomatoes" -> "Tomato").
