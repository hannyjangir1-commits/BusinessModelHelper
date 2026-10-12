import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import fs from 'node:fs';
import path from 'node:path';

import { getRouteMetadata, ROUTE_METADATA_CONFIG } from '../src/utils/seo.ts';

// ----------------------------------------------------------------------------
// Test 1: Public Route SEO Metadata
// ----------------------------------------------------------------------------
test('1. Public Routes: Unique descriptive titles, descriptions, and indexable robots policy', () => {
  const publicRoutes = ['/', '/terms', '/privacy', '/acceptable-use', '/contact'];

  for (const route of publicRoutes) {
    const meta = getRouteMetadata(route);
    assert.equal(meta.isPublicIndexable, true, `${route} must be public indexable`);
    assert(meta.title.includes('AI Business Architect'), `${route} title must be branded`);
    assert(meta.description.length > 20, `${route} description must be concise and descriptive`);
    assert.equal(meta.robots, 'index, follow', `${route} robots must be index, follow`);
  }
});

// ----------------------------------------------------------------------------
// Test 2: Authenticated / Private Route Privacy Protection
// ----------------------------------------------------------------------------
test('2. Private Workspaces: Strictly generic titles without leaking user project data and noindex, nofollow', () => {
  const privateWorkspaceRoutes = [
    '/dashboard',
    '/profile',
    '/projects/new',
    '/projects/proj-secret-client-123',
    '/projects/proj-secret-client-123/canvas',
  ];

  for (const route of privateWorkspaceRoutes) {
    const meta = getRouteMetadata(route);
    assert.equal(meta.isPublicIndexable, false, `${route} must not be publicly indexable`);
    assert.equal(meta.robots, 'noindex, nofollow', `${route} must have robots="noindex, nofollow"`);
    // Ensure titles never leak specific IDs or confidential strings
    assert(!meta.title.includes('proj-secret'), `${route} title must never leak project IDs or private project content`);
    assert(meta.title.includes('AI Business Architect'));
  }
});

// ----------------------------------------------------------------------------
// Test 3: Unrecognized 404 Route Metadata & NotFoundPage Structure
// ----------------------------------------------------------------------------
test('3. 404 Routes: Unrecognized routes receive 404 metadata and NotFoundPage contains navigation recovery', () => {
  const unknownRoute = '/some/random/nonexistent/url';
  const meta = getRouteMetadata(unknownRoute);

  assert.equal(meta.isPublicIndexable, false);
  assert.equal(meta.robots, 'noindex, follow');
  assert(meta.title.includes('Page Not Found (404)'));

  // Inspect NotFoundPage.tsx source code
  const notFoundPath = path.resolve('src/pages/NotFoundPage.tsx');
  assert(fs.existsSync(notFoundPath), 'NotFoundPage.tsx must exist');
  const notFoundContent = fs.readFileSync(notFoundPath, 'utf-8');

  assert(notFoundContent.includes('Page Not Found'), 'Renders Page Not Found heading');
  assert(notFoundContent.includes('404'), 'Renders 404 indicator');
  assert(notFoundContent.includes('Return to Home'), 'Includes Return to Home button');
  assert(notFoundContent.includes('Go to Dashboard'), 'Includes Go to Dashboard button');
  assert(notFoundContent.includes('role="region"'), 'Uses accessible region container');
  assert(notFoundContent.includes('Contact Support'), 'Offers contact support option');
});

// ----------------------------------------------------------------------------
// Test 4: robots.txt Exclusion Integrity
// ----------------------------------------------------------------------------
test('4. robots.txt: Excludes private routes and API while allowing public marketing pages', () => {
  const robotsPath = path.resolve('public/robots.txt');
  assert(fs.existsSync(robotsPath), 'public/robots.txt must exist');
  const content = fs.readFileSync(robotsPath, 'utf-8');

  // Allow public routes
  assert(content.includes('Allow: /$'), 'Must allow home page');
  assert(content.includes('Allow: /terms$'), 'Must allow /terms');
  assert(content.includes('Allow: /privacy$'), 'Must allow /privacy');
  assert(content.includes('Allow: /acceptable-use$'), 'Must allow /acceptable-use');
  assert(content.includes('Allow: /contact$'), 'Must allow /contact');

  // Disallow private/authenticated routes
  assert(content.includes('Disallow: /dashboard'), 'Must disallow /dashboard');
  assert(content.includes('Disallow: /profile'), 'Must disallow /profile');
  assert(content.includes('Disallow: /projects/'), 'Must disallow /projects/');
  assert(content.includes('Disallow: /api/'), 'Must disallow /api/');
  assert(content.includes('Sitemap: /sitemap.xml'), 'Must declare sitemap location');
});

// ----------------------------------------------------------------------------
// Test 5: sitemap.xml Structure & Public URL Inclusions
// ----------------------------------------------------------------------------
test('5. sitemap.xml: Valid XML schema containing only legitimate indexable public URLs', () => {
  const sitemapPath = path.resolve('public/sitemap.xml');
  assert(fs.existsSync(sitemapPath), 'public/sitemap.xml must exist');
  const content = fs.readFileSync(sitemapPath, 'utf-8');

  assert(content.includes('<?xml version="1.0" encoding="UTF-8"?>'), 'Must have XML declaration');
  assert(content.includes('http://www.sitemaps.org/schemas/sitemap/0.9'), 'Must reference standard sitemap schema');

  // Public URLs present
  assert(content.includes('<loc>/</loc>'), 'Includes home page');
  assert(content.includes('<loc>/terms</loc>'), 'Includes /terms');
  assert(content.includes('<loc>/privacy</loc>'), 'Includes /privacy');
  assert(content.includes('<loc>/acceptable-use</loc>'), 'Includes /acceptable-use');
  assert(content.includes('<loc>/contact</loc>'), 'Includes /contact');

  // Private routes MUST NOT be present
  assert(!content.includes('/dashboard'), 'Must not include /dashboard');
  assert(!content.includes('/profile'), 'Must not include /profile');
  assert(!content.includes('/projects'), 'Must not include /projects');
  assert(!content.includes('/api'), 'Must not include /api');
});
