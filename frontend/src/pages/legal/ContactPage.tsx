import React from 'react';
import { Mail, ShieldCheck, Terminal } from 'lucide-react';
import { Card, CardContent } from '../../components/ui/Card';

export const ContactPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">Support & Feedback</span>
        <h1 className="text-3xl font-extrabold text-slate-900 mt-1">Contact & Support</h1>
        <p className="text-sm text-slate-500 mt-2">
          Technical assistance, feature inquiries, and operator configuration details.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Mail className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Developer & Community Inquiries</h2>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                For questions regarding deployment, portfolio demonstrations, and technical architecture:
              </p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono text-slate-800">
              support@businessarchitect.local
            </div>
            <p className="text-[11px] text-slate-400">
              Note: This address is configured for demonstration and self-hosted instances. For custom domains, update the
              environment configuration.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Security & Vulnerability Reports</h2>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                If you discover a potential security vulnerability or authorization issue in this repository:
              </p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono text-slate-800">
              security@businessarchitect.local
            </div>
            <p className="text-[11px] text-slate-400">
              We appreciate responsible disclosure and address confirmed security tickets promptly.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 p-6 bg-slate-900 text-slate-300 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2 mb-2 text-white font-semibold text-sm">
          <Terminal className="w-4 h-4 text-indigo-400" />
          Production Operator Configuration Notice
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          In production deployments on Render, the operator can customize contact channels and designated escalation routes
          by updating the application documentation or providing environmental webhooks. The platform intentionally does
          not provide a dummy contact submission box that silently discards messages.
        </p>
      </div>
    </div>
  );
};
