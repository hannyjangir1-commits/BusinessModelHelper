import React, { useRef, useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { FieldErrors, parseRegistrationError } from '../../utils/errors';

interface RegisterPageProps {
  onNavigate: (path: string) => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onNavigate }) => {
  const { register } = useAuth();

  // Form field state
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAcknowledged, setPrivacyAcknowledged] = useState(false);

  // Interaction tracking for touched fields
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Error states
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Lifecycle states
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Field element refs for keyboard focus management
  const usernameRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const confirmPasswordRef = useRef<HTMLInputElement>(null);
  const termsRef = useRef<HTMLInputElement>(null);
  const privacyRef = useRef<HTMLInputElement>(null);

  // Password complexity rules (matches backend policy: 8-128 chars, at least 1 letter, at least 1 number)
  const hasMinLength = password.length >= 8 && password.length <= 128;
  const hasLetter = /[A-Za-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[^A-Za-z0-9]/.test(password);

  // Password strength calculation
  const calculateStrength = (): { score: number; label: string; color: string; width: string } => {
    if (!password) return { score: 0, label: '', color: 'bg-slate-200', width: '0%' };
    let score = 0;
    if (password.length >= 8) score++;
    if (hasLetter) score++;
    if (hasNumber) score++;
    if (password.length >= 12 || hasSpecial) score++;

    switch (score) {
      case 1:
        return { score: 1, label: 'Weak', color: 'bg-rose-500', width: '25%' };
      case 2:
        return { score: 2, label: 'Fair', color: 'bg-amber-500', width: '50%' };
      case 3:
        return { score: 3, label: 'Good', color: 'bg-indigo-600', width: '75%' };
      case 4:
        return { score: 4, label: 'Strong', color: 'bg-emerald-600', width: '100%' };
      default:
        return { score: 0, label: '', color: 'bg-slate-200', width: '0%' };
    }
  };

  const strength = calculateStrength();

  // Client validation functions
  const validateUsername = (val: string): string | undefined => {
    const clean = val.trim();
    if (!clean) return 'Username is required.';
    if (clean.length < 3) return 'Username must be at least 3 characters.';
    if (clean.length > 30) return 'Username must not exceed 30 characters.';
    if (!/^[a-zA-Z0-9_-]+$/.test(clean)) {
      return 'Username can only contain letters, numbers, underscores, and hyphens.';
    }
    return undefined;
  };

  const validateEmail = (val: string): string | undefined => {
    const clean = val.trim();
    if (!clean) return 'Email address is required.';
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(clean)) {
      return 'Please enter a valid email address (e.g. founder@venture.com).';
    }
    if (clean.length > 255) return 'Email address must not exceed 255 characters.';
    return undefined;
  };

  const validatePassword = (val: string): string | undefined => {
    if (!val) return 'Password is required.';
    if (val.length < 8) return 'Password must be at least 8 characters long.';
    if (val.length > 128) return 'Password must not exceed 128 characters.';
    if (!/[A-Za-z]/.test(val)) return 'Password must contain at least one letter.';
    if (!/\d/.test(val)) return 'Password must contain at least one number.';
    return undefined;
  };

  const validateConfirmPassword = (val: string, pwd: string): string | undefined => {
    if (!val) return 'Please confirm your password.';
    if (val !== pwd) return 'Passwords do not match.';
    return undefined;
  };

  // Field change handlers with live error clearing
  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setUsername(val);
    if (touched.username) {
      setFieldErrors((prev) => ({ ...prev, username: validateUsername(val) }));
    }
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setEmail(val);
    if (touched.email) {
      setFieldErrors((prev) => ({ ...prev, email: validateEmail(val) }));
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setPassword(val);
    if (touched.password) {
      setFieldErrors((prev) => ({ ...prev, password: validatePassword(val) }));
    }
    if (touched.confirmPassword && confirmPassword) {
      setFieldErrors((prev) => ({ ...prev, confirmPassword: validateConfirmPassword(confirmPassword, val) }));
    }
  };

  const handleConfirmPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setConfirmPassword(val);
    if (touched.confirmPassword) {
      setFieldErrors((prev) => ({ ...prev, confirmPassword: validateConfirmPassword(val, password) }));
    }
  };

  const handleBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    if (field === 'username') setFieldErrors((prev) => ({ ...prev, username: validateUsername(username) }));
    if (field === 'email') setFieldErrors((prev) => ({ ...prev, email: validateEmail(email) }));
    if (field === 'password') setFieldErrors((prev) => ({ ...prev, password: validatePassword(password) }));
    if (field === 'confirmPassword')
      setFieldErrors((prev) => ({ ...prev, confirmPassword: validateConfirmPassword(confirmPassword, password) }));
  };

  const handleTermsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTermsAccepted(e.target.checked);
    if (e.target.checked) {
      setFieldErrors((prev) => ({ ...prev, termsAccepted: undefined }));
    }
  };

  const handlePrivacyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPrivacyAcknowledged(e.target.checked);
    if (e.target.checked) {
      setFieldErrors((prev) => ({ ...prev, privacyAcknowledged: undefined }));
    }
  };

  // Form submission handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError(null);
    setSuccessMessage(null);

    // Mark all as touched
    setTouched({
      username: true,
      email: true,
      password: true,
      confirmPassword: true,
      termsAccepted: true,
      privacyAcknowledged: true,
    });

    // Run client-side validation suite
    const userErr = validateUsername(username);
    const emailErr = validateEmail(email);
    const passErr = validatePassword(password);
    const confirmErr = validateConfirmPassword(confirmPassword, password);
    const termsErr = !termsAccepted
      ? 'You must read and accept the Terms and Conditions to create an account.'
      : undefined;
    const privacyErr = !privacyAcknowledged
      ? 'You must acknowledge the Privacy Policy to proceed.'
      : undefined;

    const errors: FieldErrors = {
      username: userErr,
      email: emailErr,
      password: passErr,
      confirmPassword: confirmErr,
      termsAccepted: termsErr,
      privacyAcknowledged: privacyErr,
    };

    setFieldErrors(errors);

    // Focus the first invalid input element
    if (userErr) {
      usernameRef.current?.focus();
      return;
    }
    if (emailErr) {
      emailRef.current?.focus();
      return;
    }
    if (passErr) {
      passwordRef.current?.focus();
      return;
    }
    if (confirmErr) {
      confirmPasswordRef.current?.focus();
      return;
    }
    if (termsErr) {
      termsRef.current?.focus();
      return;
    }
    if (privacyErr) {
      privacyRef.current?.focus();
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
        privacy_accepted: privacyAcknowledged,
      });

      setSuccessMessage('Account created successfully! Redirecting to your dashboard...');
      setTimeout(() => {
        onNavigate('/dashboard');
      }, 500);
    } catch (err: unknown) {
      const parsed = parseRegistrationError(err);
      setFieldErrors(parsed.fieldErrors);
      setGeneralError(parsed.generalError);

      // Shift focus to the first errored field if available
      if (parsed.fieldErrors.username) usernameRef.current?.focus();
      else if (parsed.fieldErrors.email) emailRef.current?.focus();
      else if (parsed.fieldErrors.password) passwordRef.current?.focus();
      else if (parsed.fieldErrors.confirmPassword) confirmPasswordRef.current?.focus();
      else if (parsed.fieldErrors.termsAccepted) termsRef.current?.focus();
      else if (parsed.fieldErrors.privacyAcknowledged) privacyRef.current?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const isUsernameValid = !fieldErrors.username && username.trim().length >= 3 && /^[a-zA-Z0-9_-]+$/.test(username.trim());
  const isEmailValid = !fieldErrors.email && email.trim().length >= 5 && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim());
  const isConfirmValid = !fieldErrors.confirmPassword && confirmPassword && confirmPassword === password;

  return (
    <div className="min-h-[88vh] flex items-center justify-center px-4 py-8 sm:py-12">
      <div className="w-full max-w-6xl mx-auto lg:grid lg:grid-cols-12 lg:gap-8 items-center">
        {/* Left Side: Restrained Brand & Value Proposition (Desktop) */}
        <div className="hidden lg:flex lg:col-span-5 flex-col justify-between bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-8 lg:p-10 shadow-2xl border border-slate-800/80 min-h-[640px]">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-400/20 text-indigo-300 text-xs font-semibold mb-6">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Enterprise Blueprint Engine</span>
            </div>

            <h2 className="text-3xl font-extrabold tracking-tight text-white leading-tight">
              Architect scalable startup ventures with precision.
            </h2>
            <p className="text-sm text-slate-300 mt-3 leading-relaxed">
              Transform raw business ideas into production-grade Business Model Canvases, verified technology stacks, and financial roadmaps.
            </p>

            <div className="mt-8 space-y-4">
              <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xs">
                <div className="w-9 h-9 rounded-lg bg-indigo-600/30 border border-indigo-400/30 flex items-center justify-center text-indigo-300 shrink-0 mt-0.5">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">9-Block Business Model Canvas</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Multi-section strategic canvas with revenue models, customer clarity, and value propositions.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xs">
                <div className="w-9 h-9 rounded-lg bg-indigo-600/30 border border-indigo-400/30 flex items-center justify-center text-indigo-300 shrink-0 mt-0.5">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Verified Technology Stacks</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    FastAPI, React, PostgreSQL, and cloud deployments tailored to your startup's technical constraints.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xs">
                <div className="w-9 h-9 rounded-lg bg-indigo-600/30 border border-indigo-400/30 flex items-center justify-center text-indigo-300 shrink-0 mt-0.5">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Bank-Grade Argon2id Security</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Zero plaintext secrets, strict cryptographic hashing, and isolated multi-tenant workspaces.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>AI Business Architect v2.0</span>
            <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> Live & Ready
            </span>
          </div>
        </div>

        {/* Right Side: Rebuilt Signup Card */}
        <div className="w-full lg:col-span-7 max-w-xl mx-auto space-y-5">
          {/* Mobile Brand Header */}
          <div className="text-center lg:text-left space-y-1">
            <div className="inline-flex lg:hidden items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-700 via-indigo-600 to-indigo-500 text-white shadow-md mb-2">
              <Layers className="w-6 h-6" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Create your account
            </h1>
            <p className="text-xs sm:text-sm text-slate-500">
              Start building verified business models and enterprise technology blueprints
            </p>
          </div>

          <Card className="shadow-lg border-slate-200/90">
            <CardContent className="p-6 sm:p-8 space-y-5">
              {/* Form-level Success or Error alerts */}
              {successMessage && (
                <Alert type="success" title="Success" message={successMessage} className="animate-in fade-in" />
              )}
              {generalError && (
                <Alert
                  type="error"
                  title="Registration Error"
                  message={generalError}
                  onClose={() => setGeneralError(null)}
                  className="animate-in fade-in"
                />
              )}

              <form onSubmit={handleSubmit} noValidate className="space-y-4">
                {/* Username Input */}
                <div className="relative">
                  <Input
                    ref={usernameRef}
                    id="register-username"
                    name="username"
                    label="Username"
                    placeholder="e.g. techfounder"
                    value={username}
                    onChange={handleUsernameChange}
                    onBlur={() => handleBlur('username')}
                    error={touched.username ? fieldErrors.username : undefined}
                    helperText="3 to 30 characters (letters, numbers, underscores, hyphens)"
                    autoComplete="username"
                    required
                  />
                  {isUsernameValid && (
                    <div className="absolute right-3 top-8 text-emerald-600 pointer-events-none" aria-hidden="true">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                  )}
                </div>

                {/* Email Input */}
                <div className="relative">
                  <Input
                    ref={emailRef}
                    id="register-email"
                    name="email"
                    type="email"
                    label="Email Address"
                    placeholder="founder@venture.com"
                    value={email}
                    onChange={handleEmailChange}
                    onBlur={() => handleBlur('email')}
                    error={touched.email ? fieldErrors.email : undefined}
                    autoComplete="email"
                    required
                  />
                  {isEmailValid && (
                    <div className="absolute right-3 top-8 text-emerald-600 pointer-events-none" aria-hidden="true">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                  )}
                </div>

                {/* Password Input */}
                <div>
                  <Input
                    ref={passwordRef}
                    id="register-password"
                    name="password"
                    type="password"
                    label="Password"
                    placeholder="At least 8 characters with letter & number"
                    value={password}
                    onChange={handlePasswordChange}
                    onBlur={() => handleBlur('password')}
                    error={touched.password ? fieldErrors.password : undefined}
                    autoComplete="new-password"
                    required
                  />

                  {/* Password Strength Meter & Complexity Indicators */}
                  {password.length > 0 && (
                    <div className="mt-2.5 p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-2 text-xs">
                      {/* Strength progress bar */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-slate-700">Password Strength:</span>
                          <span
                            className={`font-bold ${
                              strength.score <= 1
                                ? 'text-rose-600'
                                : strength.score === 2
                                ? 'text-amber-600'
                                : strength.score === 3
                                ? 'text-indigo-600'
                                : 'text-emerald-600'
                            }`}
                          >
                            {strength.label}
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all duration-300 ${strength.color}`}
                            style={{ width: strength.width }}
                          />
                        </div>
                      </div>

                      {/* Requirement checklist */}
                      <div className="pt-1 grid grid-cols-1 sm:grid-cols-3 gap-1.5 text-[11px]">
                        <div
                          className={`flex items-center gap-1.5 font-medium ${
                            hasMinLength ? 'text-emerald-700 font-semibold' : 'text-slate-500'
                          }`}
                        >
                          <CheckCircle2
                            className={`w-3.5 h-3.5 ${hasMinLength ? 'text-emerald-600' : 'text-slate-300'}`}
                          />
                          <span>8+ characters</span>
                        </div>
                        <div
                          className={`flex items-center gap-1.5 font-medium ${
                            hasLetter ? 'text-emerald-700 font-semibold' : 'text-slate-500'
                          }`}
                        >
                          <CheckCircle2 className={`w-3.5 h-3.5 ${hasLetter ? 'text-emerald-600' : 'text-slate-300'}`} />
                          <span>One letter (a-z)</span>
                        </div>
                        <div
                          className={`flex items-center gap-1.5 font-medium ${
                            hasNumber ? 'text-emerald-700 font-semibold' : 'text-slate-500'
                          }`}
                        >
                          <CheckCircle2 className={`w-3.5 h-3.5 ${hasNumber ? 'text-emerald-600' : 'text-slate-300'}`} />
                          <span>One number (0-9)</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Confirm Password Input */}
                <div className="relative">
                  <Input
                    ref={confirmPasswordRef}
                    id="register-confirm-password"
                    name="confirm_password"
                    type="password"
                    label="Confirm Password"
                    placeholder="Re-enter your password"
                    value={confirmPassword}
                    onChange={handleConfirmPasswordChange}
                    onBlur={() => handleBlur('confirmPassword')}
                    error={touched.confirmPassword ? fieldErrors.confirmPassword : undefined}
                    autoComplete="new-password"
                    required
                  />
                  {isConfirmValid && (
                    <div className="absolute right-10 top-8 text-emerald-600 pointer-events-none" aria-hidden="true">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                  )}
                </div>

                {/* Mandatory Legal Acceptances */}
                <div className="pt-2 space-y-3">
                  <div>
                    <label
                      htmlFor="register-terms"
                      className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-700 leading-normal"
                    >
                      <input
                        ref={termsRef}
                        id="register-terms"
                        name="terms_accepted"
                        type="checkbox"
                        checked={termsAccepted}
                        onChange={handleTermsChange}
                        aria-invalid={Boolean(touched.termsAccepted && fieldErrors.termsAccepted)}
                        aria-describedby={
                          touched.termsAccepted && fieldErrors.termsAccepted ? 'terms-error' : undefined
                        }
                        className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4 shrink-0"
                      />
                      <span>
                        I have read and agree to the{' '}
                        <button
                          type="button"
                          onClick={() => onNavigate('/terms')}
                          className="font-semibold text-indigo-600 hover:text-indigo-800 underline focus:outline-hidden focus:ring-2 focus:ring-indigo-500 rounded-sm"
                        >
                          Terms and Conditions (Version 2026-v1.0)
                        </button>
                        . <span className="text-rose-500">*</span>
                      </span>
                    </label>
                    {touched.termsAccepted && fieldErrors.termsAccepted && (
                      <p id="terms-error" role="alert" className="mt-1 text-xs text-rose-600 font-medium pl-6">
                        {fieldErrors.termsAccepted}
                      </p>
                    )}
                  </div>

                  <div>
                    <label
                      htmlFor="register-privacy"
                      className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-700 leading-normal"
                    >
                      <input
                        ref={privacyRef}
                        id="register-privacy"
                        name="privacy_acknowledged"
                        type="checkbox"
                        checked={privacyAcknowledged}
                        onChange={handlePrivacyChange}
                        aria-invalid={Boolean(touched.privacyAcknowledged && fieldErrors.privacyAcknowledged)}
                        aria-describedby={
                          touched.privacyAcknowledged && fieldErrors.privacyAcknowledged ? 'privacy-error' : undefined
                        }
                        className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4 shrink-0"
                      />
                      <span>
                        I acknowledge the{' '}
                        <button
                          type="button"
                          onClick={() => onNavigate('/privacy')}
                          className="font-semibold text-indigo-600 hover:text-indigo-800 underline focus:outline-hidden focus:ring-2 focus:ring-indigo-500 rounded-sm"
                        >
                          Privacy Policy
                        </button>{' '}
                        and understand my project descriptions will be processed via server-side AI for blueprint generation.{' '}
                        <span className="text-rose-500">*</span>
                      </span>
                    </label>
                    {touched.privacyAcknowledged && fieldErrors.privacyAcknowledged && (
                      <p id="privacy-error" role="alert" className="mt-1 text-xs text-rose-600 font-medium pl-6">
                        {fieldErrors.privacyAcknowledged}
                      </p>
                    )}
                  </div>
                </div>

                {/* Primary Registration Submit Button */}
                <Button
                  id="register-submit-button"
                  type="submit"
                  variant="primary"
                  className="w-full justify-center mt-3 shadow-md"
                  size="lg"
                  isLoading={isLoading}
                  disabled={isLoading}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  {isLoading ? 'Creating account...' : 'Create Account & Get Started'}
                </Button>
              </form>

              {/* Navigation link for existing users */}
              <div className="pt-4 border-t border-slate-100 text-center text-xs text-slate-600">
                Already have an account?{' '}
                <button
                  type="button"
                  id="register-login-link"
                  onClick={() => onNavigate('/login')}
                  className="font-semibold text-indigo-600 hover:text-indigo-800 underline focus:outline-hidden focus:ring-2 focus:ring-indigo-500 rounded-sm"
                >
                  Sign in
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
