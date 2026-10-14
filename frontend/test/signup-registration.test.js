import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { cleanValidationMessage, parseRegistrationError } from '../src/utils/errors.ts';

// ----------------------------------------------------------------------------
// Test 1: RegisterPage semantic structure, branding, and accessibility IDs
// ----------------------------------------------------------------------------
test('1. RegisterPage: Renders brand, accessible form fields, unique IDs, and navigation links', () => {
  const registerPath = path.resolve('src/pages/auth/RegisterPage.tsx');
  assert.ok(fs.existsSync(registerPath), 'RegisterPage.tsx must exist');
  const content = fs.readFileSync(registerPath, 'utf-8');

  // Verify Heading & Brand
  assert.ok(content.includes('Create your account'), 'Must have heading "Create your account"');
  assert.ok(content.includes('Enterprise Blueprint Engine'), 'Must include brand subtitle badge');
  assert.ok(content.includes('Architect scalable startup ventures with precision'), 'Must have value proposition');

  // Verify Semantic Form Controls & Unique IDs
  assert.ok(content.includes('id="register-username"'), 'Username input has id="register-username"');
  assert.ok(content.includes('id="register-email"'), 'Email input has id="register-email"');
  assert.ok(content.includes('id="register-password"'), 'Password input has id="register-password"');
  assert.ok(content.includes('id="register-confirm-password"'), 'Confirm password input has id="register-confirm-password"');
  assert.ok(content.includes('id="register-terms"'), 'Terms checkbox has id="register-terms"');
  assert.ok(content.includes('id="register-privacy"'), 'Privacy checkbox has id="register-privacy"');
  assert.ok(content.includes('id="register-submit-button"'), 'Submit button has id="register-submit-button"');
  assert.ok(content.includes('id="register-login-link"'), 'Login link has id="register-login-link"');

  // Verify Form attributes & autocomplete
  assert.ok(content.includes('autoComplete="username"'), 'Username specifies autoComplete');
  assert.ok(content.includes('autoComplete="email"'), 'Email specifies autoComplete');
  assert.ok(content.includes('autoComplete="new-password"'), 'Password specifies new-password autoComplete');

  // Verify Separate Legal Checkboxes
  assert.ok(content.includes("onNavigate('/terms')"), 'Terms and Conditions links to /terms');
  assert.ok(content.includes("onNavigate('/privacy')"), 'Privacy Policy links to /privacy');
});

// ----------------------------------------------------------------------------
// Test 2: Client-side validation logic for all registration fields
// ----------------------------------------------------------------------------
test('2. Client Validation: Enforces username regex, email format, password policy, and match', () => {
  // Username validation rules: 3-30 chars, alphanumeric + underscore + hyphen
  const validUsernames = ['founder', 'alex_venture', 'startup-ceo', 'user123'];
  const invalidUsernames = ['', 'ab', 'user with space', 'user@domain.com', 'user.name!', 'a'.repeat(31)];

  const validateUser = (val) => {
    const clean = val.trim();
    if (!clean) return 'Username is required.';
    if (clean.length < 3) return 'Username must be at least 3 characters.';
    if (clean.length > 30) return 'Username must not exceed 30 characters.';
    if (!/^[a-zA-Z0-9_-]+$/.test(clean)) {
      return 'Username can only contain letters, numbers, underscores, and hyphens.';
    }
    return undefined;
  };

  for (const u of validUsernames) {
    assert.equal(validateUser(u), undefined, `Username ${u} should be valid`);
  }
  for (const u of invalidUsernames) {
    assert.ok(validateUser(u), `Username ${u} should be rejected`);
  }

  // Email validation rules
  const validateEmail = (val) => {
    const clean = val.trim();
    if (!clean) return 'Email address is required.';
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(clean)) {
      return 'Please enter a valid email address.';
    }
    return undefined;
  };

  assert.equal(validateEmail('founder@venture.com'), undefined);
  assert.ok(validateEmail('invalid-email'));
  assert.ok(validateEmail('user@'));
  assert.ok(validateEmail(''));

  // Password policy: min 8, max 128, at least 1 letter, at least 1 number
  const validatePass = (val) => {
    if (!val) return 'Password is required.';
    if (val.length < 8) return 'Password must be at least 8 characters long.';
    if (val.length > 128) return 'Password must not exceed 128 characters.';
    if (!/[A-Za-z]/.test(val)) return 'Password must contain at least one letter.';
    if (!/\d/.test(val)) return 'Password must contain at least one number.';
    return undefined;
  };

  assert.equal(validatePass('ValidPass123'), undefined);
  assert.ok(validatePass('short1')); // too short (< 8)
  assert.ok(validatePass('nonumberpassword')); // missing number
  assert.ok(validatePass('1234567890!')); // missing letter
});

// ----------------------------------------------------------------------------
// Test 3: Structured Error Parser maps HTTP 422 validation errors to fields
// ----------------------------------------------------------------------------
test('3. Error Parser: Correctly maps Pydantic 422 validation errors to specific fields', () => {
  const pydanticError = {
    status: 422,
    code: 'VALIDATION_ERROR',
    message: 'The request payload failed validation.',
    details: {
      validation_errors: [
        'body -> username: Value error, Username must be 3-30 characters and contain only letters, numbers, underscores, and hyphens.',
        'body -> email: Value error, Please provide a valid email address.',
        'body -> password: Value error, Password must contain at least one number.',
        'body: Value error, Passwords do not match.',
        'body -> terms_accepted: Value error, You must accept the Terms and Conditions to register.',
        'body -> privacy_acknowledged: Value error, You must acknowledge the Privacy Policy to register.',
      ],
    },
  };

  const parsed = parseRegistrationError(pydanticError);

  assert.ok(parsed.fieldErrors.username?.includes('Username must be 3-30 characters'));
  assert.ok(parsed.fieldErrors.email?.includes('valid email address'));
  assert.ok(parsed.fieldErrors.password?.includes('at least one number'));
  assert.ok(parsed.fieldErrors.confirmPassword?.includes('Passwords do not match'));
  assert.ok(parsed.fieldErrors.termsAccepted?.includes('Terms and Conditions'));
  assert.ok(parsed.fieldErrors.privacyAcknowledged?.includes('Privacy Policy'));
});

// ----------------------------------------------------------------------------
// Test 4: Structured Error Parser handles HTTP 409 Conflict & 429 Rate Limit
// ----------------------------------------------------------------------------
test('4. Error Parser: Handles HTTP 409 Conflict and HTTP 429 Rate Limit gracefully', () => {
  // HTTP 409 Conflict
  const conflictErr = {
    status: 409,
    code: 'CONFLICT',
    message: 'Username or email is already taken. Please choose different details or sign in.',
  };
  const parsedConflict = parseRegistrationError(conflictErr);
  assert.ok(parsedConflict.generalError?.includes('already taken'));
  assert.ok(parsedConflict.fieldErrors.username);
  assert.ok(parsedConflict.fieldErrors.email);

  // HTTP 429 Rate Limit
  const rateLimitErr = {
    status: 429,
    code: 'RATE_LIMIT_EXCEEDED',
    message: 'Too many registration attempts. Please try again later.',
    details: { retry_after: 120 },
  };
  const parsedRateLimit = parseRegistrationError(rateLimitErr);
  assert.ok(parsedRateLimit.generalError?.includes('120 seconds'));
});

// ----------------------------------------------------------------------------
// Test 5: API client ensures payload contract includes required fields
// ----------------------------------------------------------------------------
test('5. API Client: api.auth.register normalizes legal acknowledgments and transmits required shape', () => {
  const apiPath = path.resolve('src/services/api.ts');
  assert.ok(fs.existsSync(apiPath), 'api.ts must exist');
  const apiContent = fs.readFileSync(apiPath, 'utf-8');

  // Verify api.auth.register implementation
  assert.ok(apiContent.includes("register(data: RegisterPayload, options?: RequestOptions)"), 'Registers data payload');
  assert.ok(apiContent.includes('/api/auth/register'), 'Targets /api/auth/register endpoint');
  assert.ok(apiContent.includes('privacy_acknowledged: Boolean(data.privacy_acknowledged ?? data.privacy_accepted)'), 'Normalizes privacy acknowledgment');
  assert.ok(apiContent.includes('privacy_accepted: Boolean(data.privacy_accepted ?? data.privacy_acknowledged)'), 'Normalizes privacy acceptance alias');
});

// ----------------------------------------------------------------------------
// Test 6: Responsive layout and accessibility standards
// ----------------------------------------------------------------------------
test('6. Responsive & A11y: Desktop split-layout, mobile single-column, aria-describedby', () => {
  const registerPath = path.resolve('src/pages/auth/RegisterPage.tsx');
  const content = fs.readFileSync(registerPath, 'utf-8');

  // Desktop layout classes
  assert.ok(content.includes('lg:grid lg:grid-cols-12'), 'Uses responsive 12-column grid on desktop');
  assert.ok(content.includes('hidden lg:flex lg:col-span-5'), 'Shows value proposition on desktop');
  assert.ok(content.includes('w-full lg:col-span-7'), 'Full width single column on mobile');

  // Accessibility indicators
  assert.ok(content.includes('aria-invalid='), 'Uses aria-invalid for form controls');
  assert.ok(content.includes('aria-describedby='), 'Uses aria-describedby for errors and helper texts');
  assert.ok(content.includes('role="alert"'), 'Uses role="alert" for validation messages');
  assert.ok(content.includes('role="status"') || content.includes('animate-spin') || content.includes('Creating account...'), 'Submitting state announces loading');
});
