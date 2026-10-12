import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import fs from 'node:fs';
import path from 'node:path';

// ----------------------------------------------------------------------------
// Test 1: Modal Focus Trap, Escape, and Aria Attributes in Component Source & Rendering
// ----------------------------------------------------------------------------
test('1. Modal: Has focus trap logic, Escape handler, aria-modal="true", and restores focus', () => {
  const modalPath = path.resolve('src/components/ui/Modal.tsx');
  assert(fs.existsSync(modalPath), 'Modal.tsx must exist');
  const modalContent = fs.readFileSync(modalPath, 'utf-8');

  // Verify accessibility attributes in Modal.tsx
  assert(modalContent.includes('role="dialog"'), 'Must have role="dialog"');
  assert(modalContent.includes('aria-modal="true"'), 'Must have aria-modal="true"');
  assert(modalContent.includes('aria-labelledby="modal-title"'), 'Must have aria-labelledby');
  assert(modalContent.includes('aria-describedby='), 'Must support aria-describedby');
  assert(modalContent.includes('aria-label="Close modal"'), 'Close button must have aria-label');

  // Verify focus management in Modal.tsx
  assert(modalContent.includes('previousActiveElementRef.current = document.activeElement'), 'Saves trigger element on open');
  assert(modalContent.includes('previousActiveElementRef.current.focus()'), 'Restores focus to trigger on close');
  assert(modalContent.includes("e.key === 'Escape'"), 'Closes on Escape key');
  assert(modalContent.includes("e.key === 'Tab'"), 'Traps focus on Tab / Shift+Tab');
  assert(modalContent.includes('e.shiftKey'), 'Handles Shift+Tab wrap-around');
});

// ----------------------------------------------------------------------------
// Test 2: Input Password Reveal Button & Unique IDs via useId()
// ----------------------------------------------------------------------------
test('2. Input: Password reveal button is keyboard focusable (no tabIndex=-1) and repeated fields have unique IDs', () => {
  const inputPath = path.resolve('src/components/ui/Input.tsx');
  assert(fs.existsSync(inputPath), 'Input.tsx must exist');
  const inputContent = fs.readFileSync(inputPath, 'utf-8');

  // Verify tabIndex={-1} is removed
  assert(!inputContent.includes('tabIndex={-1}'), 'Input.tsx must NOT have tabIndex={-1} on password reveal');
  assert(!inputContent.includes('tabIndex="-1"'), 'Input.tsx must NOT have tabIndex="-1" on password reveal');

  // Verify useId is used for unique ID generation
  assert(inputContent.includes('React.useId()'), 'Input.tsx must use React.useId() for accessible unique IDs');
  assert(inputContent.includes('htmlFor={inputId}'), 'Label must target inputId via htmlFor');
  assert(inputContent.includes('aria-label={showPassword ?'), 'Reveal button must toggle aria-label');

  // Verify ProfilePage gives explicit unique IDs to repeated Current Password fields
  const profilePath = path.resolve('src/pages/ProfilePage.tsx');
  const profileContent = fs.readFileSync(profilePath, 'utf-8');
  assert(profileContent.includes('id="change-password-current"'), 'Change password has unique id="change-password-current"');
  assert(profileContent.includes('id="delete-account-password"'), 'Delete account modal has unique id="delete-account-password"');
});

// ----------------------------------------------------------------------------
// Test 3: FAQ Disclosures (aria-expanded, aria-controls, stable IDs)
// ----------------------------------------------------------------------------
test('3. FAQ Disclosures: Accordion triggers in LandingPage.tsx have aria-expanded, aria-controls, and region role', () => {
  const landingPath = path.resolve('src/pages/LandingPage.tsx');
  assert(fs.existsSync(landingPath), 'LandingPage.tsx must exist');
  const landingContent = fs.readFileSync(landingPath, 'utf-8');

  assert(landingContent.includes('aria-expanded={isOpen}'), 'FAQ accordion trigger must have aria-expanded={isOpen}');
  assert(landingContent.includes('aria-controls={`faq-answer-${idx}`}'), 'FAQ trigger must have aria-controls');
  assert(landingContent.includes('id={`faq-question-${idx}`}'), 'FAQ trigger must have id');
  assert(landingContent.includes('id={`faq-answer-${idx}`}'), 'FAQ panel must have id');
  assert(landingContent.includes('role="region"'), 'FAQ answer panel must have role="region"');
  assert(landingContent.includes('aria-labelledby={`faq-question-${idx}`}'), 'FAQ answer panel must reference trigger via aria-labelledby');
});

// ----------------------------------------------------------------------------
// Test 4: Navbar Semantic Logo, Mobile Menu, and User Menu Disclosures
// ----------------------------------------------------------------------------
test('4. Navbar: Semantic button logo, aria-expanded, aria-controls for mobile & user disclosures', () => {
  const navbarPath = path.resolve('src/components/Navbar.tsx');
  assert(fs.existsSync(navbarPath), 'Navbar.tsx must exist');
  const navbarContent = fs.readFileSync(navbarPath, 'utf-8');

  // Logo is a semantic button, not a clickable div
  assert(navbarContent.includes('aria-label="AI Business Architect Home"'), 'Logo button has aria-label');
  assert(navbarContent.includes('<button'), 'Logo is rendered as a button');
  assert(!navbarContent.includes('className="flex items-center gap-2.5 cursor-pointer select-none"\n            onClick='), 'Logo must not be a non-semantic clickable div');

  // Mobile menu toggle button
  assert(navbarContent.includes('id="mobile-menu-button"'), 'Mobile menu button has stable id');
  assert(navbarContent.includes('aria-controls="mobile-navigation-menu"'), 'Mobile menu button has aria-controls');
  assert(navbarContent.includes('aria-expanded={mobileMenuOpen}'), 'Mobile menu button has aria-expanded');
  assert(navbarContent.includes('id="mobile-navigation-menu"'), 'Mobile drawer has id="mobile-navigation-menu"');

  // User menu disclosure
  assert(navbarContent.includes('id="user-menu-button"'), 'User menu button has stable id');
  assert(navbarContent.includes('aria-haspopup="true"'), 'User menu button has aria-haspopup="true"');
  assert(navbarContent.includes('aria-expanded={userDropdownOpen}'), 'User menu button has aria-expanded');
  assert(navbarContent.includes('aria-controls="user-dropdown-menu"'), 'User menu button has aria-controls');
  assert(navbarContent.includes('role="menu"'), 'User dropdown has role="menu"');
  assert(navbarContent.includes('role="menuitem"'), 'User dropdown items have role="menuitem"');
  assert(navbarContent.includes("e.key === 'Escape'"), 'Navbar closes disclosures on Escape key');
});

// ----------------------------------------------------------------------------
// Test 5: Semantic Dashboard Project Cards & Independently Operable Actions
// ----------------------------------------------------------------------------
test('5. Dashboard Cards: Semantic article, heading button, and independently operable nested actions', () => {
  const dashboardPath = path.resolve('src/pages/DashboardPage.tsx');
  assert(fs.existsSync(dashboardPath), 'DashboardPage.tsx must exist');
  const dashboardContent = fs.readFileSync(dashboardPath, 'utf-8');

  assert(dashboardContent.includes('<article'), 'Card container uses semantic <article> element');
  assert(dashboardContent.includes('aria-label={`Open project: ${project.name}`}'), 'Project title is an operable button');
  assert(dashboardContent.includes('aria-label={`Export PDF for ${project.name}`}'), 'PDF action has clear aria-label');
  assert(dashboardContent.includes('aria-label={`Delete project ${project.name}`}'), 'Delete action has clear aria-label');
  assert(!dashboardContent.includes('className="cursor-pointer flex flex-col justify-between"'), 'Card container must not be a clickable div wrapping other buttons');
});

// ----------------------------------------------------------------------------
// Test 6: Skip Navigation Link & Landmarks
// ----------------------------------------------------------------------------
test('6. Skip Navigation: Link points to #main-content and main landmark exists in App.tsx', () => {
  const appPath = path.resolve('src/App.tsx');
  assert(fs.existsSync(appPath), 'App.tsx must exist');
  const appContent = fs.readFileSync(appPath, 'utf-8');

  assert(appContent.includes('href="#main-content"'), 'Skip link targets #main-content');
  assert(appContent.includes('Skip to main content'), 'Skip link has descriptive text');
  assert(appContent.includes('id="main-content"'), 'Main landmark has id="main-content"');
  assert(appContent.includes('tabIndex={-1}'), 'Main landmark has tabIndex={-1} for keyboard focus targeting');
});

// ----------------------------------------------------------------------------
// Test 7: Color Contrast WCAG AA Verification
// ----------------------------------------------------------------------------
test('7. Contrast: Tested slate-600 (#475569) on slate-50 (#f8fafc) exceeds WCAG AA 4.5:1 ratio', () => {
  // Helper to compute luminance and contrast ratio according to WCAG 2.1 specifications
  function getLuminance(r, g, b) {
    const [rs, gs, bs] = [r, g, b].map((c) => {
      const v = c / 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }

  function getContrastRatio(rgb1, rgb2) {
    const l1 = getLuminance(...rgb1);
    const l2 = getLuminance(...rgb2);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return (lighter + 0.05) / (darker + 0.05);
  }

  // slate-600: #475569 -> (71, 85, 105)
  const slate600 = [71, 85, 105];
  // slate-50: #f8fafc -> (248, 250, 252)
  const slate50 = [248, 250, 252];
  // slate-400 (former low contrast): #94a3b8 -> (148, 163, 184)
  const slate400 = [148, 163, 184];

  const ratioSlate600 = getContrastRatio(slate600, slate50);
  const ratioSlate400 = getContrastRatio(slate400, slate50);

  assert(
    ratioSlate600 >= 4.5,
    `slate-600 on slate-50 ratio (${ratioSlate600.toFixed(2)}:1) must meet or exceed WCAG AA 4.5:1`
  );
  assert(
    ratioSlate400 < 4.5,
    `Former slate-400 on slate-50 ratio (${ratioSlate400.toFixed(2)}:1) failed WCAG AA`
  );

  // Check that MarketResearchView.tsx uses text-slate-600 for retrieved timestamp
  const mrvPath = path.resolve('src/components/modules/MarketResearchView.tsx');
  const mrvContent = fs.readFileSync(mrvPath, 'utf-8');
  assert(
    mrvContent.includes('text-slate-600') && mrvContent.includes('Retrieved {src.retrieved_at'),
    'MarketResearchView.tsx must use WCAG AA text-slate-600 for retrieved timestamp'
  );
});

// ----------------------------------------------------------------------------
// Test 8: Stylesheet print and reduced motion rules
// ----------------------------------------------------------------------------
test('8. CSS: index.css includes @media print, reduced motion, and removes overflow-x: hidden from body', () => {
  const cssPath = path.resolve('src/index.css');
  const cssContent = fs.readFileSync(cssPath, 'utf-8');

  assert(cssContent.includes('@media print'), 'index.css must include @media print stylesheet');
  assert(
    cssContent.includes('@media (prefers-reduced-motion: reduce)'),
    'index.css must include prefers-reduced-motion media query'
  );

  // Check that body does NOT have overflow-x: hidden
  const bodyBlockMatch = cssContent.match(/body\s*\{([^}]+)\}/);
  assert(bodyBlockMatch, 'Body rule must exist');
  assert(
    !bodyBlockMatch[1].includes('overflow-x: hidden'),
    'Body rule must NOT contain overflow-x: hidden masking horizontal overflow'
  );
});
