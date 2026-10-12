import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Compass,
  ExternalLink,
  Layers,
  LineChart,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
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
  isLoading?: boolean;
  onResearchUpdated: () => void;
}

export const MarketResearchView: React.FC<MarketResearchViewProps> = ({
  projectId,
  research,
  versions,
  isLoading = false,
  onResearchUpdated,
}) => {
  const [currentResearch, setCurrentResearch] = useState<MarketResearchResponse | null>(research);
  const [selectedVersion, setSelectedVersion] = useState<number | undefined>(research?.version);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isLoadingVersion, setIsLoadingVersion] = useState<boolean>(false);
  const [error, setError] = useState<{ message: string; isAuth?: boolean; isNetwork?: boolean } | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Sync internal state whenever research prop changes from parent
  useEffect(() => {
    setCurrentResearch(research);
    if (research?.version) {
      setSelectedVersion(research.version);
    }
  }, [research]);

  // Robust data extraction supporting both content_json and content properties
  const data: MarketResearchReportData | null =
    currentResearch?.content_json || currentResearch?.content || null;

  // Extract source citations safely from either the report data or the response container
  const rawSources: any = data?.sources || currentResearch?.sources || [];
  const sources: SourceItem[] = Array.isArray(rawSources) ? rawSources : [];

  const handleGenerate = async () => {
    if (isGenerating) return; // Prevent duplicate concurrent submissions
    setIsGenerating(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await api.marketResearch.generate(projectId);
      setCurrentResearch(res);
      setSelectedVersion(res.version);
      setSuccess('Market and competitor intelligence report successfully retrieved and synthesized.');
      onResearchUpdated();
    } catch (err: any) {
      const status = err?.status || err?.response?.status;
      const isAuth = status === 401 || status === 403;
      const isNetwork = !window.navigator.onLine || err?.message?.includes('fetch') || err?.message?.includes('Network');
      setError({
        message: err?.message || 'Failed to generate market research report. Please try again.',
        isAuth,
        isNetwork,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleVersionChange = async (ver: number) => {
    if (isLoadingVersion || isGenerating) return;
    setIsLoadingVersion(true);
    setError(null);
    setSelectedVersion(ver);
    try {
      const res = await api.marketResearch.get(projectId, ver);
      setCurrentResearch(res);
    } catch (err: any) {
      setError({
        message: err?.message || `Failed to load market research version ${ver}.`,
        isNetwork: !window.navigator.onLine,
      });
    } finally {
      setIsLoadingVersion(false);
    }
  };

  // 1. Initial Loading State
  if (isLoading || isLoadingVersion) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-16 text-center max-w-xl mx-auto my-8 space-y-4 shadow-xs">
        <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
          <RefreshCw className="w-6 h-6 animate-spin" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-900">Loading Market Intelligence</h3>
          <p className="text-xs text-slate-500">
            {isLoadingVersion
              ? `Retrieving historical report version ${selectedVersion}...`
              : 'Retrieving latest market signals and competitive benchmark data...'}
          </p>
        </div>
      </div>
    );
  }

  // 2. Generating State Banner (duplicate submission locked)
  const generatingOverlay = isGenerating && (
    <div className="bg-gradient-to-r from-sky-500/10 via-indigo-500/10 to-sky-500/10 border border-sky-300 rounded-xl p-4 flex items-center gap-3 animate-pulse">
      <RefreshCw className="w-5 h-5 text-sky-600 animate-spin shrink-0" />
      <div className="flex-1">
        <h4 className="text-xs font-bold text-sky-900">Conducting Live Market & Competitor Synthesis</h4>
        <p className="text-[11px] text-sky-700">
          Querying search providers, inspecting competitor landscapes, analyzing TAM/SAM/SOM boundaries, and synthesizing strategic signals...
        </p>
      </div>
    </div>
  );

  // 3. Empty State (No report generated yet)
  if (!currentResearch || !data) {
    return (
      <div className="space-y-6">
        {generatingOverlay}

        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-10 text-center max-w-xl mx-auto space-y-6 my-8">
          <div className="w-14 h-14 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto shadow-xs">
            <Compass className="w-7 h-7" />
          </div>

          <div className="space-y-2">
            <h3 className="text-lg font-bold text-slate-900">Market & Competitor Intelligence</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
              Synthesize verified external web evidence, uncover direct and alternative competitors, evaluate pricing models, estimate TAM/SAM/SOM market sizes, and map entry barriers.
            </p>
          </div>

          {error && (
            <Alert
              type="error"
              message={error.message}
              onClose={() => setError(null)}
            />
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold uppercase tracking-wider text-sky-700 block mb-1">
                Competitors
              </span>
              <p className="text-[11px] text-slate-600">
                Identifies real rivals, pricing models, feature sets, strengths, and weaknesses.
              </p>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 block mb-1">
                Market Sizing
              </span>
              <p className="text-[11px] text-slate-600">
                Breaks down TAM, SAM, and SOM qualitative sizing with methodology caveats.
              </p>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block mb-1">
                Evidence Base
              </span>
              <p className="text-[11px] text-slate-600">
                Grounded in web citations or transparently marked as AI heuristic modeling.
              </p>
            </div>
          </div>

          <div className="pt-2">
            <Button
              onClick={handleGenerate}
              isLoading={isGenerating}
              disabled={isGenerating}
              leftIcon={<Sparkles className="w-4 h-4" />}
              className="w-full sm:w-auto px-8 justify-center"
            >
              {isGenerating ? 'Synthesizing Market Intelligence...' : 'Execute Market & Competitor Research'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // 4. Successful Report Display
  const hasLiveSources = sources.length > 0;

  return (
    <div className="space-y-6">
      {generatingOverlay}

      {/* Top Header & Version Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-slate-900">Competitive Landscape & Market Signals</h2>
              <Badge variant="sky">Version {currentResearch.version}</Badge>
            </div>
            <p className="text-xs text-slate-500">
              {hasLiveSources
                ? `Grounded in ${sources.length} retrieved external search citations • SSRF Protected`
                : 'Heuristic Analytical Mode • No external live search citations retrieved'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {versions && versions.length > 1 && (
            <select
              value={selectedVersion || currentResearch.version}
              onChange={(e) => handleVersionChange(Number(e.target.value))}
              disabled={isGenerating || isLoadingVersion}
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
            {isGenerating ? 'Synthesizing...' : 'Refresh Research'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="space-y-2">
          <Alert
            type="error"
            message={error.message}
            onClose={() => setError(null)}
          />
          {error.isNetwork && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerate}
              leftIcon={<RefreshCw className="w-3 h-3" />}
            >
              Retry Request
            </Button>
          )}
        </div>
      )}

      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {/* No Live External Evidence Informational Banner */}
      {!hasLiveSources && (
        <div className="bg-amber-50/90 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1 text-xs text-amber-900 leading-relaxed">
            <h4 className="font-bold text-amber-950">
              Heuristic Intelligence Mode — No Live External Evidence Retrieved
            </h4>
            <p>
              External web search providers returned zero direct citations for these query terms. The analysis below was generated using established domain heuristics, market modeling, and foundational industry dynamics.
            </p>
            <p className="text-[11px] text-amber-800 font-medium">
              Important: Competitor pricing, market sizes, and market shares are qualitative planning benchmarks and should be validated through direct founder interviews and primary quotes before committing capital.
            </p>
          </div>
        </div>
      )}

      {/* Executive Market Summary Card */}
      <Card className="border-sky-100 bg-gradient-to-r from-sky-50/40 via-white to-indigo-50/30">
        <CardContent className="pt-6">
          <div className="space-y-2.5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="sky">{data.industry_definition || 'Target Sector'}</Badge>
              {hasLiveSources ? (
                <Badge variant="emerald" size="sm">Evidence Grounded</Badge>
              ) : (
                <Badge variant="amber" size="sm">Heuristic Model</Badge>
              )}
            </div>
            <p className="text-sm text-slate-800 leading-relaxed font-medium">
              {data.executive_summary}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Market Sizing: TAM / SAM / SOM */}
      {data.market_sizing && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-600" /> Market Sizing & Addressable Boundaries (TAM / SAM / SOM)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.market_sizing.market_definition && (
              <p className="text-xs text-slate-600 italic">
                Scope: {data.market_sizing.market_definition}
              </p>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">
                    Total Addressable Market (TAM)
                  </span>
                  <Badge variant="slate" size="sm">Macro</Badge>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  {data.market_sizing.tam_description || 'Global industry macro boundary.'}
                </p>
              </div>

              <div className="p-4 bg-sky-50/50 border border-sky-200 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-sky-700">
                    Serviceable Addressable Market (SAM)
                  </span>
                  <Badge variant="sky" size="sm">Segment</Badge>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  {data.market_sizing.sam_description || 'Reachable target customer segment.'}
                </p>
              </div>

              <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-700">
                    Serviceable Obtainable Market (SOM)
                  </span>
                  <Badge variant="emerald" size="sm">Near-Term Target</Badge>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  {data.market_sizing.som_description || 'Realistic early-stage beachhead share.'}
                </p>
              </div>
            </div>

            {data.market_sizing.sizing_caveats && (
              <p className="text-[11px] text-slate-500 bg-slate-100/70 p-2.5 rounded-lg border border-slate-200/60">
                <strong>Methodology Caveat:</strong> {data.market_sizing.sizing_caveats}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Strategic Market Trends */}
      {data.market_trends && data.market_trends.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <LineChart className="w-4 h-4 text-indigo-600" /> Strategic Market Trends & Signals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.market_trends.map((t, idx) => (
                <div key={idx} className="border border-slate-200 rounded-xl p-4 space-y-2 bg-slate-50/50">
                  <h4 className="font-bold text-sm text-slate-900">{t.trend_title}</h4>
                  <p className="text-xs text-slate-600 leading-relaxed">{t.description}</p>
                  <div className="pt-2 border-t border-slate-200/60 text-xs text-indigo-700">
                    <strong>Founder Implication:</strong> {t.implications_for_founder}
                  </div>
                  {t.supporting_sources && t.supporting_sources.length > 0 && (
                    <div className="pt-1 flex flex-wrap gap-1">
                      {t.supporting_sources.map((src, sIdx) => {
                        const isLiveUrl = src && src.startsWith('http');
                        return isLiveUrl ? (
                          <a
                            key={sIdx}
                            href={src}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[10px] text-sky-600 hover:text-sky-800 bg-sky-50 px-2 py-0.5 rounded"
                          >
                            Citation <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        ) : (
                          <span
                            key={sIdx}
                            className="text-[10px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded italic"
                          >
                            {src || 'Model estimate'}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Barriers to Entry & Distribution Channels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.barriers_to_entry && data.barriers_to_entry.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-600" /> Structural Barriers to Entry
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {data.barriers_to_entry.map((barrier, bIdx) => (
                  <li key={bIdx} className="text-xs text-slate-700 flex items-start gap-2 bg-amber-50/30 p-2.5 rounded-lg border border-amber-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                    <span>{barrier}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {data.distribution_channels && data.distribution_channels.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-600" /> Viable Distribution Channels
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {data.distribution_channels.map((channel, cIdx) => (
                  <li key={cIdx} className="text-xs text-slate-700 flex items-start gap-2 bg-emerald-50/30 p-2.5 rounded-lg border border-emerald-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span>{channel}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Competitor Benchmark Profiles */}
      {data.competitors && data.competitors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="w-4 h-4 text-sky-600" /> Direct & Alternative Competitor Profiles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {data.competitors.map((comp, idx) => (
                <div
                  key={idx}
                  className="border border-slate-200 rounded-xl p-5 space-y-3 bg-white hover:border-slate-300 transition-all shadow-2xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="font-bold text-base text-slate-900">{comp.name}</h4>
                      {comp.website && (
                        <a
                          href={comp.website.startsWith('http') ? comp.website : `https://${comp.website}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-sky-600 hover:underline flex items-center gap-1 mt-0.5"
                        >
                          {comp.website.replace(/^https?:\/\//, '')} <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    <Badge variant="slate" size="sm">
                      {comp.estimated_pricing || comp.pricing_model || 'Quote-based'}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-600">{comp.product_summary}</p>

                  <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs">
                    <div>
                      <span className="font-semibold text-slate-700">Target Audience:</span>{' '}
                      <span className="text-slate-600">{comp.target_audience}</span>
                    </div>
                    {comp.key_features && comp.key_features.length > 0 && (
                      <div>
                        <span className="font-semibold text-slate-700">Key Features:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {comp.key_features.map((f, fIdx) => (
                            <Badge key={fIdx} variant="slate" size="sm">{f}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {comp.positioning && (
                      <div>
                        <span className="font-semibold text-slate-700">Positioning & Edge:</span>
                        <p className="text-slate-600 mt-0.5">{comp.positioning}</p>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-[11px]">
                    <div className="bg-emerald-50/60 p-2.5 rounded-lg border border-emerald-100/60">
                      <span className="font-bold text-emerald-800 uppercase block mb-1">Strengths</span>
                      <ul className="text-emerald-900 list-disc list-inside space-y-0.5">
                        {comp.strengths && comp.strengths.length > 0 ? (
                          comp.strengths.slice(0, 3).map((s, i) => <li key={i}>{s}</li>)
                        ) : (
                          <li className="list-none text-emerald-600">None documented</li>
                        )}
                      </ul>
                    </div>
                    <div className="bg-rose-50/60 p-2.5 rounded-lg border border-rose-100/60">
                      <span className="font-bold text-rose-800 uppercase block mb-1">Weaknesses</span>
                      <ul className="text-rose-900 list-disc list-inside space-y-0.5">
                        {comp.weaknesses && comp.weaknesses.length > 0 ? (
                          comp.weaknesses.slice(0, 3).map((w, i) => <li key={i}>{w}</li>)
                        ) : (
                          <li className="list-none text-rose-600">None documented</li>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Comparison Matrix Table */}
      {data.comparison_matrix && data.comparison_matrix.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Search className="w-4 h-4 text-indigo-600" /> Head-to-Head Comparison Matrix
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 uppercase font-bold text-[10px] bg-slate-50">
                    <th className="py-2.5 px-3">Evaluation Criterion</th>
                    <th className="py-2.5 px-3 text-indigo-700 bg-indigo-50/50">Our Venture</th>
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
                        <td key={vIdx} className="py-2.5 px-3 text-slate-600">
                          {typeof val === 'object' && val !== null ? JSON.stringify(val) : String(val ?? '—')}
                        </td>
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
      {hasLiveSources && (
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
                    <span className="text-xs font-medium text-slate-600">
                      Retrieved {src.retrieved_at ? new Date(src.retrieved_at).toLocaleDateString() : 'Recent'}
                    </span>
                  </div>
                  <p className="text-slate-600 leading-relaxed">{src.snippet}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Methodology Disclaimer */}
      {data.research_methodology_disclaimer && (
        <div className="text-[11px] text-slate-500 text-center py-2">
          {data.research_methodology_disclaimer}
        </div>
      )}
    </div>
  );
};
