import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Cpu,
  Download,
  FolderPlus,
  Layers,
  Plus,
  Search,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Project } from '../types';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Alert } from '../components/ui/Alert';

interface DashboardPageProps {
  onNavigate: (path: string, projectId?: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Deletion modal state
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.projects.list({ search: search.trim() || undefined });
      setProjects(res.items || []);
      setTotalCount(res.pagination.total_count || 0);
    } catch (err: any) {
      setError(err.message || 'Failed to load projects.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [search]);

  const handleDelete = async () => {
    if (!projectToDelete) return;
    setIsDeleting(true);
    try {
      await api.projects.delete(projectToDelete.id);
      setProjectToDelete(null);
      await fetchProjects();
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
    } catch (err: any) {
      setError('Could not export PDF. Please ensure at least one module has been generated.');
    }
  };

  // Real statistics calculated from stored projects
  const bmcCount = projects.filter((p) => p.has_business_model).length;
  const techCount = projects.filter((p) => p.has_technology_stack).length;

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

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}

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

      {/* Search and Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Input
            placeholder="Search projects by name, idea, or industry..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="text-center py-20 text-slate-500 text-sm">Loading projects...</div>
      ) : projects.length === 0 ? (
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
          <Button variant="primary" onClick={() => onNavigate('/projects/new')} leftIcon={<Plus className="w-4 h-4" />}>
            Create your first project
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card
              key={project.id}
              hover
              onClick={() => onNavigate(`/projects/${project.id}`, project.id)}
              className="cursor-pointer flex flex-col justify-between"
            >
              <CardContent className="p-6 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">
                      {project.industry}
                    </span>
                    <h3 className="text-base font-bold text-slate-900 mt-0.5 line-clamp-1">{project.name}</h3>
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
                    onClick={(e) => handleDownloadPdf(e, project)}
                    className="p-1.5 text-slate-500 hover:text-indigo-600 rounded-md hover:bg-slate-200 transition-colors"
                    title="Export PDF Blueprint"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setProjectToDelete(project);
                    }}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md hover:bg-rose-50 transition-colors"
                    title="Delete Project"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
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
