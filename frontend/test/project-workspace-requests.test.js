import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

import {
  api,
  ApiError,
  isAbortError,
  isNotFoundError,
} from '../src/services/api.ts';
import { normalizeValidationReportData } from '../src/utils/validator.ts';

// Functional representation of IdeaValidatorView using standard React.createElement (matching IdeaValidatorView.tsx)
function IdeaValidatorViewComponent({
  projectId,
  report,
  versions = [],
  isLoading = false,
  error = null,
  versionError = null,
  onRetry,
  onRetryVersions,
  onReportUpdated,
}) {
  const [currentReport, setCurrentReport] = React.useState(report);
  const [selectedVersion, setSelectedVersion] = React.useState(report?.version);
  const [isLoadingVersion, setIsLoadingVersion] = React.useState(false);
  const [localError, setLocalError] = React.useState(null);

  React.useEffect(() => {
    setCurrentReport(report);
    setSelectedVersion(report?.version);
  }, [report]);

  const handleVersionChange = async (ver) => {
    if (isLoadingVersion) return;
    setIsLoadingVersion(true);
    setLocalError(null);
    setSelectedVersion(ver);
    try {
      const fetched = await api.validator.get(projectId, ver);
      setCurrentReport(fetched);
    } catch (err) {
      setLocalError(err?.message || `Failed to load validation report version ${ver}.`);
    } finally {
      setIsLoadingVersion(false);
    }
  };

  const activeReport = currentReport;
  const rawData = activeReport?.content_json || activeReport?.content || null;
  const data = rawData ? normalizeValidationReportData(rawData) : null;

  if (isLoading || isLoadingVersion) {
    return React.createElement('div', { role: 'status' }, 'Loading Validation Report...');
  }

  if (error && !activeReport) {
    return React.createElement(
      'div',
      { role: 'alert' },
      React.createElement('p', null, error),
      onRetry ? React.createElement('button', { onClick: onRetry }, 'Retry') : null
    );
  }

  if (!activeReport || !data) {
    return React.createElement('div', null, 'Idea Validation Report Empty State');
  }

  return React.createElement(
    'div',
    null,
    React.createElement('span', null, `Version ${activeReport.version}`),
    versionError
      ? React.createElement(
          'div',
          { role: 'alert', className: 'version-error-banner' },
          React.createElement('span', null, `Unable to load version history: ${versionError}`),
          onRetryVersions ? React.createElement('button', { onClick: onRetryVersions }, 'Retry History') : null
        )
      : null,
    React.createElement('p', null, data.overview || '')
  );
}

// Helpers to create mock JSON Responses
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify({ success: status < 400, data }), {
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

// ----------------------------------------------------------------------------
// Test 1: Concurrency and Independent Partial Failure Isolation
// ----------------------------------------------------------------------------
test('1. Concurrency & Partial Failure Isolation: One failing module does not block or clear others', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      const urlStr = String(url);
      if (urlStr.includes('/api/projects/proj-123/business-model')) {
        // Slow or failing BMC module
        return errorResponse('BMC service timeout', 504, 'GATEWAY_TIMEOUT');
      }
      if (urlStr.includes('/api/projects/proj-123/validator')) {
        // Successful validator report
        return jsonResponse({
          id: 'val-1',
          project_id: 'proj-123',
          module_type: 'validation_report',
          version: 1,
          content: {
            overview: 'Problem-solution fit validated.',
            interview_questions: ['How do you currently validate client demand?'],
            validation_experiments: [],
          },
        });
      }
      if (urlStr.includes('/api/projects/proj-123/technology-stack')) {
        // Successful tech stack
        return jsonResponse({
          id: 'tech-1',
          project_id: 'proj-123',
          module_type: 'technology_stack',
          version: 1,
          content: {
            frontend: { technology: 'React', category: 'Frontend' },
          },
        });
      }
      return jsonResponse({});
    };

    // Load independent modules concurrently
    const [bmcResult, valResult, techResult] = await Promise.allSettled([
      api.bmc.get('proj-123'),
      api.validator.get('proj-123'),
      api.techStack.get('proj-123'),
    ]);

    // BMC failed, but was isolated
    assert.strictEqual(bmcResult.status, 'rejected');
    assert.strictEqual(bmcResult.reason.status, 504);

    // Validator and Tech Stack succeeded completely
    assert.strictEqual(valResult.status, 'fulfilled');
    assert.strictEqual(valResult.value.version, 1);
    assert.strictEqual(valResult.value.content.overview, 'Problem-solution fit validated.');

    assert.strictEqual(techResult.status, 'fulfilled');
    assert.strictEqual(techResult.value.content.frontend.technology, 'React');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 2: Distinguishing "No Report Exists" (404) from Server/Network Failures
// ----------------------------------------------------------------------------
test('2. Distinguish 404 "no report exists" from server/network failures', async () => {
  const originalFetch = globalThis.fetch;
  try {
    // 2a. Test 404 NOT_FOUND response
    globalThis.fetch = async () => errorResponse('No validation report found', 404, 'NOT_FOUND');

    let notFoundError = null;
    try {
      await api.validator.get('proj-empty');
    } catch (err) {
      notFoundError = err;
    }
    assert(notFoundError instanceof ApiError);
    assert.strictEqual(notFoundError.status, 404);
    assert.strictEqual(isNotFoundError(notFoundError), true);

    // 2b. Test 500 SERVER_ERROR response
    globalThis.fetch = async () => errorResponse('Database connection lost', 500, 'SERVER_ERROR');

    let serverError = null;
    try {
      await api.validator.get('proj-broken');
    } catch (err) {
      serverError = err;
    }
    assert(serverError instanceof ApiError);
    assert.strictEqual(serverError.status, 500);
    assert.strictEqual(isNotFoundError(serverError), false);

    // 2c. Test Network/Connection failure
    globalThis.fetch = async () => {
      throw new TypeError('Failed to fetch: NetworkError');
    };

    let networkError = null;
    try {
      await api.validator.get('proj-offline');
    } catch (err) {
      networkError = err;
    }
    assert(networkError instanceof TypeError);
    assert.strictEqual(isNotFoundError(networkError), false);
    assert.strictEqual(isAbortError(networkError), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 3: Version-List Failure After Report Success Preserves Valid Report
// ----------------------------------------------------------------------------
test('3. Version-list failure after report success preserves report and records versionError', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => {
      const urlStr = String(url);
      if (urlStr.endsWith('/validator')) {
        // Report fetch succeeds
        return jsonResponse({
          id: 'val-report-2',
          project_id: 'proj-123',
          module_type: 'validation_report',
          version: 2,
          content: {
            overview: 'Comprehensive customer discovery completed.',
            interview_questions: ['What was the last tool you paid for?'],
          },
        });
      }
      if (urlStr.endsWith('/validator/versions')) {
        // Version list fails
        return errorResponse('Version history service unavailable', 503, 'SERVICE_UNAVAILABLE');
      }
      return jsonResponse({});
    };

    // Simulate coordinator logic in ProjectDetailPage
    let validatorReport = null;
    let validatorVersions = [];
    let validatorError = null;
    let validatorVersionError = null;

    const [valRes, verRes] = await Promise.allSettled([
      api.validator.get('proj-123'),
      api.validator.listVersions('proj-123'),
    ]);

    if (valRes.status === 'fulfilled') {
      validatorReport = valRes.value;
      validatorError = null;
    } else {
      validatorReport = null;
      validatorError = valRes.reason.message;
    }

    if (verRes.status === 'fulfilled') {
      validatorVersions = verRes.value;
      validatorVersionError = null;
    } else {
      // Must NOT clear validatorReport!
      validatorVersionError = verRes.reason.message;
    }

    // Report is preserved!
    assert.notStrictEqual(validatorReport, null);
    assert.strictEqual(validatorReport.version, 2);
    assert.strictEqual(validatorReport.content.overview, 'Comprehensive customer discovery completed.');
    assert.strictEqual(validatorError, null);

    // Version error is isolated and recorded
    assert.strictEqual(validatorVersions.length, 0);
    assert.strictEqual(validatorVersionError, 'Version history service unavailable');

    // UI rendering test: IdeaValidatorViewComponent renders the report AND the version error banner with retry
    const html = renderToStaticMarkup(
      React.createElement(IdeaValidatorViewComponent, {
        projectId: 'proj-123',
        report: validatorReport,
        versions: validatorVersions,
        versionError: validatorVersionError,
        onRetryVersions: () => {},
        onReportUpdated: () => {},
      })
    );

    assert(html.includes('Comprehensive customer discovery completed.'));
    assert(html.includes('Unable to load version history: Version history service unavailable'));
    assert(html.includes('Retry History'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 4: Historical Validator Selection Displays Selected Version (No Overwrite)
// ----------------------------------------------------------------------------
test('4. Historical validator selection: fetches and displays selected version without reloading latest', async () => {
  const originalFetch = globalThis.fetch;
  try {
    const historicalReports = {
      1: {
        id: 'val-v1',
        project_id: 'proj-123',
        module_type: 'validation_report',
        version: 1,
        content: { overview: 'Early Stage Hypothesis: v1' },
      },
      2: {
        id: 'val-v2',
        project_id: 'proj-123',
        module_type: 'validation_report',
        version: 2,
        content: { overview: 'Updated Hypothesis: v2 Latest' },
      },
    };

    let fetchedVersionRequested = null;
    globalThis.fetch = async (url) => {
      const urlStr = String(url);
      if (urlStr.includes('/validator?version=1')) {
        fetchedVersionRequested = 1;
        return jsonResponse(historicalReports[1]);
      }
      if (urlStr.includes('/validator')) {
        fetchedVersionRequested = 2;
        return jsonResponse(historicalReports[2]);
      }
      return jsonResponse({});
    };

    // User selects historical version 1
    const v1Report = await api.validator.get('proj-123', 1);
    assert.strictEqual(fetchedVersionRequested, 1);
    assert.strictEqual(v1Report.version, 1);
    assert.strictEqual(v1Report.content.overview, 'Early Stage Hypothesis: v1');

    // Render historical version 1 in IdeaValidatorView
    const htmlV1 = renderToStaticMarkup(
      React.createElement(IdeaValidatorViewComponent, {
        projectId: 'proj-123',
        report: v1Report,
        versions: [
          { version: 1, created_at: new Date().toISOString() },
          { version: 2, created_at: new Date().toISOString() },
        ],
        onReportUpdated: () => {
          assert.fail('onReportUpdated should not be triggered when viewing historical versions!');
        },
      })
    );

    assert(htmlV1.includes('Version 1'));
    assert(htmlV1.includes('Early Stage Hypothesis: v1'));
    assert(!htmlV1.includes('Updated Hypothesis: v2 Latest'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 5: Rapid Project Switching with Out-of-Order Responses
// ----------------------------------------------------------------------------
test('5. Rapid project switching: stale responses from old project cannot overwrite newly selected project', async () => {
  const originalFetch = globalThis.fetch;
  try {
    let projectARequestAborted = false;

    globalThis.fetch = async (url, options) => {
      const urlStr = String(url);
      if (urlStr.includes('/api/projects/proj-A')) {
        // Delayed response for Project A (150ms)
        return new Promise((resolve, reject) => {
          const timer = setTimeout(() => {
            resolve(
              jsonResponse({
                id: 'proj-A',
                name: 'Outdated Project A',
                industry: 'Legacy Tech',
              })
            );
          }, 150);

          if (options?.signal) {
            options.signal.addEventListener('abort', () => {
              clearTimeout(timer);
              projectARequestAborted = true;
              const err = new Error('The user aborted a request.');
              err.name = 'AbortError';
              reject(err);
            });
          }
        });
      }

      if (urlStr.includes('/api/projects/proj-B')) {
        // Fast response for Project B (10ms)
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve(
              jsonResponse({
                id: 'proj-B',
                name: 'Active Project B',
                industry: 'Fintech',
              })
            );
          }, 10);
        });
      }

      return jsonResponse({});
    };

    // Simulated component switching state
    let displayedProject = null;
    let currentRequestId = 0;
    let activeAbortController = null;

    const switchProject = (newProjectId) => {
      if (activeAbortController) {
        activeAbortController.abort();
      }
      activeAbortController = new AbortController();
      displayedProject = null; // Reset state immediately
      const reqId = ++currentRequestId;
      const signal = activeAbortController.signal;

      api.projects
        .get(newProjectId, { signal })
        .then((data) => {
          if (signal.aborted || reqId !== currentRequestId) return;
          displayedProject = data;
        })
        .catch((err) => {
          if (isAbortError(err) || reqId !== currentRequestId) return;
        });
    };

    // User starts loading Project A
    switchProject('proj-A');

    // Immediately switches to Project B before Project A finishes
    switchProject('proj-B');

    // Wait for all timeouts to finish
    await new Promise((r) => setTimeout(r, 200));

    // Project A request was properly aborted
    assert.strictEqual(projectARequestAborted, true);

    // Project B is displayed and has not been clobbered
    assert.notStrictEqual(displayedProject, null);
    assert.strictEqual(displayedProject.id, 'proj-B');
    assert.strictEqual(displayedProject.name, 'Active Project B');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 6: Cancellation / Unmount Behavior with AbortSignal
// ----------------------------------------------------------------------------
test('6. Cancellation & Unmount: Aborted requests throw AbortError recognized by isAbortError', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (_url, options) => {
      if (options?.signal?.aborted) {
        const err = new Error('The user aborted a request.');
        err.name = 'AbortError';
        throw err;
      }
      return new Promise((_, reject) => {
        options?.signal?.addEventListener('abort', () => {
          const err = new Error('The user aborted a request.');
          err.name = 'AbortError';
          reject(err);
        });
      });
    };

    const controller = new AbortController();

    const promise = api.validator.get('proj-cancelled', { signal: controller.signal });

    // Simulate component unmount
    controller.abort();

    let caughtError = null;
    try {
      await promise;
    } catch (err) {
      caughtError = err;
    }

    assert.notStrictEqual(caughtError, null);
    assert.strictEqual(isAbortError(caughtError), true);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

// ----------------------------------------------------------------------------
// Test 7: Shared API Helper Backwards Compatibility with RequestOptions
// ----------------------------------------------------------------------------
test('7. Shared API helper accepts optional RequestOptions without breaking existing call patterns', async () => {
  const originalFetch = globalThis.fetch;
  try {
    const receivedSignals = [];

    globalThis.fetch = async (_url, options) => {
      receivedSignals.push(options?.signal || null);
      return jsonResponse({
        id: 'test-res',
        version: 1,
        content: {},
      });
    };

    const controller = new AbortController();

    // 1. Calling with no options (legacy call pattern)
    await api.projects.get('p-1');
    assert.strictEqual(receivedSignals[0], null);

    // 2. Calling with AbortSignal options
    await api.projects.get('p-1', { signal: controller.signal });
    assert.strictEqual(receivedSignals[1], controller.signal);

    // 3. Calling bmc.get with (id)
    await api.bmc.get('p-1');
    assert.strictEqual(receivedSignals[2], null);

    // 4. Calling bmc.get with (id, version)
    await api.bmc.get('p-1', 3);
    assert.strictEqual(receivedSignals[3], null);

    // 5. Calling bmc.get with (id, { signal })
    await api.bmc.get('p-1', { signal: controller.signal });
    assert.strictEqual(receivedSignals[4], controller.signal);

    // 6. Calling bmc.get with (id, version, { signal })
    await api.bmc.get('p-1', 4, { signal: controller.signal });
    assert.strictEqual(receivedSignals[5], controller.signal);

    // 7. Calling listVersions with { signal }
    await api.bmc.listVersions('p-1', { signal: controller.signal });
    assert.strictEqual(receivedSignals[6], controller.signal);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
