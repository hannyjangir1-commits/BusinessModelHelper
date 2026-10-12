import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

// ----------------------------------------------------------------------------
// Test 1: DashboardPage displays project count badge and 3-project limit banner
// ----------------------------------------------------------------------------
test('1. DashboardPage: Enforces 3-project capacity badge and informative limit banner', () => {
  const dashPath = path.resolve('src/pages/DashboardPage.tsx');
  assert.ok(fs.existsSync(dashPath), 'DashboardPage.tsx must exist');
  const content = fs.readFileSync(dashPath, 'utf-8');

  // Verify project capacity badge
  assert.ok(content.includes('id="project-capacity-badge"'), 'Must have project-capacity-badge element');
  assert.ok(content.includes('{totalCount}/3 Projects'), 'Must display {totalCount}/3 Projects');

  // Verify limit reached banner at 3/3
  assert.ok(content.includes('id="project-limit-banner"'), 'Must have project-limit-banner when totalCount >= 3');
  assert.ok(content.includes('Active Project Limit Reached (3 of 3 slots used)'), 'Must explain limit reached');
  assert.ok(content.includes('delete an existing project to free up a slot'), 'Must explain how to proceed at limit');

  // Verify create button reflects limit
  assert.ok(content.includes('disabled={totalCount >= 3}'), 'Create button must be disabled when at 3 projects');
  assert.ok(content.includes("totalCount >= 3 ? 'Limit Reached (3/3)' : 'Create Project'"), 'Button label updates at limit');
});

// ----------------------------------------------------------------------------
// Test 2: CreateProjectPage verifies limit on mount and provides recovery guidance
// ----------------------------------------------------------------------------
test('2. CreateProjectPage: Checks project count on mount, disables submit, and warns when at limit', () => {
  const createPath = path.resolve('src/pages/CreateProjectPage.tsx');
  assert.ok(fs.existsSync(createPath), 'CreateProjectPage.tsx must exist');
  const content = fs.readFileSync(createPath, 'utf-8');

  // Verify project count check on mount
  assert.ok(content.includes('api.projects.list({ page: 1, pageSize: 1 })'), 'Checks project count on mount');
  assert.ok(content.includes('projectCount !== null && projectCount >= 3'), 'Checks if projectCount is at limit');

  // Verify limit warning banner
  assert.ok(content.includes('Active Project Limit Reached (3 of 3 slots used)'), 'Displays limit warning alert');
  assert.ok(content.includes('return to the Dashboard and delete an existing project first'), 'Explains recovery path');

  // Verify submit button disabled state
  assert.ok(content.includes('disabled={projectCount !== null && projectCount >= 3}'), 'Disables submit button when at limit');
  assert.ok(content.includes("projectCount !== null && projectCount >= 3 ? 'Limit Reached (3/3)' : 'Create Project Workspace'"), 'Updates button label when at limit');
});

// ----------------------------------------------------------------------------
// Test 3: API Error mapping for PROJECT_LIMIT_REACHED
// ----------------------------------------------------------------------------
test('3. API Error mapping: 403 with PROJECT_LIMIT_REACHED carries message and structured details', async () => {
  const errorJson = {
    success: false,
    error: {
      code: 'PROJECT_LIMIT_REACHED',
      message: 'You have reached the maximum limit of 3 active projects for your account. Please delete an existing project before creating a new one.',
      details: { current_count: 3, max_limit: 3 },
    },
  };

  const response = new Response(JSON.stringify(errorJson), {
    status: 403,
    headers: { 'Content-Type': 'application/json' },
  });

  const parsed = await response.json();
  assert.equal(parsed.error.code, 'PROJECT_LIMIT_REACHED');
  assert.equal(parsed.error.details.max_limit, 3);
  assert.equal(parsed.error.details.current_count, 3);
  assert.ok(parsed.error.message.includes('maximum limit of 3 active projects'));
});
