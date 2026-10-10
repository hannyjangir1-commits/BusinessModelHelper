import React, { useState } from 'react';
import {
  Compass,
  ExternalLink,
  Globe,
  Layers,
  LineChart,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  BlueprintVersionItem,
  MarketResearchReportData,
  MarketResearchResponse,
  SourceItem,
} from '../../types';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Alert } from '../ui/Alert';

interface MarketResearchViewProps {
  projectId: string;
  research: MarketResearchResponse | null;
  versions: BlueprintVersionItem[];
  onResearchUpdated: () => void;
}

export const MarketResearchView: React.FC<MarketResearchViewProps> = ({
  projectId,
  research,
  versions,
  onResearchUpdated,
}) => {
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [selectedVersion, setSelectedVersion] = useState<number | undefined>(research?.version);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setSuccess(null);
    try {
      await api.marketResearch.generate(projectId);
      setSuccess('Market and competitor intelligence report successfully retrieved and synthesized.');
      onResearchUpdated();
    } catch (err: any) {
      setError(err?.message || 'Failed to generate market research report.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleVersionChange = async (ver: number) => {
    setSelectedVersion(ver);
    try {
      await api.marketResearch.get(projectId, ver);
      onResearchUpdated();
    } catch (err: any) {
      setError(err?.message || 'Failed to load research version.');
    }
  };

  const data: MarketResearchReportData | null = research?.content || null;
  const sources: SourceItem[] = research?.sources || [];

  if (!research || !data) {
    return (
      <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8">
        <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
          <Compass className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-slate-900">Market & Competitor Intelligence</h3>
          <p className="text-sm text-slate-500">
            Conduct verified external research, analyze competitor pricing and positioning, and extract source-backed market signals.
          </p>
        </div>
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        <Button
          onClick={handleGenerate}
          isLoading={isGenerating}
          leftIcon={<Sparkles className="w-4 h-4" />}
          className="w-full justify-center"
        >
          Research Market & Competitors
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Version Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-slate-900">Competitive Landscape & Market Signals</h2>
              <Badge variant="sky">Version {research.version}</Badge>
            </div>
            <p className="text-xs text-slate-500">
              Grounded in {sources.length} retrieved external sources • SSRF Protected
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {versions.length > 1 && (
            <select
              value={selectedVersion || research.version}
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
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh Research
          </Button>
        </div>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {/* Executive Market Summary Card */}
      <Card className="border-sky-100 bg-gradient-to-r from-sky-50/40 to-white">
        <CardContent className="pt-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="sky">{data.industry_definition || 'Market Definition'}</Badge>
            </div>
            <p className="text-sm text-slate-800 leading-relaxed font-medium">{data.executive_summary}</p>
          </div>
        </CardContent>
      </Card>

      {/* Market Trends */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <LineChart className="w-4 h-4 text-indigo-600" /> Strategic Market Trends & Signals
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.market_trends?.map((t, idx) => (
              <div key={idx} className="border border-slate-200 rounded-xl p-4 space-y-2 bg-slate-50/50">
                <h4 className="font-bold text-sm text-slate-900">{t.trend_title}</h4>
                <p className="text-xs text-slate-600 leading-relaxed">{t.description}</p>
                <div className="pt-2 border-t border-slate-200/60 text-xs text-indigo-700">
                  <strong>Implication:</strong> {t.implications_for_founder}
                </div>
                {t.supporting_sources && t.supporting_sources.length > 0 && (
                  <div className="pt-1 flex flex-wrap gap-1">
                    {t.supporting_sources.map((src, sIdx) => (
                      <a
                        key={sIdx}
                        href={src}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[10px] text-sky-600 hover:text-sky-800 bg-sky-50 px-2 py-0.5 rounded"
                      >
                        Source citation <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Competitor Benchmark Profiles */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="w-4 h-4 text-sky-600" /> Direct & Alternative Competitor Profiles
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {data.competitors?.map((comp, idx) => (
              <div key={idx} className="border border-slate-200 rounded-xl p-5 space-y-3 bg-white hover:border-slate-300 transition-all">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="font-bold text-base text-slate-900">{comp.name}</h4>
                    {comp.website && (
                      <a
                        href={comp.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-sky-600 hover:underline flex items-center gap-1 mt-0.5"
                      >
                        {comp.website.replace('https://', '')} <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                  <Badge variant="slate" size="sm">{comp.estimated_pricing || comp.pricing_model}</Badge>
                </div>

                <p className="text-xs text-slate-600">{comp.product_summary}</p>

                <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs">
                  <div>
                    <span className="font-semibold text-slate-700">Target Audience:</span>{' '}
                    <span className="text-slate-600">{comp.target_audience}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-700">Key Features:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {comp.key_features?.map((f, fIdx) => (
                        <Badge key={fIdx} variant="slate" size="sm">{f}</Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-700">Positioning & Edge:</span>
                    <p className="text-slate-600 mt-0.5">{comp.positioning}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-[11px]">
                  <div className="bg-emerald-50/60 p-2 rounded-lg">
                    <span className="font-bold text-emerald-800 uppercase block mb-0.5">Strengths</span>
                    <ul className="text-emerald-900 list-disc list-inside">
                      {comp.strengths?.slice(0, 2).map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="bg-rose-50/60 p-2 rounded-lg">
                    <span className="font-bold text-rose-800 uppercase block mb-0.5">Weaknesses</span>
                    <ul className="text-rose-900 list-disc list-inside">
                      {comp.weaknesses?.slice(0, 2).map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Comparison Matrix Table */}
      {data.comparison_matrix && data.comparison_matrix.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Head-to-Head Comparison Matrix</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 uppercase font-bold text-[10px] bg-slate-50">
                    <th className="py-2.5 px-3">Evaluation Criterion</th>
                    <th className="py-2.5 px-3 text-indigo-700">Our Solution</th>
                    {Object.keys(data.comparison_matrix[0]?.competitor_comparison || {}).map((cName) => (
                      <th key={cName} className="py-2.5 px-3 text-slate-700">{cName}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.comparison_matrix.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="py-2.5 px-3 font-semibold text-slate-800">{row.criterion}</td>
                      <td className="py-2.5 px-3 text-indigo-700 font-medium bg-indigo-50/20">{row.founder_solution}</td>
                      {Object.values(row.competitor_comparison || {}).map((val, vIdx) => (
                        <td key={vIdx} className="py-2.5 px-3 text-slate-600">{val}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sourced Citations & Web Evidence */}
      {sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" /> Verified External Search Citations ({sources.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sources.map((src, i) => (
                <div key={i} className="text-xs p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-bold text-sky-700 hover:underline flex items-center gap-1.5"
                    >
                      {src.title || src.url} <ExternalLink className="w-3 h-3" />
                    </a>
                    <span className="text-[10px] text-slate-400">
                      Retrieved {new Date(src.retrieved_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-slate-600 leading-relaxed">{src.snippet}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
