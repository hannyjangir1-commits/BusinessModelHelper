/**
 * Structured validation error parser for backend API errors.
 * Translates FastAPI / Pydantic validation details and domain exception responses
 * into actionable field-level errors and accessible form-level messages.
 */

export interface FieldErrors {
  username?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  termsAccepted?: string;
  privacyAcknowledged?: string;
}

export interface ParsedRegistrationError {
  fieldErrors: FieldErrors;
  generalError: string | null;
}

/**
 * Strips Pydantic error prefixes like "body -> username: Value error, "
 * leaving a clean, user-friendly sentence.
 */
export function cleanValidationMessage(raw: string): string {
  if (!raw) return '';
  return raw
    .replace(/^body(\s*->\s*[^:]+)?:\s*/i, '')
    .replace(/^(Value error|String should have|Input should be)[,\s]*/i, '')
    .trim();
}

/**
 * Parses any backend error thrown during registration into structured field and form errors.
 */
export function parseRegistrationError(err: unknown): ParsedRegistrationError {
  const result: ParsedRegistrationError = {
    fieldErrors: {},
    generalError: null,
  };

  if (!err) {
    result.generalError = 'An unexpected error occurred. Please try again.';
    return result;
  }

  const apiErr = err as {
    status?: number;
    code?: string;
    message?: string;
    details?: {
      validation_errors?: string[];
      retry_after?: number;
      [key: string]: unknown;
    };
  };

  const status = apiErr.status ?? 0;
  const code = apiErr.code ?? '';
  const message = apiErr.message || '';

  // 1. HTTP 409 Conflict: Duplicate username or email
  if (status === 409 || code === 'CONFLICT') {
    const conflictMsg = message || 'Username or email is already taken. Please choose different details or sign in.';
    result.generalError = conflictMsg;
    result.fieldErrors.username = 'This username may already be in use.';
    result.fieldErrors.email = 'This email may already be registered.';
    return result;
  }

  // 2. HTTP 429 Rate Limit
  if (status === 429 || code === 'RATE_LIMIT_EXCEEDED') {
    const retryAfter = apiErr.details?.retry_after;
    result.generalError = retryAfter
      ? `Too many registration attempts. Please wait ${retryAfter} seconds before trying again.`
      : message || 'Too many registration attempts. Please try again later.';
    return result;
  }

  // 3. HTTP 422 Unprocessable Entity (Validation Error)
  if (status === 422 || code === 'VALIDATION_ERROR') {
    const validationList = apiErr.details?.validation_errors;

    if (Array.isArray(validationList) && validationList.length > 0) {
      for (const item of validationList) {
        const raw = String(item);
        const clean = cleanValidationMessage(raw);

        if (raw.includes('username')) {
          result.fieldErrors.username = clean || 'Please provide a valid username.';
        } else if (raw.includes('email')) {
          result.fieldErrors.email = clean || 'Please provide a valid email address.';
        } else if (raw.includes('confirm_password') || raw.toLowerCase().includes('passwords do not match')) {
          result.fieldErrors.confirmPassword = clean || 'Passwords do not match.';
        } else if (raw.includes('password')) {
          result.fieldErrors.password = clean || 'Password does not meet requirements.';
        } else if (raw.includes('terms_accepted') || raw.toLowerCase().includes('terms and conditions')) {
          result.fieldErrors.termsAccepted = clean || 'You must accept the Terms and Conditions to register.';
        } else if (
          raw.includes('privacy_acknowledged') ||
          raw.includes('privacy_accepted') ||
          raw.toLowerCase().includes('privacy policy')
        ) {
          result.fieldErrors.privacyAcknowledged = clean || 'You must acknowledge the Privacy Policy to register.';
        } else {
          // Unmapped validation error
          if (!result.generalError) {
            result.generalError = clean;
          }
        }
      }
    }

    // If message is a specific error (e.g. from service ValidationError)
    if (message && message !== 'The request payload failed validation.') {
      const lower = message.toLowerCase();
      if (lower.includes('password') && lower.includes('match')) {
        result.fieldErrors.confirmPassword = message;
      } else if (lower.includes('password')) {
        result.fieldErrors.password = message;
      } else if (lower.includes('username')) {
        result.fieldErrors.username = message;
      } else if (lower.includes('email')) {
        result.fieldErrors.email = message;
      } else if (lower.includes('terms')) {
        result.fieldErrors.termsAccepted = message;
      } else if (lower.includes('privacy')) {
        result.fieldErrors.privacyAcknowledged = message;
      } else if (!result.generalError) {
        result.generalError = message;
      }
    }

    if (!result.generalError && Object.keys(result.fieldErrors).length === 0) {
      result.generalError = message || 'Please check the form fields and correct the highlighted errors.';
    }

    return result;
  }

  // 4. Default fallback
  result.generalError = message || 'Registration failed. Please check your network connection and try again.';
  return result;
}
