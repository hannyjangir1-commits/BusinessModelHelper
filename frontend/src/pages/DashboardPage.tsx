import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Download,
  FolderPlus,
  Layers,
  Plus,
  RotateCcw,
  Search,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { PaginationMetadata, Project } from '../types';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';

interface DashboardPageProps {
  onNavigate: (path: string, projectId?: string) => void;
}

const DEFAULT_PAGE_SIZE = 12;

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [pagination, setPagination] = useState<PaginationMetadata | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filter state
  const [search, setSearch] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [industryFilter, setIndustryFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);

  // Deletion modal state
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Concurrency & Debounce guards
  const activeAbortControllerRef = useRef<AbortController | null>(null);
  const currentRequestIdRef = useRef<number>(0);

  // Debounce search input by 300ms and reset page to 1
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Handle industry filter change and reset page to 1
  const handleIndustryChange = (val: string) => {
    setIndustryFilter(val);
    setPage(1);
  };

  // Reset all filters and search term
  const handleClearFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setIndustryFilter('');
    setPage(1);
  };

  // Core fetch logic with AbortController and request-sequence generation guard
  const fetchProjects = useCallback(
    async (targetPage: number, targetSearch: string, targetIndustry: string) => {
      // 1. Cancel previous in-flight request
      if (activeAbortControllerRef.current) {
        activeAbortControllerRef.current.abort();
      }
      const controller = new AbortController();
      activeAbortControllerRef.current = controller;

      // 2. Monotonically increment request ID to ignore superseded responses
      const requestId = ++currentRequestIdRef.current;

      setLoading(true);
      setError(null);

      try {
        const res = await api.projects.list(
          {
            page: targetPage,
            pageSize: DEFAULT_PAGE_SIZE,
            search: targetSearch.trim() || undefined,
            industry: targetIndustry.trim() || undefined,
          },
          { signal: controller.signal }
        );

        // Guard: Drop response if a newer request was dispatched
        if (requestId !== currentRequestIdRef.current) {
          return;
        }

        setProjects(res.items || []);
        setPagination(res.pagination || null);
        setTotalCount(res.pagination?.total_count ?? (res.items?.length || 0));
      } catch (err: any) {
        // Guard: Ignore if superseded or aborted
        if (requestId !== currentRequestIdRef.current) {
          return;
        }
        if (err.name === 'AbortError' || err.message?.includes('aborted') || controller.signal.aborted) {
          return;
        }

        setError(err.message || 'Failed to load projects. Please try again.');
      } finally {
        if (requestId === currentRequestIdRef.current) {
          setLoading(false);
        }
      }
    },
    []
  );

  // Fetch projects whenever page, debouncedSearch, or industryFilter change
  useEffect(() => {
    fetchProjects(page, debouncedSearch, industryFilter);
  }, [page, debouncedSearch, industryFilter, fetchProjects]);

  // Clean up any pending network request on unmount
  useEffect(() => {
    return () => {
      if (activeAbortControllerRef.current) {
        activeAbortControllerRef.current.abort();
      }
    };
  }, []);

  const handleRetry = () => {
    fetchProjects(page, debouncedSearch, industryFilter);
  };

  const handleDelete = async () => {
    if (!projectToDelete) return;
    setIsDeleting(true);
    try {
      await api.projects.delete(projectToDelete.id);
      setProjectToDelete(null);

      // Handle pagination boundary if last project on current page was deleted
      const nextPage = projects.length === 1 && page > 1 ? page - 1 : page;
      if (nextPage !== page) {
        setPage(nextPage);
      } else {
        await fetchProjects(page, debouncedSearch, industryFilter);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete project.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDownloadPdf = async (e: React.MouseEvent, project: Project) => {
    e.stopPropagation();
    try {
      const blob = await api.exports.downloadPdf(project.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AI_Business_Architect_${project.name.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError('Could not export PDF. Please ensure at least one module has been generated.');
    }
  };

  // Real statistics calculated from stored projects
  const bmcCount = projects.filter((p) => p.has_business_model).length;
  const techCount = projects.filter((p) => p.has_technology_stack).length;

  const isFiltered = Boolean(debouncedSearch.trim() || industryFilter.trim());

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Welcome & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Welcome back, {user?.display_name || user?.username}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Manage your venture projects, generated canvases, and architectural blueprints.
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => onNavigate('/projects/new')}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Create Project
        </Button>
      </div>

      {/* Top Error Alert Banner if an error occurred */}
      {error && (
        <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRetry} leftIcon={<RotateCcw className="w-3.5 h-3.5" />}>
              Retry
            </Button>
            <button
              onClick={() => setError(null)}
              className="text-rose-500 hover:text-rose-800 p-1"
              aria-label="Dismiss error"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <FolderPlus className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Projects</p>
              <p className="text-2xl font-extrabold text-slate-900 mt-0.5">{totalCount}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Business Canvases</p>
              <p className="text-2xl font-extrabold text-slate-900 mt-0.5">{bmcCount}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Tech Stacks</p>
              <p className="text-2xl font-extrabold text-slate-900 mt-0.5">{techCount}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Industry Filters Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Input
            placeholder="Search projects by name, idea, or industry..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            aria-label="Search projects"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        <div className="w-full sm:w-48">
          <select
            aria-label="Filter by industry"
            value={industryFilter}
            onChange={(e) => handleIndustryChange(e.target.value)}
            className="w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
          >
            <option value="">All Industries</option>
            <option value="SaaS">SaaS / B2B</option>
            <option value="Fintech">Fintech</option>
            <option value="HealthTech">HealthTech</option>
            <option value="E-Commerce">E-Commerce</option>
            <option value="EdTech">EdTech</option>
            <option value="CleanTech">CleanTech</option>
            <option value="AI">AI / DeepTech</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {(Boolean(search) || Boolean(industryFilter)) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            leftIcon={<X className="w-3.5 h-3.5" />}
            className="text-xs text-slate-500 hover:text-slate-800"
          >
            Reset Filters
          </Button>
        )}
      </div>

      {/* Content Area: Loading, Error, Empty, No-Results, or Grid */}
      {loading ? (
        /* State 1: Accessible Loading Skeleton Grid */
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          role="status"
          aria-label="Loading projects..."
        >
          {Array.from({ length: 6 }).map((_, idx) => (
            <Card key={idx} className="animate-pulse flex flex-col justify-between">
              <CardContent className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="h-4 w-20 bg-slate-200 rounded" />
                  <div className="h-4 w-16 bg-slate-200 rounded-full" />
                </div>
                <div className="h-5 w-3/4 bg-slate-200 rounded" />
                <div className="space-y-2">
                  <div className="h-3 w-full bg-slate-200 rounded" />
                  <div className="h-3 w-5/6 bg-slate-200 rounded" />
                </div>
                <div className="flex gap-2 pt-2">
                  <div className="h-5 w-16 bg-slate-200 rounded" />
                  <div className="h-5 w-16 bg-slate-200 rounded" />
                </div>
              </CardContent>
              <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between rounded-b-xl">
                <div className="h-3 w-24 bg-slate-200 rounded" />
                <div className="h-4 w-12 bg-slate-200 rounded" />
              </div>
            </Card>
          ))}
          <span className="sr-only">Loading projects...</span>
        </div>
      ) : error && projects.length === 0 ? (
        /* State 2: Error & Retry State when no cached projects */
        <div className="bg-white border border-rose-200 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8 shadow-sm">
          <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Failed to Load Projects</h3>
            <p className="text-xs text-slate-600 mt-1 max-w-xs mx-auto">{error}</p>
          </div>
          <Button variant="primary" onClick={handleRetry} leftIcon={<RotateCcw className="w-4 h-4" />}>
            Try Again
          </Button>
        </div>
      ) : projects.length === 0 && isFiltered ? (
        /* State 3: No-Results Filtered State */
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-500 flex items-center justify-center mx-auto">
            <Search className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">No Matching Projects</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
              No projects matched your search or industry filter. Try adjusting your query or resetting filters.
            </p>
          </div>
          <Button variant="outline" onClick={handleClearFilters} leftIcon={<X className="w-4 h-4" />}>
            Clear Search & Filters
          </Button>
        </div>
      ) : projects.length === 0 ? (
        /* State 4: Genuinely Empty Account State */
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">No Business Projects Yet</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
              Transform your raw startup idea into an actionable blueprint with our guided wizard.
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => onNavigate('/projects/new')}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Create your first project
          </Button>
        </div>
      ) : (
        /* State 5: Projects Grid + Pagination Controls */
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <article
                key={project.id}
                className="bg-white border border-slate-200/90 rounded-xl shadow-xs hover:shadow-md hover:border-slate-300 transition-all flex flex-col justify-between"
              >
                <CardContent className="p-6 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">
                        {project.industry}
                      </span>
                      <h3 className="text-base font-bold text-slate-900 mt-0.5 line-clamp-1">
                        <button
                          type="button"
                          onClick={() => onNavigate(`/projects/${project.id}`, project.id)}
                          className="text-left font-bold text-slate-900 hover:text-indigo-600 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 rounded-md transition-colors block w-full cursor-pointer"
                          aria-label={`Open project: ${project.name}`}
                        >
                          {project.name}
                        </button>
                      </h3>
                    </div>
                    <Badge variant="slate" size="sm">
                      {project.business_stage}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{project.idea_description}</p>

                  <div className="pt-2 flex flex-wrap items-center gap-1.5">
                    {project.has_business_model ? (
                      <Badge variant="emerald" size="sm">
                        BMC v{project.latest_bmc_version || 1}
                      </Badge>
                    ) : (
                      <Badge variant="slate" size="sm">
                        No BMC
                      </Badge>
                    )}

                    {project.has_technology_stack ? (
                      <Badge variant="sky" size="sm">
                        Stack v{project.latest_tech_version || 1}
                      </Badge>
                    ) : (
                      <Badge variant="slate" size="sm">
                        No Stack
                      </Badge>
                    )}

                    {project.has_validator_report && (
                      <Badge variant="indigo" size="sm">
                        Validator
                      </Badge>
                    )}

                    {project.has_market_research && (
                      <Badge variant="amber" size="sm">
                        Research
                      </Badge>
                    )}

                    {project.has_roadmap && (
                      <Badge variant="indigo" size="sm">
                        Roadmap
                      </Badge>
                    )}
                  </div>
                </CardContent>

                <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 rounded-b-xl">
                  <span>Updated {new Date(project.updated_at).toLocaleDateString()}</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={(e) => handleDownloadPdf(e, project)}
                      className="p-2 min-w-[36px] min-h-[36px] flex items-center justify-center text-slate-600 hover:text-indigo-600 rounded-md hover:bg-slate-200 transition-colors focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                      title="Export PDF Blueprint"
                      aria-label={`Export PDF for ${project.name}`}
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setProjectToDelete(project)}
                      className="p-2 min-w-[36px] min-h-[36px] flex items-center justify-center text-slate-500 hover:text-rose-600 rounded-md hover:bg-rose-50 transition-colors focus:outline-hidden focus:ring-2 focus:ring-rose-500"
                      title="Delete Project"
                      aria-label={`Delete project ${project.name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Real Pagination Controls */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-slate-200">
              <p className="text-xs sm:text-sm text-slate-500">
                Showing <span className="font-semibold text-slate-800">{(page - 1) * pagination.page_size + 1}</span>{' '}
                to{' '}
                <span className="font-semibold text-slate-800">
                  {Math.min(page * pagination.page_size, pagination.total_count)}
                </span>{' '}
                of <span className="font-semibold text-slate-800">{pagination.total_count}</span> projects
              </p>

              <div className="flex items-center gap-1.5" role="navigation" aria-label="Pagination">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!pagination.has_prev || page <= 1 || loading}
                  leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
                  aria-label="Previous page"
                >
                  Previous
                </Button>

                {/* Page number buttons */}
                <div className="flex items-center gap-1 mx-1">
                  {Array.from({ length: pagination.total_pages }, (_, i) => i + 1).map((pageNum) => {
                    if (
                      pagination.total_pages > 7 &&
                      pageNum !== 1 &&
                      pageNum !== pagination.total_pages &&
                      Math.abs(pageNum - page) > 1
                    ) {
                      if (pageNum === 2 && page > 3) {
                        return (
                          <span key="ellipsis-start" className="px-1 text-slate-400 text-xs">
                            …
                          </span>
                        );
                      }
                      if (pageNum === pagination.total_pages - 1 && page < pagination.total_pages - 2) {
                        return (
                          <span key="ellipsis-end" className="px-1 text-slate-400 text-xs">
                            …
                          </span>
                        );
                      }
                      return null;
                    }

                    const isActive = pageNum === page;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        disabled={loading}
                        aria-current={isActive ? 'page' : undefined}
                        className={`w-8 h-8 rounded-lg text-xs font-semibold transition-colors ${
                          isActive
                            ? 'bg-indigo-600 text-white shadow-sm'
                            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                  disabled={!pagination.has_next || page >= pagination.total_pages || loading}
                  rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                  aria-label="Next page"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Confirmation Modal for Project Deletion */}
      <Modal
        isOpen={Boolean(projectToDelete)}
        onClose={() => setProjectToDelete(null)}
        title="Delete Business Project?"
        description="This action will permanently delete the project and all associated blueprints and generation runs."
        maxWidth="md"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-700">
            Are you sure you want to delete <strong>{projectToDelete?.name}</strong>? This cannot be undone.
          </p>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button variant="outline" onClick={() => setProjectToDelete(null)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} isLoading={isDeleting}>
              Delete Project
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
