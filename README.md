# AI Personal Food Creator & Kitchen Assistant 🥑

A modern, responsive web application designed to help users decide what to cook based on the ingredients available in their fridge, budget constraints, dietary preferences, cooking time, and serving size.

---

## 🎨 Design Philosophy
- **Palette**: Warm cream background (`#FAF7F2`), crisp white card surfaces (`#FFFFFF`), natural sage-green accents (`#4A6B53`), and earthy terracotta highlights (`#C0603B`).
- **Typography**: Editorial modern typography pairing **Outfit** for headers and **Plus Jakarta Sans** for body and data.
- **Aesthetic**: Calm, organic culinary feel. No harsh dark themes, no neon gradients, and clean micro-interactions.

---

## 🏗️ Architecture & Technology Stack

```
Food Creator & Kitchen Assistant/
├── backend/                  # Python + FastAPI REST API
│   ├── app/
│   │   ├── config.py         # Application configuration & CORS settings
│   │   ├── database.py       # SQLite connection and session factory
│   │   ├── models/           # SQLAlchemy DB models (Recipe, PantryItem, ShoppingListItem)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Fuzzy ingredient matching & curated culinary datasets
│   │   ├── routes/           # Endpoints for health, recipes, pantry, and shopping list
│   │   └── main.py           # FastAPI entrypoint with lifespan startup & DB auto-seeding
│   ├── requirements.txt      # FastAPI, Uvicorn, SQLAlchemy, Pydantic, httpx
│   ├── test_backend.py       # Verification test script
│   └── .env.example          # Template for environment configuration
│
├── frontend/                 # React 19 + Vite + Vanilla CSS
│   ├── src/
│   │   ├── components/       # Reusable UI (Navbar, RecipeCard, RecipeModal, Feedback, Icons)
│   │   ├── pages/            # Dashboard, CreatorPage, RecipeResults, PantryPage, ShoppingListPage
│   │   ├── context/          # Shared KitchenContext (pantry, active ingredients, shopping list)
│   │   ├── services/         # API fetch client communicating with backend
│   │   └── styles/           # CSS design system (variables.css, global.css, components.css)
│   ├── vite.config.js        # Vite dev server with proxy to backend port 8000
│   └── package.json
└── README.md
```

---

## ✨ Features Implemented (Milestone 1)

1. **Responsive Home Dashboard**:
   - Culinary hero banner with quick start navigation.
   - Live pantry status & shopping checklist summary counters.
   - Chef-curated recipe recommendations grid.

2. **Smart Food Creator (Ingredient Entry & Preferences)**:
   - Add ingredients by typing with instant validation and keyboard `Enter` support.
   - Quick-add common pantry staples (Garlic, Eggs, Olive oil, Chicken, Spinach, etc.) with one click.
   - Removable chip tags with remove animation.
   - One-click **"Load My Pantry"** button to transfer stored fridge inventory directly into the search.
   - **Filter Controls**:
     - Budget limit slider ($5 to $40).
     - Dietary restrictions: Vegetarian, Vegan, Gluten-Free, Dairy-Free, Low-Carb, High-Protein.
     - Cuisine selector: All, Italian, Mexican, Asian, Mediterranean, Indian, American.
     - Max cooking time: 15m, 25m, 35m, 60m.
     - Servings selector: 1, 2, 4, 6 people.

3. **Intelligent Recipe Matching & Results**:
   - Fuzzy ingredient matching algorithm computes match percentages (e.g. 100% Match, 75% Match).
   - Identifies exact missing ingredients and matched ingredients.
   - Sort by Best Match %, Shortest Cooking Time, or Lowest Cost.
   - Empty state with reset prompts if filters are too strict.

4. **Interactive Recipe Detail View**:
   - Modal drawer showing high-res culinary photography.
   - Complete ingredient list with exact quantities and units.
   - Clear visual indicators for ingredients you already have vs missing items.
   - **One-click "Add Missing to Shopping List"**: Automatically batches unowned ingredients into your shopping list.
   - Step-by-step numbered preparation instructions.
   - Nutritional breakdown (Calories, Protein, Carbs, Fat, Fiber).

5. **Pantry Inventory Manager**:
   - Track items in your fridge and cupboards with quantity, units, and estimated freshness (days to expire).
   - Category filters: Produce, Dairy & Eggs, Meat & Seafood, Pantry Staples, Spices & Oils.
   - Add new ingredient modal with input validation.
   - **"Populate Recommended Starter Fridge"** button for instant setup.
   - **"Cook with All Pantry Items"** button that sends stocked items into the Food Creator.

6. **Interactive Shopping Checklist**:
   - Displays required groceries with recipe attribution (e.g., `For Tuscan Garlic Chicken`).
   - Checkbox toggle marks items as purchased with strike-through styling.
   - Manual grocery quick-add bar.
   - "Clear Completed" button to purge purchased items.

7. **FastAPI Endpoints**:
   - `GET /api/health` — Service health check.
   - `GET /api/recipes` — Query all recipes with optional filters.
   - `POST /api/recipes/search` — Fuzzy match and rank recipes based on available ingredients.
   - `GET /api/recipes/{id}` — Full recipe details.
   - `GET/POST/PUT/DELETE /api/pantry` — Pantry item management.
   - `GET/POST/PATCH/DELETE /api/shopping-list` — Shopping checklist management.

---

## 🚀 Setup & Execution Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Running the Backend Server

Open a terminal in the project directory:

```bash
cd backend
# Activate the virtual environment
.\venv\Scripts\activate   # On Windows
# source venv/bin/activate # On macOS/Linux

# Run the FastAPI server
uvicorn app.main:app --reload --port 8000
```

The backend server will start at `http://localhost:8000`.
- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### 2. Running the Verification Test Suite

To run the automated backend test suite:

```bash
cd backend
.\venv\Scripts\python test_backend.py
```

### 3. Running the Frontend Development Server

Open a second terminal:

```bash
cd frontend
npm run dev
```

The frontend application will start at `http://localhost:5173`. Open this URL in your web browser.

---

## 🧪 Testing the Application (Step-by-Step Flow)

1. **Verify Backend Health**:
   - Visit `http://localhost:8000/api/health` in your browser or curl it. Expect: `{"status": "healthy", ...}`.
2. **Explore Dashboard**:
   - Navigate to `http://localhost:5173`. Notice the warm cream background and sage-green design.
3. **Seed or Manage Pantry**:
   - Click the **Pantry** tab. Click **"Populate Recommended Starter Fridge"** to load 9 fresh staples.
   - Click **"Cook with All Pantry Items"** — notice how it transfers the ingredients into the Food Creator!
4. **Create a Meal**:
   - In the **Food Creator**, add any ingredients (or use the loaded pantry items).
   - Adjust the budget slider or select dietary preferences (e.g., "Gluten-Free" or "Vegetarian").
   - Click **"Find Matching Recipes"**.
5. **Inspect Recipe Results & Add Missing Ingredients**:
   - View the recipe cards displaying match % badges (e.g. `100% Match` or `38% Match - Missing 5 items`).
   - Click **"View Recipe"** on any card.
   - In the recipe modal, review the step-by-step instructions.
   - If missing ingredients exist, click **"Add Missing to Shopping List"**.
6. **Check Shopping List**:
   - Navigate to the **Shopping List** tab. Verify the missing items are present with recipe attribution.
   - Click checkboxes to mark items as purchased, and click **"Clear Completed"**.
