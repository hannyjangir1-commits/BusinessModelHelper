import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, id, type = 'text', className = '', ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id || (label ? `${label.toLowerCase().replace(/[^a-z0-9]/g, '-')}-${generatedId}` : generatedId);
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === 'password';
    const computedType = isPassword ? (showPassword ? 'text' : 'password') : type;

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            {label}
            {props.required && <span className="text-rose-500 ml-1">*</span>}
          </label>
        )}
        <div className="relative">
          <input
            id={inputId}
            ref={ref}
            type={computedType}
            aria-invalid={Boolean(error)}
            className={`w-full px-3.5 py-2 text-sm bg-white border rounded-lg transition-colors focus:outline-hidden focus:ring-2 focus:border-transparent ${
              error
                ? 'border-rose-400 focus:ring-rose-400 text-rose-900 placeholder-rose-300'
                : 'border-slate-300 focus:ring-indigo-500 text-slate-900 placeholder-slate-400'
            } ${isPassword ? 'pr-11' : ''} ${className}`}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 min-w-[36px] min-h-[36px] flex items-center justify-center text-slate-500 hover:text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 rounded-lg transition-colors cursor-pointer"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
        </div>
        {error && <p className="mt-1.5 text-xs text-rose-600 font-medium">{error}</p>}
        {helperText && !error && <p className="mt-1.5 text-xs text-slate-500">{helperText}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';
