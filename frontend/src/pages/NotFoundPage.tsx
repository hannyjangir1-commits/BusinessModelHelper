import React from 'react';
import { Compass, Home, HelpCircle, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/Button';

interface NotFoundPageProps {
  onNavigate: (path: string) => void;
}

export const NotFoundPage: React.FC<NotFoundPageProps> = ({ onNavigate }) => {
  return (
    <div
      role="region"
      aria-label="Page not found notice"
      className="max-w-3xl mx-auto px-4 py-16 sm:py-24 text-center space-y-6"
    >
      <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto shadow-xs">
        <Compass className="w-8 h-8" aria-hidden="true" />
      </div>

      <div className="space-y-2">
        <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
          Error 404
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Page Not Found
        </h1>
        <p className="text-sm sm:text-base text-slate-600 max-w-md mx-auto leading-relaxed">
          The address you requested does not exist or may have been moved.
          Verify the URL or navigate back to your workspace.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
        <Button
          variant="primary"
          onClick={() => onNavigate('/')}
          leftIcon={<Home className="w-4 h-4" />}
        >
          Return to Home
        </Button>
        <Button
          variant="outline"
          onClick={() => onNavigate('/dashboard')}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
        >
          Go to Dashboard
        </Button>
        <Button
          variant="ghost"
          onClick={() => onNavigate('/contact')}
          leftIcon={<HelpCircle className="w-4 h-4" />}
        >
          Contact Support
        </Button>
      </div>

      <div className="pt-8 border-t border-slate-200 text-xs text-slate-500">
        <p>Looking for legal policies?</p>
        <div className="flex justify-center gap-4 mt-2">
          <button
            onClick={() => onNavigate('/terms')}
            className="hover:text-indigo-600 underline cursor-pointer"
          >
            Terms of Service
          </button>
          <span>•</span>
          <button
            onClick={() => onNavigate('/privacy')}
            className="hover:text-indigo-600 underline cursor-pointer"
          >
            Privacy Policy
          </button>
          <span>•</span>
          <button
            onClick={() => onNavigate('/acceptable-use')}
            className="hover:text-indigo-600 underline cursor-pointer"
          >
            Acceptable Use
          </button>
        </div>
      </div>
    </div>
  );
};
