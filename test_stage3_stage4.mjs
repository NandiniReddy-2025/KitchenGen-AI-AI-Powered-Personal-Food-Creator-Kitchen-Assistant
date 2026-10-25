import fs from 'fs';
import path from 'path';

const API_BASE = 'http://127.0.0.1:8000/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, options);
  let data = null;
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await res.json();
  } else {
    data = await res.text();
  }
  return { status: res.status, data, ok: res.ok };
}

async function runStage3And4Tests() {
  console.log('🧪 Starting KitchenGen AI — Stage 3 & Stage 4 Comprehensive Verification Suite...\n');

  let passed = 0;
  let total = 0;

  function assert(condition, name, details = '') {
    total++;
    if (condition) {
      console.log(`  ✅ [PASS] ${name}`);
      passed++;
    } else {
      console.error(`  ❌ [FAIL] ${name} ${details ? '- ' + details : ''}`);
    }
  }

  // --- STAGE 4 ASSET VERIFICATION ---
  console.log('--- STAGE 4: Refrigerator Test Images & Expected Data ---');

  const rootDir = path.resolve('public/test-images/refrigerators');
  const frontDir = path.resolve('frontend/public/test-images/refrigerators');

  assert(fs.existsSync(rootDir), '1. public/test-images/refrigerators directory exists');
  assert(fs.existsSync(frontDir), '2. frontend/public/test-images/refrigerators directory exists');

  const expectedImages = [
    'indian-fridge.jpg',
    'vegetable-fridge.jpg',
    'nearly-empty-fridge.jpg',
    'full-fridge.jpg',
    'indian-ingredients-fridge.jpg',
    'breakfast-fridge.jpg',
    'fruit-fridge.jpg',
    'healthy-fridge.jpg',
    'messy-fridge.jpg',
    'organized-fridge.jpg',
    'low-light-fridge.jpg',
    'obstructed-fridge.jpg',
    'containers-fridge.jpg',
    'small-fridge.jpg',
    'mixed-indian-fridge.jpg'
  ];

  let allImagesValid = true;
  for (const imgName of expectedImages) {
    const p1 = path.join(rootDir, imgName);
    const p2 = path.join(frontDir, imgName);
    const exists = fs.existsSync(p1) && fs.existsSync(p2);
    const size = exists ? fs.statSync(p1).size : 0;
    if (!exists || size < 1000) {
      allImagesValid = false;
      console.error(`Missing or empty image: ${imgName} (size: ${size} bytes)`);
    }
  }
  assert(allImagesValid, `3. All 15 refrigerator test images exist and are non-empty valid files (${expectedImages.length} images)`);

  const expJsonPath = path.join(rootDir, 'expected-ingredients.json');
  assert(fs.existsSync(expJsonPath), '4. expected-ingredients.json exists');
  const expData = JSON.parse(fs.readFileSync(expJsonPath, 'utf8'));
  const allImagesInJson = expectedImages.every(img => Array.isArray(expData[img]) && expData[img].length > 0);
  assert(allImagesInJson, '5. expected-ingredients.json contains ground truth for all 15 images with non-empty lists');

  const readmePath = path.join(rootDir, 'README.md');
  assert(fs.existsSync(readmePath), '6. README.md exists and documents dataset');
  const readmeText = fs.readFileSync(readmePath, 'utf8');
  assert(readmeText.includes('License') && readmeText.includes('How to Upload') && readmeText.includes('How to Compare'), '7. README.md contains license, instructions, and comparison workflow');

  // --- STAGE 3 BACKEND API & INGREDIENT RECOGNITION ---
  console.log('\n--- STAGE 3: Image Upload & Recognition API ---');

  // Health
  const health = await request('/health');
  assert(health.status === 200 && health.data.status === 'healthy', '8. Backend API health check');

  // AI Status
  const aiStatus = await request('/ai/status');
  assert(aiStatus.status === 200, '9. AI Status endpoint returns 200', JSON.stringify(aiStatus.data));
  assert(aiStatus.data.configured === true, '10. Gemini AI is properly configured on backend');

  // Register & login test user
  const testEmail = `tester.stage3.${Date.now()}@kitchengen.ai`;
  const regRes = await request('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Stage 3 Tester', email: testEmail, password: 'Password123!' })
  });
  assert(regRes.status === 201 && regRes.data.access_token, '11. User registration');
  const token = regRes.data.access_token;
  const authHeaders = { Authorization: `Bearer ${token}` };

  // Validation 1: Invalid file type rejection
  const invalidFormData = new FormData();
  invalidFormData.append('file', new Blob(['test content'], { type: 'text/plain' }), 'test.txt');
  const invRes = await request('/ai/analyze-photo', {
    method: 'POST',
    headers: authHeaders,
    body: invalidFormData
  });
  assert(invRes.status === 400 && invRes.data.detail.includes('Invalid file type'), '12. Rejects invalid file types (e.g. .txt)');

  // Validation 2: Empty file rejection
  const emptyFormData = new FormData();
  emptyFormData.append('file', new Blob([], { type: 'image/jpeg' }), 'empty.jpg');
  const emptyRes = await request('/ai/analyze-photo', {
    method: 'POST',
    headers: authHeaders,
    body: emptyFormData
  });
  assert(emptyRes.status === 400 && emptyRes.data.detail.includes('empty'), '13. Rejects 0-byte empty image files');

  // Vision Analysis 1: Real test image (indian-fridge.jpg)
  console.log('  Testing Gemini Vision photo recognition on indian-fridge.jpg...');
  const imgBuffer = fs.readFileSync(path.join(rootDir, 'indian-fridge.jpg'));
  const validFormData = new FormData();
  validFormData.append('file', new Blob([imgBuffer], { type: 'image/jpeg' }), 'indian-fridge.jpg');

  const visionRes = await request('/ai/analyze-photo', {
    method: 'POST',
    headers: authHeaders,
    body: validFormData
  });

  assert(visionRes.status === 200, '14. Photo analysis returns HTTP 200');
  assert(visionRes.data.success === true, '15. Photo analysis response has success: true');
  assert(Array.isArray(visionRes.data.ingredients), '16. Photo analysis returns structured ingredients array');
  assert(visionRes.data.ingredients.length >= 3, `17. Detected ${visionRes.data.ingredients.length} visible ingredients`);

  // Check schema consistency: name, confidence
  const firstIng = visionRes.data.ingredients[0];
  assert(typeof firstIng.name === 'string' && firstIng.name.length > 0, '18a. Ingredient name is present');
  assert(typeof firstIng.confidence === 'number' && firstIng.confidence > 0, '18b. Confidence is a valid numeric score', `Confidence: ${firstIng.confidence}`);

  console.log(`    Detected items from indian-fridge.jpg: ${visionRes.data.ingredients.map(i => `${i.name} (${Math.round(i.confidence * 100)}%)`).join(', ')}`);

  // --- STAGE 3 PANTRY INTEGRATION ---
  console.log('\n--- STAGE 3: Review, Batch Addition & Pantry Integration ---');

  // Verify initial empty pantry
  const initialPantry = await request('/pantry', { headers: authHeaders });
  assert(initialPantry.status === 200 && Array.isArray(initialPantry.data), '19. Pantry retrieved successfully');
  const initialCount = initialPantry.data.length;

  // Add confirmed ingredients to pantry via batch API
  const confirmedItems = [
    { name: 'tomatoes', quantity: 2, unit: 'items', category: 'Produce' },
    { name: 'onions', quantity: 3, unit: 'items', category: 'Produce' },
    { name: 'paneer', quantity: 200, unit: 'g', category: 'Dairy & Eggs' },
    { name: 'green chillies', quantity: 5, unit: 'items', category: 'Produce' }
  ];

  const batchRes = await request('/pantry/batch', {
    method: 'POST',
    headers: { ...authHeaders, 'Content-Type': 'application/json' },
    body: JSON.stringify(confirmedItems)
  });

  assert(batchRes.status === 201, '20. Batch add confirmed ingredients returns HTTP 201');
  assert(Array.isArray(batchRes.data) && batchRes.data.length === 4, '21. Correct number of items processed');

  // Check name normalization (e.g. 'tomatoes' -> 'Tomato', 'onions' -> 'Onion', 'paneer' -> 'Paneer')
  const updatedPantry = await request('/pantry', { headers: authHeaders });
  const tomatoItem = updatedPantry.data.find(p => p.name.toLowerCase() === 'tomato');
  assert(!!tomatoItem, '22. Normalized ingredient names (e.g. "tomatoes" -> "Tomato")');
  assert(updatedPantry.data.length === initialCount + 4, `23. Pantry Inventory count updated from ${initialCount} to ${updatedPantry.data.length}`);

  // Test Duplicate Avoidance: submit duplicate items
  console.log('  Testing duplicate ingredient avoidance on re-submission...');
  const duplicateSubmission = [
    { name: 'Tomato', quantity: 1, unit: 'items', category: 'Produce' }, // duplicate
    { name: 'Ginger', quantity: 1, unit: 'piece', category: 'Produce' }  // new
  ];

  const dupRes = await request('/pantry/batch', {
    method: 'POST',
    headers: { ...authHeaders, 'Content-Type': 'application/json' },
    body: JSON.stringify(duplicateSubmission)
  });

  assert(dupRes.status === 201, '24. Duplicate submission processed successfully');
  const afterDupPantry = await request('/pantry', { headers: authHeaders });
  // Tomato should have updated quantity (2 + 1 = 3), total count should only increase by 1 for Ginger
  const tomatoAfter = afterDupPantry.data.find(p => p.name.toLowerCase() === 'tomato');
  assert(tomatoAfter.quantity === 3, '25. Avoids duplicate rows: increments quantity on existing item instead of duplicate entry', `Tomato quantity: ${tomatoAfter.quantity}`);
  assert(afterDupPantry.data.length === initialCount + 5, '26. Total pantry count accurately reflects deduplication');

  // Test Refresh AI Chef Recommendations using updated pantry
  console.log('  Testing AI Chef recommendation refresh with updated pantry...');
  const pantryNames = afterDupPantry.data.map(p => p.name);
  const recsRes = await request('/ai/recommendations', {
    method: 'POST',
    headers: { ...authHeaders, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pantry_ingredients: pantryNames,
      max_recommendations: 6
    })
  });

  assert(recsRes.status === 200, '27. AI Chef recommendations refresh successfully');
  assert(Array.isArray(recsRes.data.recommendations) && recsRes.data.recommendations.length > 0, '28. AI Chef returns personalized recommendations based on updated pantry items');
  const topRec = recsRes.data.recommendations[0];
  assert(topRec.match_percentage > 0, `29. Recommendations show matched pantry ingredients (${topRec.recipe.title}: ${topRec.match_percentage}% match)`);

  // --- VERIFY EXISTING FEATURES INTACT ---
  console.log('\n--- VERIFYING EXISTING FEATURES REMAIN INTACT ---');

  // Recipes API
  const recipes = await request('/recipes');
  assert(recipes.status === 200 && recipes.data.length >= 50, '30. Stored recipes collection intact');

  // Favorites API
  const favAdd = await request(`/favorites/${topRec.recipe.id}`, { method: 'POST', headers: authHeaders });
  assert(favAdd.status === 201, '31. User favorites add intact');
  const favGet = await request('/favorites', { headers: authHeaders });
  assert(favGet.status === 200 && favGet.data.length === 1, '32. User favorites fetch intact');

  // Shopping List API
  const shopAdd = await request('/shopping-list', {
    method: 'POST',
    headers: { ...authHeaders, 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Coriander Seeds', quantity: 50, unit: 'g', category: 'Spices & Oils' })
  });
  assert(shopAdd.status === 201, '33. Shopping list add intact');
  const shopGet = await request('/shopping-list', { headers: authHeaders });
  assert(shopGet.status === 200 && shopGet.data.length === 1, '34. Shopping list fetch intact');

  console.log('\n========================================');
  console.log(`Tests Completed: ${total} | Passed: ${passed} | Failed: ${total - passed}`);
  console.log('========================================\n');

  if (passed === total) {
    console.log('🎉 ALL 34 STAGE 3 & STAGE 4 TESTS PASSED PERFECTLY!\n');
  } else {
    process.exit(1);
  }
}

runStage3And4Tests().catch(err => {
  console.error('Test run failed with error:', err);
  process.exit(1);
});
