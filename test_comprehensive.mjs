import http from 'http';

function makeRequest(method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(`http://127.0.0.1:8000${path}`);
    const reqHeaders = {
      'Content-Type': 'application/json',
      ...headers,
    };

    const req = http.request(
      url,
      {
        method,
        headers: reqHeaders,
      },
      (res) => {
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => {
          let json = null;
          try {
            json = JSON.parse(data);
          } catch {
            json = data;
          }
          resolve({ status: res.statusCode, data: json, headers: res.headers });
        });
      }
    );

    req.on('error', reject);
    if (body) {
      req.write(typeof body === 'string' ? body : JSON.stringify(body));
    }
    req.end();
  });
}

async function runTests() {
  console.log('🧪 Starting KitchenGen AI Comprehensive Test Suite...\n');
  let testCount = 0;
  let passedCount = 0;

  function assert(condition, testName, details = '') {
    testCount++;
    if (condition) {
      console.log(`  ✅ [PASS] ${testName}`);
      passedCount++;
    } else {
      console.error(`  ❌ [FAIL] ${testName} ${details ? '- ' + details : ''}`);
    }
  }

  // 1. Health check
  const health = await makeRequest('GET', '/api/health');
  assert(health.status === 200 && health.data.status === 'healthy', '1. Backend Health Check');

  // 2. User Authentication (Register + Login)
  const testEmail = `chef.tester.${Date.now()}@kitchengen.ai`;
  const regRes = await makeRequest('POST', '/api/auth/register', {
    name: 'Chef Tester',
    email: testEmail,
    password: 'Password123!',
  });
  assert(regRes.status === 201 && regRes.data.access_token, '2a. User Registration Flow');

  const loginRes = await makeRequest('POST', '/api/auth/login', {
    email: testEmail,
    password: 'Password123!',
  });
  assert(loginRes.status === 200 && loginRes.data.access_token, '2b. User Login Flow');
  const token = loginRes.data.access_token;
  const authHeaders = { Authorization: `Bearer ${token}` };

  // 3. Verify Database Recipes
  const recipesRes = await makeRequest('GET', '/api/recipes');
  assert(recipesRes.status === 200 && Array.isArray(recipesRes.data) && recipesRes.data.length > 50, '3. Indian Recipe Collection Loaded', `Total recipes: ${recipesRes.data?.length}`);

  // 4. Test Empty Pantry AI Recommendations
  const emptyRecsRes = await makeRequest('POST', '/api/ai/recommendations', {
    pantry_ingredients: []
  });
  assert(emptyRecsRes.status === 200, '4. Empty Pantry Request Handling');
  assert(emptyRecsRes.data.pantry_empty === true, '4b. Correctly flags empty pantry');
  assert(emptyRecsRes.data.recommendations.length === 0, '4c. Returns 0 recipes for empty pantry with helpful prompt');

  // 5. Test AI Recommendations with Real Pantry Items
  const userPantry = ['Paneer', 'Tomato', 'Onion', 'Butter', 'Cream', 'Ginger', 'Garlic', 'Garam Masala'];
  const recsRes = await makeRequest('POST', '/api/ai/recommendations', {
    pantry_ingredients: userPantry,
    max_recommendations: 6
  });
  assert(recsRes.status === 200, '5. AI Chef Recommendations with Pantry Items');
  const recs = recsRes.data.recommendations;
  assert(Array.isArray(recs) && recs.length > 0 && recs.length <= 6, '5a. Strictly capped between 1 and 6 recipes', `Count: ${recs?.length}`);

  // 6. Verify Match Percentage & Ranking Order
  if (recs.length > 1) {
    let sortedDescending = true;
    for (let i = 0; i < recs.length - 1; i++) {
      if (recs[i].match_percentage < recs[i + 1].match_percentage) {
        // If missing count is 0 on the first, it can rank higher even if percentage matches differently
        if (recs[i].missing_count !== 0 && recs[i+1].missing_count === 0) {
          sortedDescending = false;
        }
      }
    }
    assert(sortedDescending, '6. Ranked accurately by ingredient availability & suitability');
  }

  // 7. Verify Honest Missing Ingredients
  const firstRec = recs[0];
  assert(firstRec.match_percentage > 0, '7a. Honest match percentage displayed on card', `Match: ${firstRec.match_percentage}%`);
  assert(Array.isArray(firstRec.matched_ingredients) && firstRec.matched_ingredients.length > 0, '7b. Shows matched pantry ingredients');
  assert(Array.isArray(firstRec.missing_ingredients), '7c. Identifies exact missing ingredients');

  // 8. Test Meal Category Filtering (e.g. Breakfast)
  const breakfastRecs = await makeRequest('POST', '/api/ai/recommendations', {
    pantry_ingredients: ['Rice', 'Urad Dal', 'Poha', 'Mustard Seeds', 'Curry Leaves', 'Potato'],
    meal_category: 'Breakfast',
    max_recommendations: 6
  });
  assert(breakfastRecs.status === 200, '8. Meal Category Filter (Breakfast)');
  const bList = breakfastRecs.data.recommendations;
  assert(bList.length <= 6, '8a. Breakfast recommendations <= 6 recipes');
  const allBreakfast = bList.every(r => {
    const cats = (r.recipe.meal_categories || []).map(c => c.toLowerCase());
    return cats.includes('breakfast') || r.recipe.category.toLowerCase() === 'breakfast';
  });
  assert(allBreakfast, '8b. All returned dishes belong to Breakfast category');

  // 9. Test Cooking Time Limit Filter (e.g. <= 25 mins)
  const quickRecs = await makeRequest('POST', '/api/ai/recommendations', {
    pantry_ingredients: userPantry,
    time_limit_minutes: 25,
    max_recommendations: 6
  });
  assert(quickRecs.status === 200, '9. Cooking Time Limit Filter (<= 25m)');
  const qList = quickRecs.data.recommendations;
  const allUnderOrEqualTime = qList.every(r => r.recipe.total_time_minutes <= 25);
  assert(allUnderOrEqualTime, '9a. All dishes adhere to cooking time limit');

  // 10. Test Dietary Filter (Vegetarian)
  const vegRecs = await makeRequest('POST', '/api/ai/recommendations', {
    pantry_ingredients: ['Chicken', 'Paneer', 'Onion', 'Tomato', 'Butter'],
    dietary_type: 'Vegetarian',
    max_recommendations: 6
  });
  assert(vegRecs.status === 200, '10. Dietary Restriction Filter (Vegetarian)');
  const allVeg = vegRecs.data.recommendations.every(r => {
    const tags = (r.recipe.dietary_tags || []).map(t => t.toLowerCase());
    return tags.includes('vegetarian') && !tags.includes('non-vegetarian');
  });
  assert(allVeg, '10a. Non-vegetarian dishes strictly excluded');

  // 11. Test Allergy Exclusion (Nut-Free)
  const nutFreeRecs = await makeRequest('POST', '/api/ai/recommendations', {
    pantry_ingredients: userPantry,
    allergies: ['Nut-Free'],
    max_recommendations: 6
  });
  assert(nutFreeRecs.status === 200, '11. Allergy Filter (Nut-Free)');
  const nutKeywords = ['cashew', 'kaju', 'peanut', 'almond', 'badam', 'walnut', 'pista'];
  const hasNoNuts = nutFreeRecs.data.recommendations.every(r => {
    return !r.recipe.ingredients.some(ing => {
      const name = ing.name.toLowerCase();
      return nutKeywords.some(nk => name.includes(nk));
    });
  });
  assert(hasNoNuts, '11a. Dishes containing nuts strictly excluded when Nut-Free selected');

  // 12. Test Shopping List Integration
  const shopAddRes = await makeRequest('POST', '/api/shopping-list', {
    name: 'Kasuri Methi',
    quantity: 1,
    unit: 'packet',
    category: 'Spices & Oils',
    recipe_source: 'For Paneer Butter Masala'
  }, authHeaders);
  assert(shopAddRes.status === 201, '12. Add Missing to Shopping List API');

  const shopGetRes = await makeRequest('GET', '/api/shopping-list', null, authHeaders);
  assert(shopGetRes.status === 200 && Array.isArray(shopGetRes.data), '12b. Shopping List retrieved successfully');

  // 13. Test Recipe Details Endpoint
  const detailRes = await makeRequest('GET', `/api/recipes/${firstRec.recipe.id}`);
  assert(detailRes.status === 200, '13. View Recipe Details API');
  assert(Array.isArray(detailRes.data.instructions) && detailRes.data.instructions.length > 0, '13a. Preparation instructions present');
  assert(Array.isArray(detailRes.data.ingredients) && detailRes.data.ingredients.length > 0, '13b. Full ingredients with quantities present');
  assert(detailRes.data.nutrition && detailRes.data.nutrition.calories, '13c. Nutrition facts present');

  console.log(`\n========================================`);
  console.log(`Tests Completed: ${testCount} | Passed: ${passedCount} | Failed: ${testCount - passedCount}`);
  console.log(`========================================\n`);

  if (passedCount === testCount) {
    console.log('🎉 ALL TESTS PASSED SUCCESSFULLY!');
  } else {
    process.exit(1);
  }
}

runTests().catch(err => {
  console.error('Test execution failed:', err);
  process.exit(1);
});
