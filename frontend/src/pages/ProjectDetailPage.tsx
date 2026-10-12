import React, { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  ArrowLeft,
  Bot,
  CheckCircle2,
  Compass,
  Cpu,
  Download,
  Edit2,
  History,
  Layers,
  Milestone,
  RefreshCw,
  Save,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { api, isAbortError, isNotFoundError } from '../services/api';
import {
  Blueprint,
  BlueprintVersionItem,
  BMCBlock,
  BusinessModelCanvasData,
  GenerationRun,
  MarketResearchResponse,
  Project,
  RoadmapResponse,
  TechnologyStackData,
  TechRecommendationItem,
  ValidationReportResponse,
} from '../types';
import { Button } from '../components/ui/Button';
import { IdeaValidatorView } from '../components/modules/IdeaValidatorView';
import { MarketResearchView } from '../components/modules/MarketResearchView';
import { RoadmapView } from '../components/modules/RoadmapView';
import { CopilotWorkspaceView } from '../components/modules/CopilotWorkspaceView';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Alert } from '../components/ui/Alert';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';

type TabType =
  | 'bmc'
  | 'tech'
  | 'validator'
  | 'research'
  | 'roadmap'
  | 'copilot'
  | 'overview'
  | 'history';

const normalizeTab = (tab?: string): TabType => {
  if (!tab) return 'bmc';
  const clean = tab.toLowerCase().trim();
  if (clean === 'market-research' || clean === 'research') return 'research';
  if (clean === 'validator' || clean === 'idea-validator') return 'validator';
  if (clean === 'roadmap' || clean === 'execution-roadmap') return 'roadmap';
  if (clean === 'copilot' || clean === 'blueprint-copilot') return 'copilot';
  if (clean === 'tech' || clean === 'technology-stack' || clean === 'tech-stack') return 'tech';
  if (clean === 'overview') return 'overview';
  if (clean === 'history') return 'history';
  return 'bmc';
};

export const ModuleLoadingCard: React.FC<{ message: string }> = ({ message }) => (
  <div
    role="status"
    aria-live="polite"
    className="bg-white border border-slate-200 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8 animate-pulse shadow-xs"
  >
    <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
      <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
    </div>
    <p className="text-xs font-semibold text-slate-600">{message}</p>
  </div>
);

export const ModuleErrorCard: React.FC<{
  title: string;
  message: string;
  onRetry: () => void;
  moduleName?: string;
}> = ({ title, message, onRetry, moduleName = 'module' }) => (
  <div
    role="alert"
    aria-live="polite"
    className="bg-rose-50/70 border border-rose-200 rounded-2xl p-10 text-center max-w-lg mx-auto space-y-4 my-8"
  >
    <div className="w-12 h-12 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
      <AlertTriangle className="w-6 h-6 text-rose-600" aria-hidden="true" />
    </div>
    <div className="space-y-1">
      <h3 className="text-base font-bold text-slate-900">{title}</h3>
      <p className="text-xs text-rose-700">{message}</p>
    </div>
    <Button
      variant="outline"
      size="sm"
      onClick={onRetry}
      leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
      aria-label={`Retry loading ${moduleName}`}
    >
      Retry
    </Button>
  </div>
);

interface ProjectDetailPageProps {
  projectId: string;
  initialTab?: string;
  onNavigate: (path: string) => void;
}

export const ProjectDetailPage: React.FC<ProjectDetailPageProps> = ({ projectId, initialTab, onNavigate }) => {
  const [project, setProject] = useState<Project | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>(() => normalizeTab(initialTab));

  useEffect(() => {
    if (initialTab) {
      setActiveTab(normalizeTab(initialTab));
    }
  }, [initialTab]);

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    const tabSlug = tab === 'research' ? 'market-research' : tab;
    window.history.replaceState({}, '', `/projects/${projectId}/${tabSlug}`);
  };

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Business Model Canvas State
  const [bmcBlueprint, setBmcBlueprint] = useState<Blueprint | null>(null);
  const [bmcVersions, setBmcVersions] = useState<BlueprintVersionItem[]>([]);
  const [bmcLoading, setBmcLoading] = useState<boolean>(true);
  const [bmcError, setBmcError] = useState<string | null>(null);
  const [bmcVersionError, setBmcVersionError] = useState<string | null>(null);
  const [isGeneratingBmc, setIsGeneratingBmc] = useState<boolean>(false);
  const [editingBmcBlockKey, setEditingBmcBlockKey] = useState<string | null>(null);
  const [editingBmcData, setEditingBmcData] = useState<BusinessModelCanvasData | null>(null);

  // Technology Stack State
  const [techBlueprint, setTechBlueprint] = useState<Blueprint | null>(null);
  const [techVersions, setTechVersions] = useState<BlueprintVersionItem[]>([]);
  const [techLoading, setTechLoading] = useState<boolean>(true);
  const [techError, setTechError] = useState<string | null>(null);
  const [techVersionError, setTechVersionError] = useState<string | null>(null);
  const [isGeneratingTech, setIsGeneratingTech] = useState<boolean>(false);
  const [editingTechKey, setEditingTechKey] = useState<string | null>(null);
  const [editingTechData, setEditingTechData] = useState<TechnologyStackData | null>(null);

  // Module 1: Idea Validator State
  const [validatorReport, setValidatorReport] = useState<ValidationReportResponse | null>(null);
  const [validatorVersions, setValidatorVersions] = useState<BlueprintVersionItem[]>([]);
  const [validatorLoading, setValidatorLoading] = useState<boolean>(true);
  const [validatorError, setValidatorError] = useState<string | null>(null);
  const [validatorVersionError, setValidatorVersionError] = useState<string | null>(null);

  // Module 2: Market Research State
  const [marketResearch, setMarketResearch] = useState<MarketResearchResponse | null>(null);
  const [researchVersions, setResearchVersions] = useState<BlueprintVersionItem[]>([]);
  const [researchLoading, setResearchLoading] = useState<boolean>(true);
  const [researchError, setResearchError] = useState<string | null>(null);
  const [researchVersionError, setResearchVersionError] = useState<string | null>(null);

  // Module 3: Execution Roadmap State
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  const [roadmapLoading, setRoadmapLoading] = useState<boolean>(true);
  const [roadmapError, setRoadmapError] = useState<string | null>(null);

  // Generation History State
  const [historyRuns, setHistoryRuns] = useState<GenerationRun[]>([]);
  const [historyLoading, setHistoryLoading] = useState<boolean>(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // PDF Export State
  const [isExportingPdf, setIsExportingPdf] = useState<boolean>(false);

  // Request Guard & Cancellation
  const currentRequestIdRef = useRef<number>(0);
  const activeAbortControllerRef = useRef<AbortController | null>(null);

  const isStale = (requestId: number) => {
    return requestId !== currentRequestIdRef.current;
  };

  const loadProject = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    try {
      const p = await api.projects.get(projectId, { signal });
      if (isStale(reqId)) return;
      setProject(p);
      setError(null);
    } catch (err: any) {
      if (isAbortError(err) || isStale(reqId)) return;
      if (isNotFoundError(err)) {
        setProject(null);
      } else {
        setError(err?.message || 'Failed to load project details.');
      }
    } finally {
      if (!isStale(reqId)) {
        setLoading(false);
      }
    }
  };

  const loadBmc = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    setBmcLoading(true);
    setBmcError(null);
    setBmcVersionError(null);
    try {
      const [bpRes, verRes] = await Promise.allSettled([
        api.bmc.get(projectId, undefined, { signal }),
        api.bmc.listVersions(projectId, { signal }),
      ]);
      if (isStale(reqId)) return;

      if (bpRes.status === 'fulfilled') {
        setBmcBlueprint(bpRes.value);
        setBmcError(null);
      } else {
        const err = bpRes.reason;
        if (isAbortError(err)) return;
        if (isNotFoundError(err)) {
          setBmcBlueprint(null);
          setBmcError(null);
        } else {
          setBmcBlueprint(null);
          setBmcError(err?.message || 'Failed to load Business Model Canvas.');
        }
      }

      if (verRes.status === 'fulfilled') {
        setBmcVersions(verRes.value);
        setBmcVersionError(null);
      } else {
        const err = verRes.reason;
        if (!isAbortError(err)) {
          setBmcVersionError(err?.message || 'Failed to load version history.');
        }
      }
    } finally {
      if (!isStale(reqId)) {
        setBmcLoading(false);
      }
    }
  };

  const loadBmcVersions = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    try {
      const vers = await api.bmc.listVersions(projectId, { signal });
      if (isStale(reqId)) return;
      setBmcVersions(vers);
      setBmcVersionError(null);
    } catch (err: any) {
      if (!isAbortError(err) && !isStale(reqId)) {
        setBmcVersionError(err?.message || 'Failed to load version history.');
      }
    }
  };

  const loadTech = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    setTechLoading(true);
    setTechError(null);
    setTechVersionError(null);
    try {
      const [bpRes, verRes] = await Promise.allSettled([
        api.techStack.get(projectId, undefined, { signal }),
        api.techStack.listVersions(projectId, { signal }),
      ]);
      if (isStale(reqId)) return;

      if (bpRes.status === 'fulfilled') {
        setTechBlueprint(bpRes.value);
        setTechError(null);
      } else {
        const err = bpRes.reason;
        if (isAbortError(err)) return;
        if (isNotFoundError(err)) {
          setTechBlueprint(null);
          setTechError(null);
        } else {
          setTechBlueprint(null);
          setTechError(err?.message || 'Failed to load Technology Stack.');
        }
      }

      if (verRes.status === 'fulfilled') {
        setTechVersions(verRes.value);
        setTechVersionError(null);
      } else {
        const err = verRes.reason;
        if (!isAbortError(err)) {
          setTechVersionError(err?.message || 'Failed to load version history.');
        }
      }
    } finally {
      if (!isStale(reqId)) {
        setTechLoading(false);
      }
    }
  };

  const loadTechVersions = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    try {
      const vers = await api.techStack.listVersions(projectId, { signal });
      if (isStale(reqId)) return;
      setTechVersions(vers);
      setTechVersionError(null);
    } catch (err: any) {
      if (!isAbortError(err) && !isStale(reqId)) {
        setTechVersionError(err?.message || 'Failed to load version history.');
      }
    }
  };

  const loadValidator = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    setValidatorLoading(true);
    setValidatorError(null);
    setValidatorVersionError(null);
    try {
      const [valRes, verRes] = await Promise.allSettled([
        api.validator.get(projectId, undefined, { signal }),
        api.validator.listVersions(projectId, { signal }),
      ]);
      if (isStale(reqId)) return;

      if (valRes.status === 'fulfilled') {
        setValidatorReport(valRes.value);
        setValidatorError(null);
      } else {
        const err = valRes.reason;
        if (isAbortError(err)) return;
        if (isNotFoundError(err)) {
          setValidatorReport(null);
          setValidatorError(null);
        } else {
          setValidatorReport(null);
          setValidatorError(err?.message || 'Failed to load Idea Validator report.');
        }
      }

      if (verRes.status === 'fulfilled') {
        setValidatorVersions(verRes.value);
        setValidatorVersionError(null);
      } else {
        const err = verRes.reason;
        if (!isAbortError(err)) {
          setValidatorVersionError(err?.message || 'Failed to load version history.');
        }
      }
    } finally {
      if (!isStale(reqId)) {
        setValidatorLoading(false);
      }
    }
  };

  const loadValidatorVersions = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    try {
      const vers = await api.validator.listVersions(projectId, { signal });
      if (isStale(reqId)) return;
      setValidatorVersions(vers);
      setValidatorVersionError(null);
    } catch (err: any) {
      if (!isAbortError(err) && !isStale(reqId)) {
        setValidatorVersionError(err?.message || 'Failed to load version history.');
      }
    }
  };

  const loadMarketResearch = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    setResearchLoading(true);
    setResearchError(null);
    setResearchVersionError(null);
    try {
      const [resRes, verRes] = await Promise.allSettled([
        api.marketResearch.get(projectId, undefined, { signal }),
        api.marketResearch.listVersions(projectId, { signal }),
      ]);
      if (isStale(reqId)) return;

      if (resRes.status === 'fulfilled') {
        setMarketResearch(resRes.value);
        setResearchError(null);
      } else {
        const err = resRes.reason;
        if (isAbortError(err)) return;
        if (isNotFoundError(err)) {
          setMarketResearch(null);
          setResearchError(null);
        } else {
          setMarketResearch(null);
          setResearchError(err?.message || 'Failed to load market research.');
        }
      }

      if (verRes.status === 'fulfilled') {
        setResearchVersions(verRes.value);
        setResearchVersionError(null);
      } else {
        const err = verRes.reason;
        if (!isAbortError(err)) {
          setResearchVersionError(err?.message || 'Failed to load version history.');
        }
      }
    } finally {
      if (!isStale(reqId)) {
        setResearchLoading(false);
      }
    }
  };

  const loadMarketResearchVersions = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    try {
      const vers = await api.marketResearch.listVersions(projectId, { signal });
      if (isStale(reqId)) return;
      setResearchVersions(vers);
      setResearchVersionError(null);
    } catch (err: any) {
      if (!isAbortError(err) && !isStale(reqId)) {
        setResearchVersionError(err?.message || 'Failed to load version history.');
      }
    }
  };

  const loadRoadmap = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    setRoadmapLoading(true);
    setRoadmapError(null);
    try {
      const rd = await api.roadmap.get(projectId, { signal });
      if (isStale(reqId)) return;
      setRoadmap(rd);
      setRoadmapError(null);
    } catch (err: any) {
      if (isAbortError(err) || isStale(reqId)) return;
      if (isNotFoundError(err)) {
        setRoadmap(null);
        setRoadmapError(null);
      } else {
        setRoadmap(null);
        setRoadmapError(err?.message || 'Failed to load execution roadmap.');
      }
    } finally {
      if (!isStale(reqId)) {
        setRoadmapLoading(false);
      }
    }
  };

  const loadHistory = async (signal?: AbortSignal, reqId = currentRequestIdRef.current) => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const runs = await api.generations.listForProject(projectId, { signal });
      if (isStale(reqId)) return;
      setHistoryRuns(runs);
      setHistoryError(null);
    } catch (err: any) {
      if (isAbortError(err) || isStale(reqId)) return;
      setHistoryRuns([]);
      setHistoryError(err?.message || 'Failed to load generation audit history.');
    } finally {
      if (!isStale(reqId)) {
        setHistoryLoading(false);
      }
    }
  };

  useEffect(() => {
    // Requirement 4: Cancel inflight requests from the previously selected project
    if (activeAbortControllerRef.current) {
      activeAbortControllerRef.current.abort();
    }
    const controller = new AbortController();
    activeAbortControllerRef.current = controller;
    const reqId = ++currentRequestIdRef.current;

    // Immediately reset state so old project data does not persist into newly selected project
    setProject(null);
    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    setBmcBlueprint(null);
    setBmcVersions([]);
    setBmcLoading(true);
    setBmcError(null);
    setBmcVersionError(null);

    setTechBlueprint(null);
    setTechVersions([]);
    setTechLoading(true);
    setTechError(null);
    setTechVersionError(null);

    setValidatorReport(null);
    setValidatorVersions([]);
    setValidatorLoading(true);
    setValidatorError(null);
    setValidatorVersionError(null);

    setMarketResearch(null);
    setResearchVersions([]);
    setResearchLoading(true);
    setResearchError(null);
    setResearchVersionError(null);

    setRoadmap(null);
    setRoadmapLoading(true);
    setRoadmapError(null);

    setHistoryRuns([]);
    setHistoryLoading(true);
    setHistoryError(null);

    // Requirement 1: Concurrently load all independent modules
    loadProject(controller.signal, reqId);
    loadBmc(controller.signal, reqId);
    loadTech(controller.signal, reqId);
    loadValidator(controller.signal, reqId);
    loadMarketResearch(controller.signal, reqId);
    loadRoadmap(controller.signal, reqId);
    loadHistory(controller.signal, reqId);

    return () => {
      controller.abort();
    };
  }, [projectId]);

  // Generate BMC
  const handleGenerateBmc = async () => {
    setIsGeneratingBmc(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const blueprint = await api.bmc.generate(projectId);
      setBmcBlueprint(blueprint);
      loadBmcVersions();
      setSuccessMsg('Business Model Canvas generated successfully!');
      loadHistory();
    } catch (err: any) {
      setError(err.message || 'Failed to generate Business Model Canvas.');
    } finally {
      setIsGeneratingBmc(false);
    }
  };

  // Switch BMC Version
  const handleSelectBmcVersion = async (ver: number) => {
    try {
      const bp = await api.bmc.get(projectId, ver);
      setBmcBlueprint(bp);
    } catch (err: any) {
      setError(err.message || 'Could not load selected version.');
    }
  };

  // Generate Tech Stack
  const handleGenerateTech = async () => {
    setIsGeneratingTech(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const blueprint = await api.techStack.generate(projectId);
      setTechBlueprint(blueprint);
      loadTechVersions();
      setSuccessMsg('Technology Stack recommendation generated successfully!');
      loadHistory();
    } catch (err: any) {
      setError(err.message || 'Failed to generate Technology Stack.');
    } finally {
      setIsGeneratingTech(false);
    }
  };

  // Switch Tech Stack Version
  const handleSelectTechVersion = async (ver: number) => {
    try {
      const bp = await api.techStack.get(projectId, ver);
      setTechBlueprint(bp);
    } catch (err: any) {
      setError(err.message || 'Could not load selected version.');
    }
  };

  // Save edited BMC block
  const handleSaveBmcEdit = async () => {
    if (!editingBmcData) return;
    try {
      const updated = await api.bmc.update(projectId, editingBmcData);
      setBmcBlueprint(updated);
      setEditingBmcBlockKey(null);
      setSuccessMsg('Business Model Canvas changes saved.');
    } catch (err: any) {
      setError(err.message || 'Failed to save edits.');
    }
  };

  // Save edited Tech Stack item
  const handleSaveTechEdit = async () => {
    if (!editingTechData) return;
    try {
      const updated = await api.techStack.update(projectId, editingTechData);
      setTechBlueprint(updated);
      setEditingTechKey(null);
      setSuccessMsg('Technology Stack changes saved.');
    } catch (err: any) {
      setError(err.message || 'Failed to save edits.');
    }
  };

  // Export PDF
  const handleExportPdf = async () => {
    setIsExportingPdf(true);
    setError(null);
    try {
      const blob = await api.exports.downloadPdf(projectId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AI_Business_Architect_${(project?.name || 'Blueprint').replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setSuccessMsg('PDF blueprint exported successfully.');
    } catch (err: any) {
      setError(err.message || 'Failed to export PDF.');
    } finally {
      setIsExportingPdf(false);
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-slate-500 text-sm">Loading project workspace...</div>;
  }

  if (!project) {
    return (
      <div className="max-w-2xl mx-auto py-20 text-center space-y-4">
        <h2 className="text-xl font-bold text-slate-800">
          {error ? 'Failed to Load Project' : 'Project Not Found'}
        </h2>
        <p className="text-sm text-slate-500">
          {error || 'The requested business project could not be found or you lack permission.'}
        </p>
        <div className="flex justify-center gap-3">
          {error && (
            <Button variant="outline" onClick={() => loadProject()}>
              Retry
            </Button>
          )}
          <Button variant="primary" onClick={() => onNavigate('/dashboard')}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const bmcData = bmcBlueprint?.content_json as BusinessModelCanvasData | undefined;
  const techData = techBlueprint?.content_json as TechnologyStackData | undefined;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Back button & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('/dashboard')}
            className="p-2 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors"
            title="Back to Dashboard"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">
                {project.industry}
              </span>
              <Badge variant="slate" size="sm">
                {project.business_stage}
              </Badge>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">{project.name}</h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPdf}
            isLoading={isExportingPdf}
            leftIcon={<Download className="w-4 h-4" />}
          >
            Export PDF Blueprint
          </Button>
        </div>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {successMsg && <Alert type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-200 gap-2 sm:gap-4 overflow-x-auto pb-px">
        <button
          onClick={() => handleTabChange('bmc')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap px-1 ${
            activeTab === 'bmc'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Layers className="w-4 h-4" />
          Business Model Canvas
          {bmcBlueprint && (
            <Badge variant="emerald" size="sm">
              v{bmcBlueprint.version}
            </Badge>
          )}
        </button>

        <button
          onClick={() => handleTabChange('tech')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap px-1 ${
            activeTab === 'tech'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Cpu className="w-4 h-4" />
          Technology Stack
          {techBlueprint && (
            <Badge variant="sky" size="sm">
              v{techBlueprint.version}
            </Badge>
          )}
        </button>

        <button
          onClick={() => handleTabChange('validator')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap px-1 ${
            activeTab === 'validator'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Idea Validator
          {validatorReport && (
            <Badge variant="amber" size="sm">
              v{validatorReport.version}
            </Badge>
          )}
        </button>

        <button
          onClick={() => handleTabChange('research')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap px-1 ${
            activeTab === 'research'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Compass className="w-4 h-4" />
          Market Research / Competitor Analysis
          {marketResearch && (
            <Badge variant="sky" size="sm">
              v{marketResearch.version}
            </Badge>
          )}
        </button>

        <button
          onClick={() => handleTabChange('roadmap')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap px-1 ${
            activeTab === 'roadmap'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Milestone className="w-4 h-4" />
          Execution Roadmap
          {roadmap && (
            <Badge variant="indigo" size="sm">
              {roadmap.completed_tasks}/{roadmap.total_tasks}
            </Badge>
          )}
        </button>

        <button
          onClick={() => handleTabChange('copilot')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap px-1 ${
            activeTab === 'copilot'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <Bot className="w-4 h-4" />
          Blueprint Copilot
        </button>

        <button
          onClick={() => handleTabChange('overview')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap px-1 ${
            activeTab === 'overview'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          Overview
        </button>

        <button
          onClick={() => handleTabChange('history')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-colors border-b-2 flex items-center gap-1.5 whitespace-nowrap px-1 ${
            activeTab === 'history'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <History className="w-4 h-4" />
          History ({historyRuns.length})
        </button>
      </div>

      {/* TAB 1: BUSINESS MODEL CANVAS */}
      {activeTab === 'bmc' && (
        <div className="space-y-6">
          {bmcLoading ? (
            <ModuleLoadingCard message="Loading Business Model Canvas..." />
          ) : bmcError && !bmcBlueprint ? (
            <ModuleErrorCard
              title="Failed to Load Business Model Canvas"
              message={bmcError}
              onRetry={() => loadBmc()}
              moduleName="Business Model Canvas"
            />
          ) : !bmcBlueprint || !bmcData ? (
            <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                <Layers className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Generate Business Model Canvas</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                  Execute the 9-block venture analysis using the configured AI provider.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={handleGenerateBmc}
                isLoading={isGeneratingBmc}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                Generate Canvas
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Requirement 3: Separate Version History Error Banner without clearing report */}
              {bmcVersionError && (
                <div
                  role="alert"
                  className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 gap-3"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" aria-hidden="true" />
                    <span>Unable to load version history: {bmcVersionError}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadBmcVersions()}
                    aria-label="Retry loading BMC versions"
                  >
                    Retry History
                  </Button>
                </div>
              )}

              {/* Controls bar: Versions and Regenerate */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-slate-600">Active Version:</span>
                  <select
                    value={bmcBlueprint.version}
                    onChange={(e) => handleSelectBmcVersion(parseInt(e.target.value))}
                    className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 font-medium text-slate-800"
                    aria-label="Select BMC version"
                  >
                    {bmcVersions.map((v) => (
                      <option key={v.version} value={v.version}>
                        Version {v.version} ({new Date(v.updated_at).toLocaleTimeString()})
                      </option>
                    ))}
                  </select>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateBmc}
                  isLoading={isGeneratingBmc}
                  leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                >
                  Regenerate Canvas (v{bmcBlueprint.version + 1})
                </Button>
              </div>

              {/* Strategic Focus Banner */}
              <div className="p-5 bg-gradient-to-r from-indigo-50 via-white to-slate-50 rounded-xl border border-indigo-200 space-y-1.5">
                <div className="flex items-center gap-2">
                  <Badge variant="indigo">Core Strategy</Badge>
                  <span className="text-xs font-bold text-slate-900">{bmcData.key_strategic_focus}</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{bmcData.overview}</p>
              </div>

              {/* 9-Block Grid */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5">
                {/* 8. Key Partnerships */}
                <div className="md:col-span-1">
                  <CanvasBlockCard
                    block={bmcData.key_partnerships}
                    blockKey="key_partnerships"
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('key_partnerships');
                    }}
                  />
                </div>

                {/* 7. Key Activities & 6. Key Resources */}
                <div className="md:col-span-1 space-y-3.5">
                  <CanvasBlockCard
                    block={bmcData.key_activities}
                    blockKey="key_activities"
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('key_activities');
                    }}
                  />
                  <CanvasBlockCard
                    block={bmcData.key_resources}
                    blockKey="key_resources"
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('key_resources');
                    }}
                  />
                </div>

                {/* 2. Value Propositions */}
                <div className="md:col-span-1">
                  <CanvasBlockCard
                    block={bmcData.value_propositions}
                    blockKey="value_propositions"
                    highlight
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('value_propositions');
                    }}
                  />
                </div>

                {/* 4. Customer Relationships & 3. Channels */}
                <div className="md:col-span-1 space-y-3.5">
                  <CanvasBlockCard
                    block={bmcData.customer_relationships}
                    blockKey="customer_relationships"
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('customer_relationships');
                    }}
                  />
                  <CanvasBlockCard
                    block={bmcData.channels}
                    blockKey="channels"
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('channels');
                    }}
                  />
                </div>

                {/* 1. Customer Segments */}
                <div className="md:col-span-1">
                  <CanvasBlockCard
                    block={bmcData.customer_segments}
                    blockKey="customer_segments"
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('customer_segments');
                    }}
                  />
                </div>

                {/* 9. Cost Structure & 5. Revenue Streams */}
                <div className="md:col-span-2">
                  <CanvasBlockCard
                    block={bmcData.cost_structure}
                    blockKey="cost_structure"
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('cost_structure');
                    }}
                  />
                </div>

                <div className="md:col-span-3">
                  <CanvasBlockCard
                    block={bmcData.revenue_streams}
                    blockKey="revenue_streams"
                    onEdit={() => {
                      setEditingBmcData(JSON.parse(JSON.stringify(bmcData)));
                      setEditingBmcBlockKey('revenue_streams');
                    }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: TECHNOLOGY STACK */}
      {activeTab === 'tech' && (
        <div className="space-y-6">
          {techLoading ? (
            <ModuleLoadingCard message="Loading Technology Stack..." />
          ) : techError && !techBlueprint ? (
            <ModuleErrorCard
              title="Failed to Load Technology Stack"
              message={techError}
              onRetry={() => loadTech()}
              moduleName="Technology Stack"
            />
          ) : !techBlueprint || !techData ? (
            <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8">
              <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
                <Cpu className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Generate Technology Stack</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
                  Architect pragmatic recommendations for frontend, backend, database, hosting, and APIs.
                </p>
              </div>
              <Button
                variant="primary"
                onClick={handleGenerateTech}
                isLoading={isGeneratingTech}
                leftIcon={<Sparkles className="w-4 h-4" />}
              >
                Generate Tech Stack
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Requirement 3: Separate Version History Error Banner without clearing report */}
              {techVersionError && (
                <div
                  role="alert"
                  className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 gap-3"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" aria-hidden="true" />
                    <span>Unable to load version history: {techVersionError}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadTechVersions()}
                    aria-label="Retry loading tech stack versions"
                  >
                    Retry History
                  </Button>
                </div>
              )}

              {/* Controls bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-slate-600">Active Version:</span>
                  <select
                    value={techBlueprint.version}
                    onChange={(e) => handleSelectTechVersion(parseInt(e.target.value))}
                    className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 font-medium text-slate-800"
                    aria-label="Select Technology Stack version"
                  >
                    {techVersions.map((v) => (
                      <option key={v.version} value={v.version}>
                        Version {v.version} ({new Date(v.updated_at).toLocaleTimeString()})
                      </option>
                    ))}
                  </select>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateTech}
                  isLoading={isGeneratingTech}
                  leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                >
                  Regenerate Stack (v{techBlueprint.version + 1})
                </Button>
              </div>

              {/* Architecture Summary Banner */}
              <div className="p-5 bg-gradient-to-r from-sky-50 via-white to-slate-50 rounded-xl border border-sky-200 space-y-2">
                <div className="flex items-center justify-between">
                  <Badge variant="sky">Architecture Philosophy</Badge>
                  <span className="text-xs font-bold text-slate-800">
                    Est. Monthly Spend: {techData.estimated_monthly_infrastructure_total}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{techData.architecture_summary}</p>
              </div>

              {/* 5 Category Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TechItemCard
                  item={techData.frontend}
                  onEdit={() => {
                    setEditingTechData(JSON.parse(JSON.stringify(techData)));
                    setEditingTechKey('frontend');
                  }}
                />
                <TechItemCard
                  item={techData.backend}
                  onEdit={() => {
                    setEditingTechData(JSON.parse(JSON.stringify(techData)));
                    setEditingTechKey('backend');
                  }}
                />
                <TechItemCard
                  item={techData.database}
                  onEdit={() => {
                    setEditingTechData(JSON.parse(JSON.stringify(techData)));
                    setEditingTechKey('database');
                  }}
                />
                <TechItemCard
                  item={techData.hosting_infrastructure}
                  onEdit={() => {
                    setEditingTechData(JSON.parse(JSON.stringify(techData)));
                    setEditingTechKey('hosting_infrastructure');
                  }}
                />
                <div className="md:col-span-2">
                  <TechItemCard
                    item={techData.third_party_services}
                    onEdit={() => {
                      setEditingTechData(JSON.parse(JSON.stringify(techData)));
                      setEditingTechKey('third_party_services');
                    }}
                  />
                </div>
              </div>

              {/* Scalability & Security */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                <Card>
                  <CardContent className="p-6 space-y-3">
                    <h4 className="text-sm font-bold text-slate-900">Scalability Milestones</h4>
                    <ul className="space-y-1.5 text-xs text-slate-600">
                      {techData.scalability_considerations.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-sky-500 shrink-0 mt-0.5" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6 space-y-3">
                    <h4 className="text-sm font-bold text-slate-900">Security Safeguards</h4>
                    <ul className="space-y-1.5 text-xs text-slate-600">
                      {techData.security_considerations.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: PROJECT OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Business Concept & Value Proposition</CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-4 text-xs text-slate-700 leading-relaxed">
                <p className="whitespace-pre-wrap">{project.idea_description}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Target Market & Audience</CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-3 text-xs text-slate-700">
                <div>
                  <span className="font-semibold text-slate-900 block">Target Market Geography</span>
                  <span className="text-slate-600">{project.target_market || 'General'}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-900 block">Target Customer Profile</span>
                  <span className="text-slate-600">{project.target_audience || 'Broad'}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Operating Constraints</CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-3 text-xs text-slate-700">
                <div>
                  <span className="font-semibold text-slate-900 block">Allocated Budget</span>
                  <span className="text-slate-600">
                    {project.budget_amount ? `${project.budget_amount} ${project.budget_currency}` : 'Bootstrapped'}
                  </span>
                </div>
                <div>
                  <span className="font-semibold text-slate-900 block">Team Composition</span>
                  <span className="text-slate-600">{project.team_size || 'Solo'}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-900 block">Technical Preferences</span>
                  <span className="text-slate-600">{project.technical_preferences || 'None specified'}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-900 block">Compliance / Limits</span>
                  <span className="text-slate-600">{project.constraints || 'None specified'}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 4: AUDIT HISTORY */}
      {activeTab === 'history' && (
        <Card>
          <CardHeader>
            <CardTitle>AI Generation Run Audit Log</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {historyLoading ? (
              <p className="text-xs text-slate-500 py-6 text-center">Loading generation history...</p>
            ) : historyError ? (
              <div role="alert" className="text-center py-6 space-y-2">
                <p className="text-xs text-rose-600">{historyError}</p>
                <Button variant="outline" size="sm" onClick={() => loadHistory()}>
                  Retry History
                </Button>
              </div>
            ) : historyRuns.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No generation runs recorded yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="p-3">Module</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Model</th>
                      <th className="p-3">Latency</th>
                      <th className="p-3">Tokens (In / Out)</th>
                      <th className="p-3">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {historyRuns.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/60">
                        <td className="p-3 font-semibold text-slate-900">
                          {r.module_type === 'business_model' ? 'Business Model' : 'Tech Stack'}
                        </td>
                        <td className="p-3">
                          <Badge
                            variant={r.status === 'success' ? 'emerald' : r.status === 'failed' ? 'rose' : 'amber'}
                            size="sm"
                          >
                            {r.status}
                          </Badge>
                        </td>
                        <td className="p-3 text-slate-600">{r.model}</td>
                        <td className="p-3 text-slate-600">{r.latency_ms ? `${r.latency_ms} ms` : '—'}</td>
                        <td className="p-3 text-slate-600">
                          {r.input_token_count && r.output_token_count
                            ? `${r.input_token_count} / ${r.output_token_count}`
                            : '—'}
                        </td>
                        <td className="p-3 text-slate-500">{new Date(r.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB: IDEA VALIDATOR */}
      {activeTab === 'validator' && (
        <ErrorBoundary fallbackTitle="Idea Validator Module Error" fallbackMessage="An error occurred while displaying the Idea Validator module.">
          <IdeaValidatorView
            projectId={projectId}
            report={validatorReport}
            versions={validatorVersions}
            isLoading={validatorLoading}
            error={validatorError}
            versionError={validatorVersionError}
            onRetry={() => loadValidator()}
            onRetryVersions={() => loadValidatorVersions()}
            onReportUpdated={() => {
              loadValidatorVersions();
              loadHistory();
            }}
          />
        </ErrorBoundary>
      )}

      {/* TAB: MARKET RESEARCH */}
      {activeTab === 'research' && (
        <ErrorBoundary fallbackTitle="Market Research Module Error" fallbackMessage="An error occurred while displaying the Market Research & Competitor Analysis module.">
          {researchError && !marketResearch ? (
            <ModuleErrorCard
              title="Failed to Load Market Research"
              message={researchError}
              onRetry={() => loadMarketResearch()}
              moduleName="Market Research"
            />
          ) : (
            <div className="space-y-6">
              {researchVersionError && (
                <div
                  role="alert"
                  className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 gap-3"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" aria-hidden="true" />
                    <span>Unable to load version history: {researchVersionError}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadMarketResearchVersions()}
                    aria-label="Retry loading market research versions"
                  >
                    Retry History
                  </Button>
                </div>
              )}
              <MarketResearchView
                projectId={projectId}
                research={marketResearch}
                versions={researchVersions}
                isLoading={researchLoading}
                onResearchUpdated={() => {
                  loadMarketResearchVersions();
                  loadHistory();
                }}
              />
            </div>
          )}
        </ErrorBoundary>
      )}

      {/* TAB: EXECUTION ROADMAP */}
      {activeTab === 'roadmap' && (
        <ErrorBoundary fallbackTitle="Execution Roadmap Module Error" fallbackMessage="An error occurred while displaying the Execution Roadmap module.">
          {roadmapLoading ? (
            <ModuleLoadingCard message="Loading Execution Roadmap..." />
          ) : roadmapError && !roadmap ? (
            <ModuleErrorCard
              title="Failed to Load Execution Roadmap"
              message={roadmapError}
              onRetry={() => loadRoadmap()}
              moduleName="Execution Roadmap"
            />
          ) : (
            <RoadmapView
              projectId={projectId}
              roadmap={roadmap}
              onRoadmapUpdated={() => {
                loadRoadmap();
              }}
            />
          )}
        </ErrorBoundary>
      )}

      {/* TAB: BLUEPRINT COPILOT */}
      {activeTab === 'copilot' && (
        <ErrorBoundary fallbackTitle="Blueprint Copilot Module Error" fallbackMessage="An error occurred while displaying the Blueprint Copilot module.">
          <CopilotWorkspaceView
            projectId={projectId}
            onBlueprintModified={() => {
              loadBmc();
              loadTech();
              loadHistory();
            }}
          />
        </ErrorBoundary>
      )}

      {/* EDIT BMC BLOCK MODAL */}
      <Modal
        isOpen={Boolean(editingBmcBlockKey && editingBmcData)}
        onClose={() => setEditingBmcBlockKey(null)}
        title={`Edit Canvas Block: ${(editingBmcData as any)?.[editingBmcBlockKey || '']?.block_title || ''}`}
        maxWidth="lg"
      >
        {editingBmcBlockKey && editingBmcData && (
          <div className="space-y-4">
            <Textarea
              label="Summary"
              value={(editingBmcData as any)[editingBmcBlockKey].summary}
              onChange={(e) => {
                const copy = { ...editingBmcData };
                (copy as any)[editingBmcBlockKey].summary = e.target.value;
                setEditingBmcData(copy);
              }}
              rows={3}
            />

            <Textarea
              label="Recommendations (One per line)"
              value={(editingBmcData as any)[editingBmcBlockKey].recommendations.join('\n')}
              onChange={(e) => {
                const copy = { ...editingBmcData };
                (copy as any)[editingBmcBlockKey].recommendations = e.target.value.split('\n').filter(Boolean);
                setEditingBmcData(copy);
              }}
              rows={4}
            />

            <Textarea
              label="Rationale"
              value={(editingBmcData as any)[editingBmcBlockKey].rationale}
              onChange={(e) => {
                const copy = { ...editingBmcData };
                (copy as any)[editingBmcBlockKey].rationale = e.target.value;
                setEditingBmcData(copy);
              }}
              rows={2}
            />

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
              <Button variant="outline" onClick={() => setEditingBmcBlockKey(null)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSaveBmcEdit} leftIcon={<Save className="w-4 h-4" />}>
                Save Changes
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* EDIT TECH ITEM MODAL */}
      <Modal
        isOpen={Boolean(editingTechKey && editingTechData)}
        onClose={() => setEditingTechKey(null)}
        title={`Edit ${(editingTechData as any)?.[editingTechKey || '']?.category || ''}`}
        maxWidth="lg"
      >
        {editingTechKey && editingTechData && (
          <div className="space-y-4">
            <Input
              label="Recommended Technology"
              value={(editingTechData as any)[editingTechKey].technology}
              onChange={(e) => {
                const copy = { ...editingTechData };
                (copy as any)[editingTechKey].technology = e.target.value;
                setEditingTechData(copy);
              }}
            />

            <Textarea
              label="Purpose / Role"
              value={(editingTechData as any)[editingTechKey].purpose}
              onChange={(e) => {
                const copy = { ...editingTechData };
                (copy as any)[editingTechKey].purpose = e.target.value;
                setEditingTechData(copy);
              }}
              rows={2}
            />

            <Textarea
              label="Rationale"
              value={(editingTechData as any)[editingTechKey].reason}
              onChange={(e) => {
                const copy = { ...editingTechData };
                (copy as any)[editingTechKey].reason = e.target.value;
                setEditingTechData(copy);
              }}
              rows={2}
            />

            <Input
              label="Estimated Cost Tier"
              value={(editingTechData as any)[editingTechKey].estimated_cost}
              onChange={(e) => {
                const copy = { ...editingTechData };
                (copy as any)[editingTechKey].estimated_cost = e.target.value;
                setEditingTechData(copy);
              }}
            />

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
              <Button variant="outline" onClick={() => setEditingTechKey(null)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSaveTechEdit} leftIcon={<Save className="w-4 h-4" />}>
                Save Changes
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

// Canvas Block Card Subcomponent
const CanvasBlockCard: React.FC<{
  block: BMCBlock;
  blockKey: string;
  highlight?: boolean;
  onEdit: () => void;
}> = ({ block, highlight = false, onEdit }) => {
  return (
    <div
      className={`p-4 rounded-xl border flex flex-col justify-between transition-all ${
        highlight
          ? 'bg-indigo-50/70 border-indigo-200'
          : 'bg-white border-slate-200/90 hover:border-slate-300'
      }`}
    >
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-slate-900">{block.block_title}</h4>
          <button
            onClick={onEdit}
            className="text-slate-400 hover:text-indigo-600 p-1 rounded-md hover:bg-slate-100 transition-colors"
            title="Edit block"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
        </div>

        <p className="text-[11px] text-slate-600 leading-snug line-clamp-3">{block.summary}</p>

        <div className="space-y-1 pt-1">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Recommendations:</p>
          <ul className="text-[11px] text-slate-700 space-y-1">
            {block.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-1.5 leading-snug">
                <span className="text-indigo-500 font-bold">•</span>
                <span className="line-clamp-2">{r}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {block.validation_experiments && block.validation_experiments.length > 0 && (
        <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-slate-500 italic">
          Test: {block.validation_experiments[0]}
        </div>
      )}
    </div>
  );
};

// Technology Item Card Subcomponent
const TechItemCard: React.FC<{
  item: TechRecommendationItem;
  onEdit: () => void;
}> = ({ item, onEdit }) => {
  return (
    <Card hover>
      <CardContent className="p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-sky-600">{item.category}</span>
            <h4 className="text-base font-bold text-slate-900 mt-0.5">{item.technology}</h4>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="sky" size="sm">
              {item.estimated_cost}
            </Badge>
            <button
              onClick={onEdit}
              className="text-slate-400 hover:text-sky-600 p-1 rounded-md hover:bg-slate-100 transition-colors"
              title="Edit recommendation"
            >
              <Edit2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          <strong>Purpose:</strong> {item.purpose}
        </p>

        <p className="text-xs text-slate-600 leading-relaxed">
          <strong>Rationale:</strong> {item.reason}
        </p>

        {item.alternatives && item.alternatives.length > 0 && (
          <div className="text-xs text-slate-500">
            <strong>Alternatives Considered:</strong> {item.alternatives.join(', ')}
          </div>
        )}

        {item.tradeoffs && item.tradeoffs.length > 0 && (
          <div className="text-xs text-amber-900 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
            <strong>Trade-offs:</strong> {item.tradeoffs.join(' • ')}
          </div>
        )}

        <p className="text-[10px] text-slate-400 italic">{item.verification_notes}</p>
      </CardContent>
    </Card>
  );
};
