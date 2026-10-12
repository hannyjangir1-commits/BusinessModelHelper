/**
 * Project intake draft storage, validation, and lifecycle management.
 *
 * Retention Strategy Decision:
 * We use `localStorage` scoped to the authenticated user ID (`aba_project_intake_draft_${userId}`).
 * Project intake involves a comprehensive 4-step wizard with sensitive business models,
 * market research, and technical constraints. Founders frequently take time, reference
 * external resources, or switch browser tabs. Using `sessionStorage` would erase their work
 * on accidental tab closes. To guarantee security and privacy on shared computers:
 * 1. Drafts are strictly scoped by user ID (User B cannot read User A's draft).
 * 2. Anonymous users never have intake drafts stored in browser storage.
 * 3. Drafts are purged on successful project creation and upon explicit user logout.
 */

export interface ProjectFormData {
  name: string;
  industry: string;
  idea_description: string;
  business_stage: string;
  target_market: string;
  target_audience: string;
  budget_amount: string;
  budget_currency: string;
  team_size: string;
  technical_preferences: string;
  constraints: string;
}

export const DEFAULT_PROJECT_FORM_DATA: ProjectFormData = {
  name: '',
  industry: '',
  idea_description: '',
  business_stage: 'idea',
  target_market: '',
  target_audience: '',
  budget_amount: '',
  budget_currency: 'USD',
  team_size: 'Solo',
  technical_preferences: '',
  constraints: '',
};

export const VALID_BUSINESS_STAGES = [
  'idea',
  'validation',
  'prototype',
  'mvp',
  'growth',
] as const;

export const VALID_BUDGET_CURRENCIES = [
  'USD',
  'EUR',
  'GBP',
  'INR',
  'CAD',
] as const;

export const VALID_TEAM_SIZES = [
  'Solo',
  '2-5',
  '5-10',
  '10+',
] as const;

export const DRAFT_STORAGE_PREFIX = 'aba_project_intake_draft';
export const LEGACY_DRAFT_KEY = 'aba_project_intake_draft';

/**
 * Generate user-scoped storage key for intake draft.
 */
export function getProjectDraftKey(userId: string): string {
  return `${DRAFT_STORAGE_PREFIX}_${userId}`;
}

/**
 * Safe localStorage reader that guards against private browsing / security exceptions.
 */
export function safeGetStorageItem(key: string): string | null {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return null;
    }
    return window.localStorage.getItem(key);
  } catch (err) {
    console.warn(`[DraftStorage] Unable to read '${key}' from storage:`, err);
    return null;
  }
}

/**
 * Safe localStorage writer that guards against quota / private browsing exceptions.
 */
export function safeSetStorageItem(key: string, value: string): boolean {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return false;
    }
    window.localStorage.setItem(key, value);
    return true;
  } catch (err) {
    console.warn(`[DraftStorage] Unable to write '${key}' to storage:`, err);
    return false;
  }
}

/**
 * Safe localStorage remover that guards against security exceptions.
 */
export function safeRemoveStorageItem(key: string): boolean {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return false;
    }
    window.localStorage.removeItem(key);
    return true;
  } catch (err) {
    console.warn(`[DraftStorage] Unable to remove '${key}' from storage:`, err);
    return false;
  }
}

/**
 * Validate and sanitize stored raw data.
 * Handles malformed schemas, non-objects, missing fields, and type coercion.
 * Returns null if data is completely unusable.
 */
export function validateAndSanitizeDraft(raw: unknown): ProjectFormData | null {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    return null;
  }

  const obj = raw as Record<string, unknown>;

  // Support envelope format: { version: 1, updatedAt: '...', data: { ... } }
  const source =
    typeof obj.data === 'object' && obj.data !== null && !Array.isArray(obj.data)
      ? (obj.data as Record<string, unknown>)
      : obj;

  const sanitizeString = (val: unknown, fallback: string): string => {
    if (typeof val === 'string') return val;
    if (typeof val === 'number') return String(val);
    return fallback;
  };

  const name = sanitizeString(source.name, DEFAULT_PROJECT_FORM_DATA.name);
  const industry = sanitizeString(source.industry, DEFAULT_PROJECT_FORM_DATA.industry);
  const idea_description = sanitizeString(
    source.idea_description,
    DEFAULT_PROJECT_FORM_DATA.idea_description
  );

  const rawStage = sanitizeString(
    source.business_stage,
    DEFAULT_PROJECT_FORM_DATA.business_stage
  );
  const business_stage = (VALID_BUSINESS_STAGES as readonly string[]).includes(rawStage)
    ? rawStage
    : DEFAULT_PROJECT_FORM_DATA.business_stage;

  const target_market = sanitizeString(
    source.target_market,
    DEFAULT_PROJECT_FORM_DATA.target_market
  );
  const target_audience = sanitizeString(
    source.target_audience,
    DEFAULT_PROJECT_FORM_DATA.target_audience
  );
  const budget_amount = sanitizeString(
    source.budget_amount,
    DEFAULT_PROJECT_FORM_DATA.budget_amount
  );

  const rawCurrency = sanitizeString(
    source.budget_currency,
    DEFAULT_PROJECT_FORM_DATA.budget_currency
  ).toUpperCase();
  const budget_currency = (VALID_BUDGET_CURRENCIES as readonly string[]).includes(rawCurrency)
    ? rawCurrency
    : DEFAULT_PROJECT_FORM_DATA.budget_currency;

  const rawTeamSize = sanitizeString(source.team_size, DEFAULT_PROJECT_FORM_DATA.team_size);
  const team_size = (VALID_TEAM_SIZES as readonly string[]).includes(rawTeamSize)
    ? rawTeamSize
    : DEFAULT_PROJECT_FORM_DATA.team_size;

  const technical_preferences = sanitizeString(
    source.technical_preferences,
    DEFAULT_PROJECT_FORM_DATA.technical_preferences
  );
  const constraints = sanitizeString(source.constraints, DEFAULT_PROJECT_FORM_DATA.constraints);

  return {
    name,
    industry,
    idea_description,
    business_stage,
    target_market,
    target_audience,
    budget_amount,
    budget_currency,
    team_size,
    technical_preferences,
    constraints,
  };
}

/**
 * Load and validate stored draft for a given authenticated user.
 * Returns default form data if unauthenticated, no draft found, or malformed.
 */
export function loadProjectDraft(userId?: string | null): ProjectFormData {
  if (!userId || !userId.trim()) {
    return { ...DEFAULT_PROJECT_FORM_DATA };
  }

  const key = getProjectDraftKey(userId);
  const raw = safeGetStorageItem(key);
  if (!raw) {
    return { ...DEFAULT_PROJECT_FORM_DATA };
  }

  try {
    const parsed = JSON.parse(raw);
    const validated = validateAndSanitizeDraft(parsed);
    return validated || { ...DEFAULT_PROJECT_FORM_DATA };
  } catch (err) {
    console.warn(`[DraftStorage] Malformed JSON in draft for user '${userId}':`, err);
    return { ...DEFAULT_PROJECT_FORM_DATA };
  }
}

/**
 * Persist draft scoped to authenticated user ID.
 * Refuses to persist for anonymous users.
 */
export function saveProjectDraft(
  userId: string | null | undefined,
  data: ProjectFormData
): boolean {
  if (!userId || !userId.trim()) {
    // Strictly do not persist sensitive intake data for anonymous users
    return false;
  }

  const key = getProjectDraftKey(userId);
  const payload = {
    version: 1,
    userId,
    updatedAt: new Date().toISOString(),
    data,
  };

  return safeSetStorageItem(key, JSON.stringify(payload));
}

/**
 * Clear draft for a specific user ID (used on project creation and logout).
 */
export function clearProjectDraft(userId?: string | null): boolean {
  if (!userId || !userId.trim()) {
    return false;
  }
  const key = getProjectDraftKey(userId);
  return safeRemoveStorageItem(key);
}

/**
 * Clear legacy un-scoped draft key to avoid cross-user contamination.
 */
export function clearLegacyProjectDraft(): boolean {
  return safeRemoveStorageItem(LEGACY_DRAFT_KEY);
}
