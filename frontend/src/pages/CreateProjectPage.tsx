import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Select } from '../components/ui/Select';
import { Alert } from '../components/ui/Alert';
import { useAuth } from '../context/AuthContext';
import { User } from '../types';
import {
  ProjectFormData,
  clearProjectDraft,
  loadProjectDraft,
  saveProjectDraft,
} from '../utils/projectDraft';

interface CreateProjectPageProps {
  onNavigate: (path: string, projectId?: string) => void;
  userOverride?: User | null;
}

export const CreateProjectPage: React.FC<CreateProjectPageProps> = ({ onNavigate, userOverride }) => {
  const { user } = useAuth();
  const currentUser = userOverride !== undefined ? userOverride : user;
  const userId = currentUser?.id;

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [projectCount, setProjectCount] = useState<number | null>(null);

  // Check current project count to warn user if at the 3-project account limit
  useEffect(() => {
    let isMounted = true;
    api.projects.list({ page: 1, pageSize: 1 })
      .then((res) => {
        if (isMounted) {
          setProjectCount(res.pagination?.total_count ?? 0);
        }
      })
      .catch(() => {
        // Ignore network errors on background quota check
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Requirement 1: Restore saved draft before persistence runs via validated lazy state initializer
  const [formData, setFormData] = useState<ProjectFormData>(() => loadProjectDraft(userId));

  // Requirement 1 & 2: Gating refs so initial render or account switches never overwrite saved drafts
  const isDirtyRef = useRef<boolean>(false);
  const loadedUserIdRef = useRef<string | undefined>(userId);

  // Sync draft if authenticated user changes (Account A -> Account B)
  useEffect(() => {
    if (userId !== loadedUserIdRef.current) {
      loadedUserIdRef.current = userId;
      isDirtyRef.current = false;
      setFormData(loadProjectDraft(userId));
    }
  }, [userId]);

  // Save draft whenever formData changes, strictly gated and scoped to authenticated user
  useEffect(() => {
    if (!userId) return; // Do not persist sensitive intake data for anonymous users
    if (!isDirtyRef.current) return; // Prevent initial mount from touching or overwriting storage

    saveProjectDraft(userId, formData);
  }, [formData, userId]);

  const handleChange = (field: keyof ProjectFormData, value: any) => {
    isDirtyRef.current = true;
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const validateStep = (step: number): boolean => {
    setErrorMessage(null);
    if (step === 1) {
      if (!formData.name.trim()) {
        setErrorMessage('Project Name is required.');
        return false;
      }
      if (!formData.industry.trim()) {
        setErrorMessage('Industry is required.');
        return false;
      }
      if (!formData.idea_description.trim() || formData.idea_description.trim().length < 10) {
        setErrorMessage('Please provide a detailed business idea description (at least 10 characters).');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, 4));
    }
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  /**
   * Cancel navigation flow:
   * Deliberately preserves the in-progress draft for the authenticated user so work
   * is not accidentally lost when navigating back to the dashboard.
   * The draft will only be deleted upon successful project creation or explicit user logout.
   */
  const handleCancel = () => {
    onNavigate('/dashboard');
  };

  const handleSubmit = async () => {
    if (!validateStep(1)) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const payload = {
        name: formData.name.trim(),
        industry: formData.industry.trim(),
        idea_description: formData.idea_description.trim(),
        business_stage: formData.business_stage,
        target_market: formData.target_market.trim() || undefined,
        target_audience: formData.target_audience.trim() || undefined,
        budget_amount: formData.budget_amount ? parseFloat(formData.budget_amount) : undefined,
        budget_currency: formData.budget_currency.toUpperCase(),
        team_size: formData.team_size || undefined,
        technical_preferences: formData.technical_preferences.trim() || undefined,
        constraints: formData.constraints.trim() || undefined,
      };

      const project = await api.projects.create(payload);
      // Clean up draft upon successful project creation
      if (userId) {
        clearProjectDraft(userId);
      }
      onNavigate(`/projects/${project.id}`, project.id);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create project. Please verify inputs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
      {/* Step Indicator Header */}
      <div>
        <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          <span>Step {currentStep} of 4</span>
          <span>
            {currentStep === 1 && 'Project Identity'}
            {currentStep === 2 && 'Target Audience & Market'}
            {currentStep === 3 && 'Capital & Constraints'}
            {currentStep === 4 && 'Review & Submit'}
          </span>
        </div>
        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
          <div
            className="bg-indigo-600 h-full transition-all duration-300"
            style={{ width: `${(currentStep / 4) * 100}%` }}
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-8 space-y-6">
          {projectCount !== null && projectCount >= 3 && (
            <Alert
              type="error"
              message="Active Project Limit Reached (3 of 3 slots used): Your account has reached the maximum allowance of 3 projects. To create a new project, return to the Dashboard and delete an existing project first."
            />
          )}

          {errorMessage && <Alert type="error" message={errorMessage} onClose={() => setErrorMessage(null)} />}

          {/* Step 1: Project Identity */}
          {currentStep === 1 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Project Identity & Business Concept</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Name your project and describe the core problem and solution.
                </p>
              </div>

              <Input
                label="Project Name"
                placeholder="e.g. EcoBite AI, CloudSync Ledger"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                required
              />

              <Input
                label="Industry / Domain"
                placeholder="e.g. B2B SaaS, HealthTech, CleanTech, Fintech"
                value={formData.industry}
                onChange={(e) => handleChange('industry', e.target.value)}
                required
              />

              <Textarea
                label="Business Idea Description"
                placeholder="Explain the problem you solve, your proposed value proposition, and how it works..."
                value={formData.idea_description}
                onChange={(e) => handleChange('idea_description', e.target.value)}
                rows={5}
                helperText="Be as specific as possible. The AI engine uses this context to ground all recommendations."
                required
              />
            </div>
          )}

          {/* Step 2: Market & Customer */}
          {currentStep === 2 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Target Audience & Market Landscape</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Define who you are building for and where you plan to launch.
                </p>
              </div>

              <Select
                label="Current Business Stage"
                value={formData.business_stage}
                onChange={(e) => handleChange('business_stage', e.target.value)}
                options={[
                  { value: 'idea', label: 'Idea Stage (Unvalidated Concept)' },
                  { value: 'validation', label: 'Validation (Conducting Customer Interviews)' },
                  { value: 'prototype', label: 'Prototype / Wireframe Phase' },
                  { value: 'mvp', label: 'MVP (Building Minimal Viable Product)' },
                  { value: 'growth', label: 'Growth / Post-Launch' },
                ]}
              />

              <Input
                label="Target Market / Geography"
                placeholder="e.g. United States, North America, Global remote teams"
                value={formData.target_market}
                onChange={(e) => handleChange('target_market', e.target.value)}
              />

              <Textarea
                label="Target Audience / Ideal Customer Profile"
                placeholder="e.g. Freelance designers billing $5k+/mo, small accounting firms with 2-10 CPAs"
                value={formData.target_audience}
                onChange={(e) => handleChange('target_audience', e.target.value)}
                rows={3}
              />
            </div>
          )}

          {/* Step 3: Capital & Constraints */}
          {currentStep === 3 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Capital, Team & Technical Preferences</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Help the architecture engine recommend a realistic technology stack.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Estimated Budget"
                  type="number"
                  placeholder="e.g. 500, 5000, 20000"
                  value={formData.budget_amount}
                  onChange={(e) => handleChange('budget_amount', e.target.value)}
                  min="0"
                  helperText="Leave empty if bootstrapped with zero capital"
                />

                <Select
                  label="Currency"
                  value={formData.budget_currency}
                  onChange={(e) => handleChange('budget_currency', e.target.value)}
                  options={[
                    { value: 'USD', label: 'USD ($)' },
                    { value: 'EUR', label: 'EUR (€)' },
                    { value: 'GBP', label: 'GBP (£)' },
                    { value: 'INR', label: 'INR (₹)' },
                    { value: 'CAD', label: 'CAD ($)' },
                  ]}
                />
              </div>

              <Select
                label="Team Composition"
                value={formData.team_size}
                onChange={(e) => handleChange('team_size', e.target.value)}
                options={[
                  { value: 'Solo', label: 'Solo Founder (Full responsibility)' },
                  { value: '2-5', label: 'Small Team (2-5 people)' },
                  { value: '5-10', label: 'Medium Team (5-10 people)' },
                  { value: '10+', label: 'Funded Team (10+ people)' },
                ]}
              />

              <Input
                label="Technical Preferences (Optional)"
                placeholder="e.g. Prefer Python/React, prefer serverless, prefer open-source tools"
                value={formData.technical_preferences}
                onChange={(e) => handleChange('technical_preferences', e.target.value)}
              />

              <Textarea
                label="Known Constraints or Compliance (Optional)"
                placeholder="e.g. HIPAA compliance required, must launch in under 30 days, low network latency"
                value={formData.constraints}
                onChange={(e) => handleChange('constraints', e.target.value)}
                rows={2}
              />
            </div>
          )}

          {/* Step 4: Review Screen */}
          {currentStep === 4 && (
            <div className="space-y-5 animate-in fade-in duration-150">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Review Project Blueprint Details</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Confirm the intake details before generating your business blueprint.
                </p>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3 text-xs">
                <div>
                  <span className="text-slate-500 block uppercase tracking-wider font-semibold">Project Name</span>
                  <span className="font-bold text-slate-900 text-sm">{formData.name}</span>
                </div>
                <div>
                  <span className="text-slate-500 block uppercase tracking-wider font-semibold">Industry</span>
                  <span className="text-slate-800">{formData.industry}</span>
                </div>
                <div>
                  <span className="text-slate-500 block uppercase tracking-wider font-semibold">Idea Description</span>
                  <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">{formData.idea_description}</p>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-200">
                  <div>
                    <span className="text-slate-500 block uppercase tracking-wider font-semibold">Stage</span>
                    <span className="text-slate-800">{formData.business_stage}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block uppercase tracking-wider font-semibold">Budget</span>
                    <span className="text-slate-800">
                      {formData.budget_amount ? `${formData.budget_amount} ${formData.budget_currency}` : 'Bootstrapped'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg flex items-center gap-2 text-xs text-indigo-900">
                <Sparkles className="w-4 h-4 text-indigo-600 shrink-0" />
                <span>
                  Once created, you can instantly invoke the Business Model Canvas and Technology Stack recommendation engines.
                </span>
              </div>
            </div>
          )}

          {/* Navigation Controls */}
          <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
            {currentStep > 1 ? (
              <Button variant="outline" onClick={handleBack} leftIcon={<ArrowLeft className="w-4 h-4" />}>
                Back
              </Button>
            ) : (
              <Button variant="ghost" onClick={handleCancel}>
                Cancel
              </Button>
            )}

            {currentStep < 4 ? (
              <Button variant="primary" onClick={handleNext} rightIcon={<ArrowRight className="w-4 h-4" />}>
                Next Step
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={handleSubmit}
                isLoading={isSubmitting}
                disabled={projectCount !== null && projectCount >= 3}
                title={projectCount !== null && projectCount >= 3 ? 'Project limit reached (3/3). Delete an existing project first.' : undefined}
                rightIcon={<Check className="w-4 h-4" />}
              >
                {projectCount !== null && projectCount >= 3 ? 'Limit Reached (3/3)' : 'Create Project Workspace'}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
