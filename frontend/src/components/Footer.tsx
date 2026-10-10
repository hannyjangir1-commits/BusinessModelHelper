import React from 'react';
import { Layers } from 'lucide-react';

interface FooterProps {
  onNavigate: (path: string) => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  return (
    <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                <Layers className="w-4 h-4" />
              </div>
              <span className="font-bold text-base text-white">AI Business Architect</span>
            </div>
            <p className="text-sm text-slate-400 max-w-md leading-relaxed">
              Turn your business idea into an actionable blueprint. Transform raw startup concepts into structured
              Business Model Canvases and pragmatic technology-stack recommendations.
            </p>
            <div className="pt-2 text-xs text-slate-500">
              Targeted for solo founders, student entrepreneurs, and technical builders validating initial ventures.
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">Platform</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <button onClick={() => onNavigate('/')} className="hover:text-white transition-colors">
                  Product Overview
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/dashboard')} className="hover:text-white transition-colors">
                  Dashboard
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/projects/new')} className="hover:text-white transition-colors">
                  Idea Intake Wizard
                </button>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">Legal & Trust</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <button onClick={() => onNavigate('/terms')} className="hover:text-white transition-colors">
                  Terms & Conditions
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/privacy')} className="hover:text-white transition-colors">
                  Privacy Policy
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/acceptable-use')} className="hover:text-white transition-colors">
                  Acceptable Use Policy
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('/contact')} className="hover:text-white transition-colors">
                  Contact & Support
                </button>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {new Date().getFullYear()} AI Business Architect. All rights reserved.</p>
          <p className="text-center md:text-right max-w-xl">
            Disclaimer: AI-generated business recommendations and cost estimates are exploratory and advisory only.
            They do not constitute certified legal, financial, or tax counsel.
          </p>
        </div>
      </div>
    </footer>
  );
};
