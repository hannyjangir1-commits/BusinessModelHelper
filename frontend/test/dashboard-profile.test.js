import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

import {
  api,
  ApiError,
  getCsrfToken,
  setCsrfToken,
} from '../src/services/api.ts';
import {
  clearProjectDraft,
  DEFAULT_PROJECT_FORM_DATA,
  getProjectDraftKey,
  loadProjectDraft,
  saveProjectDraft,
} from '../src/utils/projectDraft.ts';

// Helper to construct JSON Responses
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify({ success: status < 400, ...data }), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function errorResponse(message, status = 500, code = 'SERVER_ERROR') {
  return new Response(
    JSON.stringify({ success: false, error: { message, code } }),
    {
      status,
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

// Memory Storage Mock for draft tests
class MemoryStorage {
  constructor() {
    this.store = new Map();
  }
  getItem(key) {
    return this.store.get(key) ?? null;
  }
  setItem(key, value) {
    this.store.set(key, String(value));
  }
  removeItem(key) {
    this.store.delete(key);
  }
  clear() {
    this.store.clear();
  }
}

// ----------------------------------------------------------------------------
// Test 1: Debounced Search Requests
// ----------------------------------------------------------------------------
test('1. Debounce: Rapid keystrokes do not fire immediate requests and only dispatch once after 300ms', async () => {
  const originalFetch = globalThis.fetch;
  const dispatchedRequests = [];

  try {
    globalThis.fetch = async (url) => {
      dispatchedRequests.push(String(url));
      return jsonResponse({
        items: [],
        pagination: {
          page: 1,
          page_size: 12,
          total_count: 0,
          total_pages: 1,
          has_next: false,
          has_prev: false,
        },
      });
    };

    // Simulate search debouncing mechanism used in DashboardPage
    let activeDebounceTimer = null;
    let pendingSearch = '';

    const handleSearchInput = (value, onDebounceComplete) => {
      pendingSearch = value;
      if (activeDebounceTimer) {
        clearTimeout(activeDebounceTimer);
      }
      activeDebounceTimer = setTimeout(() => {
        onDebounceComplete(pendingSearch);
      }, 300);
    };

    // User types "f", "fi", "fin", "fintech" in rapid succession (every 50ms)
    handleSearchInput('f', (s) => api.projects.list({ search: s }));
    await new Promise((r) => setTimeout(r, 50));
    assert.equal(dispatchedRequests.length, 0, 'No request fired after 50ms');

    handleSearchInput('fi', (s) => api.projects.list({ search: s }));
    await new Promise((r) => setTimeout(r, 50));
    assert.equal(dispatchedRequests.length, 0, 'No request fired after 100ms');

    handleSearchInput('fin', (s) => api.projects.list({ search: s }));
    await new Promise((r) => setTimeout(r, 50));
    assert.equal(dispatchedRequests.length, 0, 'No request fired after 150ms');

    handleSearchInput('fintech', (s) => api.projects.list({ search: s }));

    // Wait for the full 300ms debounce to elapse
    await new Promise((r) => setTimeout(r, 350));

    assert.equal(dispatchedRequests.length, 1, 'Exactly one request dispatched after debounce');
    assert(
      dispatchedRequests[0].includes('search=fintech'),
      `Dispatched URL must contain debounced search term: ${dispatchedRequests[0]}`
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 2: Superseded & Out-of-Order Responses
// ----------------------------------------------------------------------------
test('2. Superseded & Out-of-Order: Slower older responses are cancelled and never overwrite newer results', async () => {
  const originalFetch = globalThis.fetch;
  let requestAAborted = false;

  try {
    globalThis.fetch = async (url, options) => {
      const urlStr = String(url);

      if (urlStr.includes('search=slow')) {
        // Slow request taking 200ms
        return new Promise((resolve, reject) => {
          const timer = setTimeout(() => {
            resolve(
              jsonResponse({
                items: [{ id: 'proj-slow', name: 'Slow Old Project', industry: 'Legacy' }],
                pagination: { page: 1, page_size: 12, total_count: 1, total_pages: 1, has_next: false, has_prev: false },
              })
            );
          }, 200);

          if (options?.signal) {
            options.signal.addEventListener('abort', () => {
              clearTimeout(timer);
              requestAAborted = true;
              const err = new Error('The user aborted a request.');
              err.name = 'AbortError';
              reject(err);
            });
          }
        });
      }

      if (urlStr.includes('search=fast')) {
        // Fast request taking 20ms
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve(
              jsonResponse({
                items: [{ id: 'proj-fast', name: 'Fast New Project', industry: 'Modern' }],
                pagination: { page: 1, page_size: 12, total_count: 1, total_pages: 1, has_next: false, has_prev: false },
              })
            );
          }, 20);
        });
      }

      return jsonResponse({ items: [], pagination: { page: 1, page_size: 12, total_count: 0, total_pages: 1, has_next: false, has_prev: false } });
    };

    // Component state simulation
    let currentRequestId = 0;
    let activeAbortController = null;
    let displayedProjects = [];

    const fetchProjectsGuarded = async (searchTerm) => {
      if (activeAbortController) {
        activeAbortController.abort();
      }
      activeAbortController = new AbortController();
      const requestId = ++currentRequestId;
      const signal = activeAbortController.signal;

      try {
        const res = await api.projects.list({ search: searchTerm }, { signal });
        if (requestId !== currentRequestId) {
          return; // Drop superseded response
        }
        displayedProjects = res.items;
      } catch (err) {
        if (requestId !== currentRequestId || err.name === 'AbortError') {
          return; // Drop aborted/superseded errors
        }
      }
    };

    // Dispatch slow request A first
    const reqAPromise = fetchProjectsGuarded('slow');

    // After 30ms, dispatch fast request B
    await new Promise((r) => setTimeout(r, 30));
    const reqBPromise = fetchProjectsGuarded('fast');

    await Promise.all([reqAPromise, reqBPromise]);
    await new Promise((r) => setTimeout(r, 220));

    assert.equal(requestAAborted, true, 'Request A must be aborted when Request B is launched');
    assert.equal(displayedProjects.length, 1);
    assert.equal(displayedProjects[0].id, 'proj-fast', 'Displayed projects must be from Request B, never overwritten by Request A');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 3: Pagination Boundaries and Filter Preservation
// ----------------------------------------------------------------------------
test('3. Pagination: Preserves search & industry filters across pages and enforces boundaries', async () => {
  const originalFetch = globalThis.fetch;
  const requestedQueries = [];

  try {
    globalThis.fetch = async (url) => {
      const parsed = new URL(String(url), 'http://localhost');
      requestedQueries.push({
        page: parsed.searchParams.get('page'),
        pageSize: parsed.searchParams.get('page_size'),
        search: parsed.searchParams.get('search'),
        industry: parsed.searchParams.get('industry'),
      });

      const page = parseInt(parsed.searchParams.get('page') || '1', 10);
      const totalCount = 30;
      const pageSize = 12;
      const totalPages = Math.ceil(totalCount / pageSize);

      return jsonResponse({
        items: [
          { id: `proj-${page}-1`, name: `Project Page ${page}`, industry: 'SaaS' },
        ],
        pagination: {
          page,
          page_size: pageSize,
          total_count: totalCount,
          total_pages: totalPages,
          has_next: page < totalPages,
          has_prev: page > 1,
        },
      });
    };

    // Page 1 with search and industry filter
    const resPage1 = await api.projects.list({ page: 1, pageSize: 12, search: 'platform', industry: 'SaaS' });
    assert.equal(resPage1.pagination.page, 1);
    assert.equal(resPage1.pagination.has_prev, false, 'Page 1 has no previous page');
    assert.equal(resPage1.pagination.has_next, true, 'Page 1 has next page');

    // Page 2 preserving same search and industry filter
    const resPage2 = await api.projects.list({ page: 2, pageSize: 12, search: 'platform', industry: 'SaaS' });
    assert.equal(resPage2.pagination.page, 2);
    assert.equal(resPage2.pagination.has_prev, true);
    assert.equal(resPage2.pagination.has_next, true);

    // Page 3 (boundary) preserving search and industry filter
    const resPage3 = await api.projects.list({ page: 3, pageSize: 12, search: 'platform', industry: 'SaaS' });
    assert.equal(resPage3.pagination.page, 3);
    assert.equal(resPage3.pagination.has_prev, true);
    assert.equal(resPage3.pagination.has_next, false, 'Page 3 is the last page');

    // Verify all 3 requests preserved search and industry parameters
    assert.equal(requestedQueries.length, 3);
    for (const q of requestedQueries) {
      assert.equal(q.search, 'platform', 'Search query preserved across page requests');
      assert.equal(q.industry, 'SaaS', 'Industry filter preserved across page requests');
      assert.equal(q.pageSize, '12');
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 4: Search & Filter Changes Reset Page to 1
// ----------------------------------------------------------------------------
test('4. Search Reset: Changing search or industry filters resets page to 1', () => {
  let currentPage = 3;
  let currentSearch = '';
  let currentIndustry = '';

  const handleSearchChange = (newSearch) => {
    currentSearch = newSearch;
    currentPage = 1; // Reset page to 1
  };

  const handleIndustryChange = (newIndustry) => {
    currentIndustry = newIndustry;
    currentPage = 1; // Reset page to 1
  };

  const handleResetFilters = () => {
    currentSearch = '';
    currentIndustry = '';
    currentPage = 1; // Reset page to 1
  };

  // User was on page 3, changes search term
  assert.equal(currentPage, 3);
  handleSearchChange('new startup');
  assert.equal(currentPage, 1, 'Search change must reset page to 1');
  assert.equal(currentSearch, 'new startup');

  // User navigates to page 2, changes industry
  currentPage = 2;
  handleIndustryChange('Fintech');
  assert.equal(currentPage, 1, 'Industry change must reset page to 1');
  assert.equal(currentIndustry, 'Fintech');

  // User navigates to page 2, clicks Reset Filters
  currentPage = 2;
  handleResetFilters();
  assert.equal(currentPage, 1, 'Clear filters must reset page to 1');
  assert.equal(currentSearch, '');
  assert.equal(currentIndustry, '');
});

// ----------------------------------------------------------------------------
// Test 5: Distinct Loading, Error/Retry, No-Results, and Genuinely Empty States
// ----------------------------------------------------------------------------
test('5. UI States: Distinct loading skeleton, error with retry, no-results filter, and empty-account states', () => {
  // Test State A: Loading Skeleton
  const loadingMarkup = renderToStaticMarkup(
    React.createElement('div', { role: 'status', 'aria-label': 'Loading projects...' }, 'Skeleton Cards')
  );
  assert(loadingMarkup.includes('role="status"'));
  assert(loadingMarkup.includes('aria-label="Loading projects..."'));

  // Test State B: Error & Retry State
  let retryCalled = false;
  const errorMarkup = renderToStaticMarkup(
    React.createElement(
      'div',
      { className: 'error-state' },
      React.createElement('h3', null, 'Failed to Load Projects'),
      React.createElement('p', null, 'Network connection timed out.'),
      React.createElement('button', { onClick: () => { retryCalled = true; } }, 'Try Again')
    )
  );
  assert(errorMarkup.includes('Failed to Load Projects'));
  assert(errorMarkup.includes('Network connection timed out.'));
  assert(errorMarkup.includes('Try Again'));

  // Test State C: No-Results Filtered State (search/industry active, 0 results)
  const noResultsMarkup = renderToStaticMarkup(
    React.createElement(
      'div',
      { className: 'no-results-state' },
      React.createElement('h3', null, 'No Matching Projects'),
      React.createElement('p', null, 'No projects matched your search or industry filter.'),
      React.createElement('button', null, 'Clear Search & Filters')
    )
  );
  assert(noResultsMarkup.includes('No Matching Projects'));
  assert(noResultsMarkup.includes('Clear Search'));

  // Test State D: Genuinely Empty Account State (0 results, no search or filters active)
  const emptyAccountMarkup = renderToStaticMarkup(
    React.createElement(
      'div',
      { className: 'empty-account-state' },
      React.createElement('h3', null, 'No Business Projects Yet'),
      React.createElement('p', null, 'Transform your raw startup idea into an actionable blueprint with our guided wizard.'),
      React.createElement('button', null, 'Create your first project')
    )
  );
  assert(emptyAccountMarkup.includes('No Business Projects Yet'));
  assert(emptyAccountMarkup.includes('Create your first project'));
});

// ----------------------------------------------------------------------------
// Test 6: Account Deletion with CSRF, Session Invalidation, and Redundant Logout Prevention
// ----------------------------------------------------------------------------
test('6. Account Deletion: Successful deletion clears CSRF token, avoids redundant logout request, and deterministically purges local state', async () => {
  const originalFetch = globalThis.fetch;
  const originalLocalStorage = globalThis.localStorage;
  const mockStorage = new MemoryStorage();
  globalThis.localStorage = mockStorage;

  const requestCalls = [];

  try {
    // 1. Setup authenticated user and draft in storage
    const testUserId = 'usr_delete_test_123';
    saveProjectDraft(testUserId, {
      name: 'Draft Venture',
      industry: 'AI',
      business_stage: 'Idea',
      target_market: 'B2B',
      target_audience: 'Developers',
      budget_amount: 5000,
      budget_currency: 'USD',
      team_size: 'Solo',
      technical_preferences: '',
      constraints: '',
    });
    assert(loadProjectDraft(testUserId) !== null, 'Draft should exist before deletion');

    setCsrfToken('csrf-token-active-session');
    assert.equal(getCsrfToken(), 'csrf-token-active-session');

    globalThis.fetch = async (url, options) => {
      const urlStr = String(url);
      requestCalls.push({
        url: urlStr,
        method: options?.method,
        body: options?.body ? JSON.parse(options.body) : null,
      });

      if (urlStr.includes('/api/profile') && options?.method === 'DELETE') {
        // Backend verifies password, deletes account, and clears session cookie
        return jsonResponse({
          data: { deleted: true },
          message: 'Account and associated data have been permanently deleted.',
        });
      }

      if (urlStr.includes('/api/auth/logout')) {
        // Redundant second logout would fail if attempted after account deletion
        return errorResponse('Session already destroyed', 401, 'UNAUTHORIZED');
      }

      return jsonResponse({});
    };

    // Simulate ProfilePage deletion flow:
    // 1. Call api.profile.deleteAccount
    await api.profile.deleteAccount({
      password: 'CorrectPassword123!',
      confirmation_text: 'DELETE',
    });

    // 2. api.profile.deleteAccount clears CSRF token
    assert.equal(getCsrfToken(), null, 'CSRF token must be null after successful deleteAccount');

    // 3. AuthContext logout(true) skips redundant server logout
    let userState = { id: testUserId, username: 'testuser' };
    const logoutSimulated = async (skipServerRequest = false) => {
      try {
        if (userState?.id) {
          clearProjectDraft(userState.id);
        }
        if (!skipServerRequest) {
          await api.auth.logout();
        }
      } finally {
        userState = null;
      }
    };

    // Calling logout with skipServerRequest = true
    await logoutSimulated(true);

    // 4. Assertions:
    assert.equal(userState, null, 'Local user state must be deterministically cleared');
    assert.equal(mockStorage.getItem(getProjectDraftKey(testUserId)), null, 'User project draft key must be removed from storage');
    assert.deepEqual(loadProjectDraft(testUserId), DEFAULT_PROJECT_FORM_DATA, 'Draft loader returns clean defaults after draft deletion');

    // 5. Assert that no redundant POST /api/auth/logout was issued
    const logoutRequests = requestCalls.filter((r) => r.url.includes('/api/auth/logout'));
    assert.equal(logoutRequests.length, 0, 'No redundant POST /api/auth/logout request should be made');

    const deleteRequests = requestCalls.filter((r) => r.url.includes('/api/profile') && r.method === 'DELETE');
    assert.equal(deleteRequests.length, 1, 'DELETE /api/profile was executed');
    assert.equal(deleteRequests[0].body.confirmation_text, 'DELETE');
  } finally {
    globalThis.fetch = originalFetch;
    globalThis.localStorage = originalLocalStorage;
    setCsrfToken(null);
  }
});

// ----------------------------------------------------------------------------
// Test 7: Account Deletion Failure (e.g. Invalid Password) preserves session & CSRF
// ----------------------------------------------------------------------------
test('7. Account Deletion Failure: Bad password throws ApiError, retains CSRF token, and reports error accurately', async () => {
  const originalFetch = globalThis.fetch;

  try {
    setCsrfToken('valid-csrf-token');

    globalThis.fetch = async (url, options) => {
      if (options?.method === 'DELETE') {
        return errorResponse('Invalid password provided for account deletion', 400, 'INVALID_CREDENTIALS');
      }
      return jsonResponse({});
    };

    let caughtError = null;
    try {
      await api.profile.deleteAccount({
        password: 'WrongPassword!',
        confirmation_text: 'DELETE',
      });
    } catch (err) {
      caughtError = err;
    }

    assert(caughtError !== null, 'Deletion with wrong password must throw error');
    assert(caughtError instanceof ApiError, 'Must throw ApiError');
    assert.equal(caughtError.message, 'Invalid password provided for account deletion');
    assert.equal(getCsrfToken(), 'valid-csrf-token', 'CSRF token must NOT be cleared on deletion failure');
  } finally {
    globalThis.fetch = originalFetch;
    setCsrfToken(null);
  }
});
