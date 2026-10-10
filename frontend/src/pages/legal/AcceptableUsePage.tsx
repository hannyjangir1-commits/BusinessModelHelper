import React from 'react';
import { Card, CardContent } from '../../components/ui/Card';

export const AcceptableUsePage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">Platform Standards</span>
        <h1 className="text-3xl font-extrabold text-slate-900 mt-1">Acceptable Use Policy</h1>
        <p className="text-sm text-slate-500 mt-2">Effective Date: January 1, 2026 | Document Version: 2026-v1.0</p>
      </div>

      <Card>
        <CardContent className="prose prose-slate max-w-none text-slate-700 text-sm leading-relaxed space-y-6 p-8">
          <section>
            <h2 className="text-base font-bold text-slate-900">1. Purpose & Scope</h2>
            <p>
              This Acceptable Use Policy defines permitted and prohibited uses of the AI Business Architect platform.
              Our goal is to foster a safe, constructive environment for entrepreneurs, students, and software engineers
              to architect legitimate business enterprises.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-slate-900">2. Prohibited Behaviors</h2>
            <p>Users are expressly prohibited from utilizing the Platform to:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2 text-xs">
              <li>
                <strong>Illegal Enterprises:</strong> Model, plan, or promote businesses involving fraudulent schemes,
                unauthorized financial instruments, pyramid schemes, or illegal goods and services.
              </li>
              <li>
                <strong>Cyberattacks & Security Violations:</strong> Probe, scan, or test the vulnerability of the
                platform, attempt SQL injection, bypass authorization controls, or disrupt system availability.
              </li>
              <li>
                <strong>Automated Abuse:</strong> Rapidly trigger AI generation endpoints using automated bots,
                scripts, or headless browsers to circumvent rate limits or exhaust upstream quotas.
              </li>
              <li>
                <strong>Malicious Content:</strong> Submit abusive, harassing, defamatory, or harmful content into project
                intake forms.
              </li>
              <li>
                <strong>Identity Misrepresentation:</strong> Impersonate another individual or register duplicate fraudulent
                accounts for abusive purposes.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-base font-bold text-slate-900">3. Enforcement & Suspension</h2>
            <p>
              We reserve the right to suspend or terminate accounts that violate this policy without notice. Where
              appropriate, severe violations involving illegal activities or security attacks may be escalated to
              competent authorities.
            </p>
          </section>
        </CardContent>
      </Card>
    </div>
  );
};
