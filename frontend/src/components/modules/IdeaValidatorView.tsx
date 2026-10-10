import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Compass,
  HelpCircle,
  Lightbulb,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Target,
  Zap,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  BlueprintVersionItem,
  CustomerInterviewQuestion,
  InterviewQuestionItem,
  ValidationExperiment,
  ValidationReportData,
  ValidationReportResponse,
} from '../../types';
import { safeText, normalizeValidationReportData } from '../../utils/validator';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Alert } from '../ui/Alert';

interface QuestionCardProps {
  question: InterviewQuestionItem;
  index: number;
}

export const ValidationQuestionCard: React.FC<QuestionCardProps> = ({ question, index }) => {
  const isObj = typeof question === 'object' && question !== null;
  const questionText = isObj
    ? (question as CustomerInterviewQuestion).question_text || (question as any).question || (question as any).text || ''
    : String(question || '');
  const focusCategory = isObj
    ? (question as CustomerInterviewQuestion).focus_category || (question as any).category || (question as any).focus
    : undefined;
  const rationale = isObj
    ? (question as CustomerInterviewQuestion).rationale || (question as any).reasoning || (question as any).why
    : undefined;

  const getBadgeVariant = (cat?: string): 'indigo' | 'amber' | 'rose' | 'emerald' | 'slate' => {
    if (!cat) return 'slate';
    const lower = cat.toLowerCase();
    if (lower.includes('past') || lower.includes('behavior')) return 'indigo';
    if (lower.includes('friction') || lower.includes('pain')) return 'rose';
    if (lower.includes('budget') || lower.includes('pay') || lower.includes('price')) return 'emerald';
    if (lower.includes('workaround') || lower.includes('current')) return 'amber';
    return 'slate';
  };

  return (
    <div className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/80 space-y-1.5 transition-all hover:bg-white hover:border-slate-300">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 text-[11px] font-bold shrink-0 mt-0.5">
            {index + 1}
          </span>
          <p className="font-medium text-slate-800 text-xs leading-relaxed">
            {questionText || 'Unspecified validation inquiry'}
          </p>
        </div>
        {focusCategory && (
          <Badge variant={getBadgeVariant(focusCategory)} size="sm" className="shrink-0 font-medium">
            {focusCategory}
          </Badge>
        )}
      </div>
      {rationale && (
        <p className="text-[11px] text-slate-500 pl-7 italic">
          <span className="font-semibold text-slate-600 not-italic">Rationale:</span> {rationale}
        </p>
      )}
    </div>
  );
};

interface ExperimentCardProps {
  experiment: ValidationExperiment;
  index: number;
}

export const ValidationExperimentCard: React.FC<ExperimentCardProps> = ({ experiment, index }) => {
  return (
    <div className="border border-slate-200 rounded-xl p-3.5 space-y-2 bg-slate-50/50 hover:bg-white transition-all hover:border-slate-300">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold shrink-0">
            {index + 1}
          </span>
          <h4 className="font-bold text-sm text-slate-900">{safeText(experiment.experiment_name, 'Validation Experiment')}</h4>
        </div>
        <div className="flex flex-wrap items-center gap-1.5 shrink-0">
          {experiment.experiment_type && <Badge variant="indigo" size="sm">{safeText(experiment.experiment_type)}</Badge>}
          {experiment.estimated_duration && <Badge variant="slate" size="sm">{safeText(experiment.estimated_duration)}</Badge>}
          {experiment.estimated_cost && <Badge variant="emerald" size="sm">{safeText(experiment.estimated_cost)}</Badge>}
        </div>
      </div>
      {experiment.hypothesis && (
        <p className="text-xs text-slate-600">
          <strong className="text-slate-800">Hypothesis:</strong> {safeText(experiment.hypothesis)}
        </p>
      )}
      {experiment.target_audience && (
        <p className="text-[11px] text-slate-500">
          <strong className="text-slate-700">Target Cohort:</strong> {safeText(experiment.target_audience)}
        </p>
      )}
      {experiment.procedure && (
        <p className="text-[11px] text-slate-500">
          <strong className="text-slate-700">Procedure:</strong> {safeText(experiment.procedure)}
        </p>
      )}
      {experiment.success_criteria && (
        <div className="text-xs text-slate-700 pt-1.5 border-t border-slate-200/60">
          <span className="font-semibold text-slate-900">Success Criteria:</span> {safeText(experiment.success_criteria)}
        </div>
      )}
    </div>
  );
};

interface IdeaValidatorViewProps {
  projectId: string;
  report: ValidationReportResponse | null;
  versions: BlueprintVersionItem[];
  onReportUpdated: () => void;
}

export const IdeaValidatorView: React.FC<IdeaValidatorViewProps> = ({
  projectId,
  report,
  versions,
  onReportUpdated,
}) => {
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [selectedVersion, setSelectedVersion] = useState<number | undefined>(report?.version);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (isGenerating) return;
    setIsGenerating(true);
    setError(null);
    setSuccess(null);
    try {
      await api.validator.generate(projectId);
      setSuccess('Business Idea Validation report successfully synthesized.');
      onReportUpdated();
    } catch (err: any) {
      setError(err?.message || 'Failed to generate idea validation report.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleVersionChange = async (ver: number) => {
    setSelectedVersion(ver);
    try {
      await api.validator.get(projectId, ver);
      onReportUpdated();
    } catch (err: any) {
      setError(err?.message || 'Failed to load report version.');
    }
  };

  // Safely normalize raw content from backend
  const rawData = report?.content_json || report?.content || null;
  const data: ValidationReportData | null = rawData ? normalizeValidationReportData(rawData) : null;

  if (!report || !data) {
    return (
      <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8">
        <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-slate-900">Idea Validation Report</h3>
          <p className="text-sm text-slate-500">
            Rigorously evaluate problem-solution fit, assumptions, risks, and neutral validation experiments before building.
          </p>
        </div>
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        <Button
          onClick={handleGenerate}
          isLoading={isGenerating}
          disabled={isGenerating}
          leftIcon={<Sparkles className="w-4 h-4" />}
          className="w-full justify-center"
        >
          {isGenerating ? 'Interrogating Business Assumptions...' : 'Interrogate & Validate Business Idea'}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-slate-900">Validation Synthesis</h2>
              <Badge variant="amber">Version {report.version}</Badge>
            </div>
            <p className="text-xs text-slate-500">
              Evaluated {report.created_at ? new Date(report.created_at).toLocaleDateString() : 'recently'} with deterministic risk heuristics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {versions.length > 1 && (
            <select
              value={selectedVersion || report.version}
              onChange={(e) => handleVersionChange(Number(e.target.value))}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {versions.map((v) => (
                <option key={v.id || v.version} value={v.version}>
                  Version {v.version} ({v.created_at ? new Date(v.created_at).toLocaleDateString() : 'Saved'})
                </option>
              ))}
            </select>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerate}
            isLoading={isGenerating}
            disabled={isGenerating}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            {isGenerating ? 'Regenerating...' : 'Regenerate'}
          </Button>
        </div>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {/* Executive Readiness Card */}
      <Card className="border-indigo-100 bg-gradient-to-r from-indigo-50/50 to-white">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-indigo-100 text-indigo-700 rounded-xl">
              <Zap className="w-5 h-5" />
            </div>
            <div className="space-y-1 w-full">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">Readiness Assessment</span>
                <Badge variant="indigo">{safeText(data.summary?.qualitative_readiness_assessment, 'In Progress')}</Badge>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">{safeText(data.overview)}</p>
              {data.summary?.strongest_supporting_evidence && (
                <p className="text-xs text-slate-600 pt-2 border-t border-indigo-100/60">
                  <strong className="text-indigo-900">Strongest Supporting Evidence:</strong>{' '}
                  {Array.isArray(data.summary.strongest_supporting_evidence)
                    ? data.summary.strongest_supporting_evidence.map((ev) => safeText(ev)).join('; ')
                    : safeText(data.summary.strongest_supporting_evidence)}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Problem-Solution Fit & Customer Clarity */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="w-4 h-4 text-indigo-600" /> Problem–Solution Fit
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase">Core Problem</span>
              <p className="text-slate-800 font-medium mt-0.5">{safeText(data.problem_solution_fit?.problem_statement)}</p>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Who Experiences It</span>
                <p className="text-xs text-slate-700 mt-0.5">{safeText(data.problem_solution_fit?.who_experiences_it)}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Severity / Frequency</span>
                <p className="text-xs text-slate-700 mt-0.5">{safeText(data.problem_solution_fit?.frequency_and_severity)}</p>
              </div>
            </div>
            {data.problem_solution_fit?.existing_alternatives && data.problem_solution_fit.existing_alternatives.length > 0 && (
              <div className="pt-2 border-t border-slate-100">
                <span className="text-xs font-semibold text-slate-500 uppercase">Existing Alternatives</span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {data.problem_solution_fit.existing_alternatives.map((alt, i) => (
                    <Badge key={`alt-${i}`} variant="slate" size="sm">{safeText(alt)}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-600" /> Target Customer & Adoption
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase">Primary Segment</span>
              <p className="text-slate-800 font-medium mt-0.5">{safeText(data.target_customer_clarity?.primary_segment)}</p>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Buyer vs End User</span>
                <p className="text-xs text-slate-700 mt-0.5">{safeText(data.target_customer_clarity?.buyer_vs_end_user)}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Adoption Barriers</span>
                <ul className="text-xs text-slate-700 list-disc list-inside mt-0.5">
                  {data.target_customer_clarity?.adoption_barriers?.slice(0, 3).map((b, i) => (
                    <li key={`b-${i}`}>{safeText(b)}</li>
                  ))}
                </ul>
              </div>
            </div>
            {data.target_customer_clarity?.unvalidated_assumptions && data.target_customer_clarity.unvalidated_assumptions.length > 0 && (
              <div className="pt-2 border-t border-slate-100">
                <span className="text-xs font-semibold text-slate-500 uppercase">Unvalidated Assumptions</span>
                <ul className="text-xs text-amber-800 list-disc list-inside mt-1">
                  {data.target_customer_clarity.unvalidated_assumptions.slice(0, 3).map((a, i) => (
                    <li key={`a-${i}`}>{safeText(a)}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Value Proposition Assessment (if present) */}
      {data.value_proposition_assessment && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-600" /> Value Proposition & Differentiation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {data.value_proposition_assessment.core_benefit && (
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Core Benefit Delivered</span>
                <p className="text-slate-800 font-medium mt-0.5">{safeText(data.value_proposition_assessment.core_benefit)}</p>
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-100">
              {data.value_proposition_assessment.differentiation_hypotheses && data.value_proposition_assessment.differentiation_hypotheses.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase">Differentiation Hypotheses</span>
                  <ul className="text-xs text-slate-700 list-disc list-inside mt-1 space-y-0.5">
                    {data.value_proposition_assessment.differentiation_hypotheses.map((d, i) => (
                      <li key={`d-${i}`}>{safeText(d)}</li>
                    ))}
                  </ul>
                </div>
              )}
              {data.value_proposition_assessment.potential_weaknesses && data.value_proposition_assessment.potential_weaknesses.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase">Potential Weaknesses</span>
                  <ul className="text-xs text-rose-800 list-disc list-inside mt-1 space-y-0.5">
                    {data.value_proposition_assessment.potential_weaknesses.map((w, i) => (
                      <li key={`pw-${i}`}>{safeText(w)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* SWOT Quadrant Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">SWOT Strategic Analysis Matrix</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strengths */}
            <div className="bg-emerald-50/60 border border-emerald-200/80 rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <h4 className="font-bold text-xs uppercase tracking-wider text-emerald-900">Strengths (Internal)</h4>
              </div>
              <ul className="space-y-1.5 text-xs text-emerald-950">
                {data.swot_analysis?.strengths?.map((s, i) => (
                  <li key={`s-${i}`} className="flex items-start gap-1.5">
                    <span className="text-emerald-500 font-bold">•</span>
                    <span>{safeText(s)}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Weaknesses */}
            <div className="bg-amber-50/60 border border-amber-200/80 rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                <h4 className="font-bold text-xs uppercase tracking-wider text-amber-900">Weaknesses (Internal)</h4>
              </div>
              <ul className="space-y-1.5 text-xs text-amber-950">
                {data.swot_analysis?.weaknesses?.map((w, i) => (
                  <li key={`w-${i}`} className="flex items-start gap-1.5">
                    <span className="text-amber-500 font-bold">•</span>
                    <span>{safeText(w)}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Opportunities */}
            <div className="bg-sky-50/60 border border-sky-200/80 rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span>
                <h4 className="font-bold text-xs uppercase tracking-wider text-sky-900">Opportunities (External)</h4>
              </div>
              <ul className="space-y-1.5 text-xs text-sky-950">
                {data.swot_analysis?.opportunities?.map((o, i) => (
                  <li key={`o-${i}`} className="flex items-start gap-1.5">
                    <span className="text-sky-500 font-bold">•</span>
                    <span>{safeText(o)}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Threats */}
            <div className="bg-rose-50/60 border border-rose-200/80 rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                <h4 className="font-bold text-xs uppercase tracking-wider text-rose-900">Threats (External)</h4>
              </div>
              <ul className="space-y-1.5 text-xs text-rose-950">
                {data.swot_analysis?.threats?.map((t, i) => (
                  <li key={`t-${i}`} className="flex items-start gap-1.5">
                    <span className="text-rose-500 font-bold">•</span>
                    <span>{safeText(t)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Business Risks & Mitigations Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-500" /> Business Risk Register & Mitigation Strategy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase font-bold text-[10px] bg-slate-50">
                  <th className="py-2.5 px-3">Risk Category</th>
                  <th className="py-2.5 px-3">Description</th>
                  <th className="py-2.5 px-2">Likelihood</th>
                  <th className="py-2.5 px-2">Impact</th>
                  <th className="py-2.5 px-3">Suggested Mitigation</th>
                  <th className="py-2.5 px-3">Recommended Next Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.business_risks?.map((risk, idx) => (
                  <tr key={`risk-${idx}`} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-semibold text-slate-800 whitespace-nowrap">{safeText(risk.category, 'General')}</td>
                    <td className="py-2.5 px-3 text-slate-700 min-w-[200px]">{safeText(risk.description)}</td>
                    <td className="py-2.5 px-2 whitespace-nowrap">
                      <Badge variant={risk.likelihood === 'High' ? 'rose' : risk.likelihood === 'Medium' ? 'amber' : 'slate'} size="sm">
                        {safeText(risk.likelihood, 'Medium')}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-2 whitespace-nowrap">
                      <Badge variant={risk.impact === 'High' ? 'rose' : risk.impact === 'Medium' ? 'amber' : 'slate'} size="sm">
                        {safeText(risk.impact, 'Medium')}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 min-w-[200px]">{safeText(risk.suggested_mitigation)}</td>
                    <td className="py-2.5 px-3 text-indigo-700 font-medium min-w-[180px]">{safeText(risk.recommended_next_action)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Validation Experiments & Neutral Interview Questions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Actionable Validation Experiments
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.validation_experiments && data.validation_experiments.length > 0 ? (
              data.validation_experiments.map((exp, i) => (
                <ValidationExperimentCard key={`exp-${i}`} experiment={exp} index={i} />
              ))
            ) : (
              <p className="text-xs text-slate-400 italic">No validation experiments configured.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-indigo-600" /> Neutral Customer Interview Questions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-500 mb-3">
              Non-leading inquiries focusing on past behavior and current workarounds rather than speculative praise:
            </p>
            <div className="space-y-2.5">
              {data.interview_questions && data.interview_questions.length > 0 ? (
                data.interview_questions.map((q, idx) => (
                  <ValidationQuestionCard key={`q-${idx}`} question={q} index={idx} />
                ))
              ) : (
                <p className="text-xs text-slate-400 italic">No discovery interview questions generated yet.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
