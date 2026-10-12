import test from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_PROJECT_FORM_DATA,
  DRAFT_STORAGE_PREFIX,
  LEGACY_DRAFT_KEY,
  clearLegacyProjectDraft,
  clearProjectDraft,
  getProjectDraftKey,
  loadProjectDraft,
  safeGetStorageItem,
  safeRemoveStorageItem,
  safeSetStorageItem,
  saveProjectDraft,
  validateAndSanitizeDraft,
} from '../src/utils/projectDraft.ts';

/**
 * In-memory Web Storage implementation conforming to W3C Storage standard.
 */
class MockLocalStorage {
  constructor() {
    this._data = new Map();
    this.shouldThrow = false;
  }

  getItem(key) {
    if (this.shouldThrow) {
      throw new Error('SecurityError: The operation is insecure.');
    }
    return this._data.has(key) ? this._data.get(key) : null;
  }

  setItem(key, value) {
    if (this.shouldThrow) {
      throw new Error('QuotaExceededError: Storage quota exceeded.');
    }
    this._data.set(String(key), String(value));
  }

  removeItem(key) {
    if (this.shouldThrow) {
      throw new Error('SecurityError: The operation is insecure.');
    }
    this._data.delete(String(key));
  }

  clear() {
    this._data.clear();
  }

  get length() {
    return this._data.size;
  }

  key(index) {
    return Array.from(this._data.keys())[index] || null;
  }
}

// Polyfill window and localStorage for Node test runner
const mockStorage = new MockLocalStorage();
globalThis.window = { localStorage: mockStorage };

test('1. Restoring an existing draft returns all persisted fields faithfully', () => {
  mockStorage.clear();
  const userId = 'usr_founder_01';
  const sampleDraft = {
    name: 'QuantumRoute AI',
    industry: 'LogisticsTech',
    idea_description: 'Autonomous freight dispatching system utilizing edge reinforcement models.',
    business_stage: 'prototype',
    target_market: 'North America',
    target_audience: 'Mid-sized logistics fleets with 50-200 trucks',
    budget_amount: '15000',
    budget_currency: 'USD',
    team_size: '2-5',
    technical_preferences: 'Python, FastAPI, Redis, TimescaleDB',
    constraints: 'Sub-second dispatch calculations required',
  };

  saveProjectDraft(userId, sampleDraft);

  const restored = loadProjectDraft(userId);
  assert.equal(restored.name, 'QuantumRoute AI');
  assert.equal(restored.industry, 'LogisticsTech');
  assert.equal(restored.idea_description, sampleDraft.idea_description);
  assert.equal(restored.business_stage, 'prototype');
  assert.equal(restored.target_market, 'North America');
  assert.equal(restored.target_audience, sampleDraft.target_audience);
  assert.equal(restored.budget_amount, '15000');
  assert.equal(restored.budget_currency, 'USD');
  assert.equal(restored.team_size, '2-5');
  assert.equal(restored.technical_preferences, sampleDraft.technical_preferences);
  assert.equal(restored.constraints, sampleDraft.constraints);
});

test('2. Restoring does not overwrite draft on mount with empty initial state', () => {
  mockStorage.clear();
  const userId = 'usr_founder_02';
  const existingDraft = {
    ...DEFAULT_PROJECT_FORM_DATA,
    name: 'Saved Before Mount',
    industry: 'EdTech',
    idea_description: 'Adaptive learning engine for STEM students with verified comprehension tests.',
  };

  saveProjectDraft(userId, existingDraft);

  // Lazy state initializer simulation: synchronously loads draft before initial render
  const initialFormState = loadProjectDraft(userId);
  assert.equal(initialFormState.name, 'Saved Before Mount');
  assert.equal(initialFormState.industry, 'EdTech');

  // Verify that an initial clean render with isDirty=false does NOT overwrite stored draft
  let isDirty = false;
  const mountSaveEffect = () => {
    if (!userId || !isDirty) return;
    saveProjectDraft(userId, initialFormState);
  };
  mountSaveEffect();

  // Storage should still contain the original data intact
  const key = getProjectDraftKey(userId);
  const rawInStorage = JSON.parse(mockStorage.getItem(key));
  assert.equal(rawInStorage.data.name, 'Saved Before Mount');
  assert.equal(rawInStorage.data.industry, 'EdTech');
});

test('3. Account A/B isolation: User B cannot see, inherit, or overwrite User A draft', () => {
  mockStorage.clear();
  const userA = 'user_alpha_111';
  const userB = 'user_beta_222';

  const userADraft = {
    ...DEFAULT_PROJECT_FORM_DATA,
    name: 'Alpha Secret Stealth Concept',
    idea_description: 'Proprietary patent-pending cryptographic trading engine.',
    budget_amount: '500000',
  };

  saveProjectDraft(userA, userADraft);

  // User B loads their draft: must be clean defaults, NOT User A's data
  const userBLoaded = loadProjectDraft(userB);
  assert.equal(userBLoaded.name, '');
  assert.equal(userBLoaded.idea_description, '');
  assert.equal(userBLoaded.budget_amount, '');
  assert.notEqual(userBLoaded.name, userADraft.name);

  // User B saves their own draft
  const userBDraft = {
    ...DEFAULT_PROJECT_FORM_DATA,
    name: 'Beta Clean Project',
    idea_description: 'Social networking for pet owners.',
  };
  saveProjectDraft(userB, userBDraft);

  // Verify User A's draft remains completely intact and uncorrupted
  const userAReloaded = loadProjectDraft(userA);
  assert.equal(userAReloaded.name, 'Alpha Secret Stealth Concept');
  assert.equal(userAReloaded.budget_amount, '500000');

  // Verify anonymous user receives default form data and cannot save
  const anonLoaded = loadProjectDraft(null);
  assert.deepEqual(anonLoaded, DEFAULT_PROJECT_FORM_DATA);
  const anonSaved = saveProjectDraft(null, userADraft);
  assert.equal(anonSaved, false, 'Must not persist sensitive draft for anonymous users');
});

test('4. Logout cleanup: Purges user-scoped draft and legacy un-scoped draft', () => {
  mockStorage.clear();
  const userId = 'usr_logout_99';

  // Seed user draft and legacy draft
  saveProjectDraft(userId, {
    ...DEFAULT_PROJECT_FORM_DATA,
    name: 'Draft to Be Logged Out',
    idea_description: 'Confidential business idea requiring cleanup upon session termination.',
  });
  mockStorage.setItem(LEGACY_DRAFT_KEY, JSON.stringify({ name: 'Old Unscoped Draft' }));

  assert.notEqual(mockStorage.getItem(getProjectDraftKey(userId)), null);
  assert.notEqual(mockStorage.getItem(LEGACY_DRAFT_KEY), null);

  // Simulate logout cleanup
  clearProjectDraft(userId);
  clearLegacyProjectDraft();

  // Verify both storage keys have been eliminated
  assert.equal(mockStorage.getItem(getProjectDraftKey(userId)), null);
  assert.equal(mockStorage.getItem(LEGACY_DRAFT_KEY), null);

  // Subsequent load for that user returns clean defaults
  const afterLogout = loadProjectDraft(userId);
  assert.deepEqual(afterLogout, DEFAULT_PROJECT_FORM_DATA);
});

test('5. Malformed stored data & schema migration edge cases handled without crashing', () => {
  mockStorage.clear();
  const userId = 'usr_malformed_test';
  const key = getProjectDraftKey(userId);

  // 5a. Corrupt JSON syntax in storage
  mockStorage.setItem(key, '{ invalid json syntax ::: 123');
  const fromCorruptJson = loadProjectDraft(userId);
  assert.deepEqual(fromCorruptJson, DEFAULT_PROJECT_FORM_DATA, 'Corrupt JSON falls back to defaults');

  // 5b. Non-object primitives (strings, numbers, booleans, arrays)
  mockStorage.setItem(key, JSON.stringify('a plain string instead of object'));
  assert.deepEqual(loadProjectDraft(userId), DEFAULT_PROJECT_FORM_DATA);

  mockStorage.setItem(key, JSON.stringify([1, 2, 3, 'array']));
  assert.deepEqual(loadProjectDraft(userId), DEFAULT_PROJECT_FORM_DATA);

  mockStorage.setItem(key, JSON.stringify(null));
  assert.deepEqual(loadProjectDraft(userId), DEFAULT_PROJECT_FORM_DATA);

  // 5c. Partial / outdated schema (e.g. valid name, but missing newer fields or having unknown keys)
  mockStorage.setItem(
    key,
    JSON.stringify({
      version: 0,
      name: 'Partial Migration Project',
      industry: 'AgriTech',
      unexpected_legacy_field: 42,
    })
  );
  const sanitized = loadProjectDraft(userId);
  assert.equal(sanitized.name, 'Partial Migration Project');
  assert.equal(sanitized.industry, 'AgriTech');
  assert.equal(sanitized.business_stage, 'idea', 'Missing stage falls back to default');
  assert.equal(sanitized.budget_currency, 'USD', 'Missing currency falls back to default');
  assert.equal(sanitized.team_size, 'Solo', 'Missing team size falls back to default');

  // 5d. Out-of-bounds enum values (e.g. unknown business stage or currency)
  const invalidEnums = validateAndSanitizeDraft({
    name: 'Enum Test',
    business_stage: 'super-growth-invalid',
    budget_currency: 'DOGECOIN',
    team_size: 'Mega-Corp',
  });
  assert.equal(invalidEnums.name, 'Enum Test');
  assert.equal(invalidEnums.business_stage, 'idea', 'Invalid stage sanitized to default');
  assert.equal(invalidEnums.budget_currency, 'USD', 'Invalid currency sanitized to default');
  assert.equal(invalidEnums.team_size, 'Solo', 'Invalid team size sanitized to default');

  // 5e. Storage-disabled / private-browsing errors
  mockStorage.shouldThrow = true;
  assert.equal(safeGetStorageItem('any_key'), null);
  assert.equal(safeSetStorageItem('any_key', 'val'), false);
  assert.equal(safeRemoveStorageItem('any_key'), false);
  assert.deepEqual(loadProjectDraft(userId), DEFAULT_PROJECT_FORM_DATA);
  assert.equal(saveProjectDraft(userId, DEFAULT_PROJECT_FORM_DATA), false);
  mockStorage.shouldThrow = false;
});

test('6. Successful project creation clears draft from storage and enables clean navigation', () => {
  mockStorage.clear();
  const userId = 'usr_creator_88';
  const initialDraft = {
    ...DEFAULT_PROJECT_FORM_DATA,
    name: 'Completed SaaS Workspace',
    industry: 'FinTech',
    idea_description: 'Automated invoice factoring for cross-border freelancers.',
    budget_amount: '25000',
  };

  saveProjectDraft(userId, initialDraft);
  assert.notEqual(mockStorage.getItem(getProjectDraftKey(userId)), null);

  // Simulate successful project submission
  const simulatedCreationResponse = { id: 'proj_new_98765', name: initialDraft.name };
  let navigatedPath = null;
  const onNavigate = (path) => {
    navigatedPath = path;
  };

  // Creation completion handler
  clearProjectDraft(userId);
  onNavigate(`/projects/${simulatedCreationResponse.id}`);

  // Draft should be purged
  assert.equal(mockStorage.getItem(getProjectDraftKey(userId)), null);
  assert.equal(navigatedPath, '/projects/proj_new_98765');

  // Subsequent load is fresh clean state
  assert.deepEqual(loadProjectDraft(userId), DEFAULT_PROJECT_FORM_DATA);
});
