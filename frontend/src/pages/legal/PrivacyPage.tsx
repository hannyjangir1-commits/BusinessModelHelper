import React from 'react';
import { Card, CardContent } from '../../components/ui/Card';

export const PrivacyPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">Privacy & Transparency</span>
        <h1 className="text-3xl font-extrabold text-slate-900 mt-1">Privacy Policy</h1>
        <p className="text-sm text-slate-500 mt-2">Effective Date: January 1, 2026 | Document Version: 2026-v1.0</p>
      </div>

      <Card>
        <CardContent className="prose prose-slate max-w-none text-slate-700 text-sm leading-relaxed space-y-6 p-8">
          <section>
            <h2 className="text-base font-bold text-slate-900">1. Information We Collect</h2>
            <p>
              We collect information necessary to deliver and secure the AI Business Architect platform, specifically:
            </p>
            <ul className="list-disc pl-5 space-y-1 mt-1 text-xs">
              <li>
                <strong>Account Credentials:</strong> Username, email address, and an Argon2id one-way cryptographic
                password hash. (We never store, log, or have access to your plain-text password.)
              </li>
              <li>
                <strong>User Profile:</strong> Optional display name, professional bio, country, and preferred currency.
              </li>
              <li>
                <strong>Project Intake Data:</strong> Business project name, raw idea description, industry, business
                stage, target audience, budget, and constraints.
              </li>
              <li>
                <strong>Audit & Generation Metadata:</strong> Timestamps, model identifiers, latency, and token counts
                associated with blueprint generations.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-slate-900">2. How Submitted Business Ideas Are Processed by AI</h2>
            <p>
              When you generate a Business Model Canvas or Technology Stack recommendation, your project inputs are
              transmitted over secure server-side TLS connections to the configured AI provider:
            </p>
            <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg text-indigo-900 text-xs mt-2">
              <strong>Third-Party AI Integration (Google Gemini API):</strong>
              <p className="mt-1">
                Data sent to Google GenAI for inference is subject to Google Cloud’s commercial data protection terms.
                We do not share your business ideas with advertising networks, data brokers, or public scraping engines.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-base font-bold text-slate-900">3. Cookies & Session Storage</h2>
            <p>
              AI Business Architect employs secure, first-party HTTP-only session cookies with <code>SameSite=Lax</code> and
              cryptographic token signatures. We do not use third-party tracking cookies, invasive marketing pixels, or
              session replay trackers.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-slate-900">4. Data Retention & Deletion Rights</h2>
            <p>
              Your saved projects, blueprints, and generations remain securely stored in PostgreSQL until you choose to
              delete them. You have full control over your data:
            </p>
            <ul className="list-disc pl-5 space-y-1 mt-1 text-xs">
              <li>You may delete individual projects at any time.</li>
              <li>You may permanently delete your entire user account and all cascading data via Account Settings.</li>
            </ul>
            <p className="mt-2 text-xs text-slate-500">
              Note: When you initiate account deletion, your records are immediately purged from active relational
              databases. Ephemeral disaster-recovery database backups age out according to standard retention schedules.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-slate-900">5. Security Safeguards</h2>
            <p>
              We implement industry-standard defense-in-depth measures, including Argon2id password hashing, CSRF token
              validation, rate-limiting on sensitive endpoints, strict server-side Pydantic payload validation, and
              encrypted database transport.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-slate-900">6. Policy Inquiries</h2>
            <p>
              For privacy requests or questions regarding this policy, please consult the Contact page or configuration
              guidance in the application documentation.
            </p>
          </section>
        </CardContent>
      </Card>
    </div>
  );
};
