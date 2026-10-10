import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Lightbulb,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Target,
  Zap,
} from 'lucide-react';
import { api } from '../../services/api';
import { BlueprintVersionItem, ValidationReportData, ValidationReportResponse } from '../../types';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Alert } from '../ui/Alert';

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

  const data: ValidationReportData | null = report?.content_json || report?.content || null;

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
              Evaluated {new Date(report.created_at).toLocaleDateString()} with deterministic risk heuristics
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
                <option key={v.id} value={v.version}>
                  Version {v.version} ({new Date(v.created_at).toLocaleDateString()})
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
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">Readiness Assessment</span>
                <Badge variant="indigo">{data.summary?.qualitative_readiness_assessment || 'In Progress'}</Badge>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">{data.overview}</p>
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
              <p className="text-slate-800 font-medium mt-0.5">{data.problem_solution_fit?.problem_statement}</p>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Who Experiences It</span>
                <p className="text-xs text-slate-700 mt-0.5">{data.problem_solution_fit?.who_experiences_it}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Severity / Frequency</span>
                <p className="text-xs text-slate-700 mt-0.5">{data.problem_solution_fit?.frequency_and_severity}</p>
              </div>
            </div>
            <div className="pt-2 border-t border-slate-100">
              <span className="text-xs font-semibold text-slate-500 uppercase">Existing Alternatives</span>
              <div className="flex flex-wrap gap-1.5 mt-1">
                {data.problem_solution_fit?.existing_alternatives?.map((alt, i) => (
                  <Badge key={i} variant="slate" size="sm">{alt}</Badge>
                ))}
              </div>
            </div>
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
              <p className="text-slate-800 font-medium mt-0.5">{data.target_customer_clarity?.primary_segment}</p>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Buyer vs End User</span>
                <p className="text-xs text-slate-700 mt-0.5">{data.target_customer_clarity?.buyer_vs_end_user}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Adoption Barriers</span>
                <ul className="text-xs text-slate-700 list-disc list-inside mt-0.5">
                  {data.target_customer_clarity?.adoption_barriers?.slice(0, 2).map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="pt-2 border-t border-slate-100">
              <span className="text-xs font-semibold text-slate-500 uppercase">Unvalidated Assumptions</span>
              <ul className="text-xs text-amber-800 list-disc list-inside mt-1">
                {data.target_customer_clarity?.unvalidated_assumptions?.slice(0, 2).map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

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
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-emerald-500 font-bold">•</span>
                    <span>{s}</span>
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
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-amber-500 font-bold">•</span>
                    <span>{w}</span>
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
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-sky-500 font-bold">•</span>
                    <span>{o}</span>
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
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-rose-500 font-bold">•</span>
                    <span>{t}</span>
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
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-semibold text-slate-800 whitespace-nowrap">{risk.category}</td>
                    <td className="py-2.5 px-3 text-slate-700 min-w-[200px]">{risk.description}</td>
                    <td className="py-2.5 px-2 whitespace-nowrap">
                      <Badge variant={risk.likelihood === 'High' ? 'rose' : risk.likelihood === 'Medium' ? 'amber' : 'slate'} size="sm">
                        {risk.likelihood}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-2 whitespace-nowrap">
                      <Badge variant={risk.impact === 'High' ? 'rose' : risk.impact === 'Medium' ? 'amber' : 'slate'} size="sm">
                        {risk.impact}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 min-w-[200px]">{risk.suggested_mitigation}</td>
                    <td className="py-2.5 px-3 text-indigo-700 font-medium min-w-[180px]">{risk.recommended_next_action}</td>
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
            {data.validation_experiments?.map((exp, i) => (
              <div key={i} className="border border-slate-200 rounded-xl p-3.5 space-y-2 bg-slate-50/50">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-bold text-sm text-slate-900">{exp.experiment_name}</h4>
                  <div className="flex items-center gap-1.5">
                    <Badge variant="indigo" size="sm">{exp.experiment_type}</Badge>
                    <Badge variant="slate" size="sm">{exp.estimated_duration}</Badge>
                  </div>
                </div>
                <p className="text-xs text-slate-600"><strong>Hypothesis:</strong> {exp.hypothesis}</p>
                <div className="text-xs text-slate-700 pt-1.5 border-t border-slate-200/60">
                  <span className="font-semibold text-slate-900">Success Criteria:</span> {exp.success_criteria}
                </div>
              </div>
            ))}
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
            <ol className="space-y-2.5 text-xs text-slate-800 list-decimal list-inside">
              {data.interview_questions?.map((q, idx) => (
                <li key={idx} className="p-2 rounded-lg bg-slate-50 border border-slate-100 font-medium">
                  {q}
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
