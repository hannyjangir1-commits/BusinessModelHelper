import React, { useState } from 'react';
import { ArrowRight, CheckCircle2, Layers } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';

interface RegisterPageProps {
  onNavigate: (path: string) => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onNavigate }) => {
  const { register } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAcknowledged, setPrivacyAcknowledged] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    if (!termsAccepted) {
      setErrorMessage('You must read and accept the Terms and Conditions to create an account.');
      return;
    }

    if (!privacyAcknowledged) {
      setErrorMessage('You must acknowledge the Privacy Policy to proceed.');
      return;
    }

    setIsLoading(true);
    try {
      await register({
        username: username.trim(),
        email: email.trim().toLowerCase(),
        password,
        confirm_password: confirmPassword,
        terms_accepted: termsAccepted,
        privacy_acknowledged: privacyAcknowledged,
      });
      onNavigate('/dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please check your information.');
    } finally {
      setIsLoading(false);
    }
  };

  const hasLetter = /[A-Za-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasMinLength = password.length >= 8;

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-600 text-white shadow-md mb-3">
            <Layers className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Create Your Account</h1>
          <p className="text-xs text-slate-500 mt-1">
            Start architecting structured startup blueprints and technology stacks
          </p>
        </div>

        <Card>
          <CardContent className="p-8 space-y-5">
            {errorMessage && <Alert type="error" message={errorMessage} onClose={() => setErrorMessage(null)} />}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Username"
                placeholder="techfounder"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                helperText="3 to 30 characters (letters, numbers, underscores, hyphens)"
                required
              />

              <Input
                label="Email Address"
                type="email"
                placeholder="founder@venture.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <Input
                label="Password"
                type="password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              {/* Password complexity indicators */}
              {password && (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1 text-xs">
                  <p className="font-semibold text-slate-700 mb-1">Password Requirements:</p>
                  <div className={`flex items-center gap-1.5 ${hasMinLength ? 'text-emerald-700' : 'text-slate-500'}`}>
                    <CheckCircle2 className="w-3.5 h-3.5" /> At least 8 characters
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasLetter ? 'text-emerald-700' : 'text-slate-500'}`}>
                    <CheckCircle2 className="w-3.5 h-3.5" /> Contains at least one letter
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasNumber ? 'text-emerald-700' : 'text-slate-500'}`}>
                    <CheckCircle2 className="w-3.5 h-3.5" /> Contains at least one number
                  </div>
                </div>
              )}

              <Input
                label="Confirm Password"
                type="password"
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />

              {/* Legal Acceptances */}
              <div className="pt-2 space-y-3">
                <label className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-700 leading-normal">
                  <input
                    type="checkbox"
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                    required
                  />
                  <span>
                    I have read and agree to the{' '}
                    <button
                      type="button"
                      onClick={() => onNavigate('/terms')}
                      className="font-semibold text-indigo-600 hover:underline"
                    >
                      Terms and Conditions (Version 2026-v1.0)
                    </button>
                    .
                  </span>
                </label>

                <label className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-700 leading-normal">
                  <input
                    type="checkbox"
                    checked={privacyAcknowledged}
                    onChange={(e) => setPrivacyAcknowledged(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                    required
                  />
                  <span>
                    I acknowledge the{' '}
                    <button
                      type="button"
                      onClick={() => onNavigate('/privacy')}
                      className="font-semibold text-indigo-600 hover:underline"
                    >
                      Privacy Policy
                    </button>{' '}
                    and understand my project descriptions will be processed via server-side AI for blueprint generation.
                  </span>
                </label>
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full justify-center mt-3"
                size="lg"
                isLoading={isLoading}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Create Account & Get Started
              </Button>
            </form>

            <div className="pt-4 border-t border-slate-100 text-center text-xs text-slate-600">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => onNavigate('/login')}
                className="font-semibold text-indigo-600 hover:text-indigo-800"
              >
                Sign in
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
