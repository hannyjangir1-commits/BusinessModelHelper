import React, { useState } from 'react';
import {
  Calendar,
  Milestone,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { api } from '../../services/api';
import { RoadmapResponse } from '../../types';
import { Button } from '../ui/Button';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Modal } from '../ui/Modal';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { Alert } from '../ui/Alert';

interface RoadmapViewProps {
  projectId: string;
  roadmap: RoadmapResponse | null;
  onRoadmapUpdated: () => void;
}

export const RoadmapView: React.FC<RoadmapViewProps> = ({
  projectId,
  roadmap,
  onRoadmapUpdated,
}) => {
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [selectedMilestone, setSelectedMilestone] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // New Task Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [newTaskTitle, setNewTaskTitle] = useState<string>('');
  const [newTaskDesc, setNewTaskDesc] = useState<string>('');
  const [newTaskMilestone, setNewTaskMilestone] = useState<string>('30-day');
  const [newTaskPriority, setNewTaskPriority] = useState<string>('medium');
  const [newTaskDeliverable, setNewTaskDeliverable] = useState<string>('');
  const [isSubmittingTask, setIsSubmittingTask] = useState<boolean>(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setSuccess(null);
    try {
      await api.roadmap.generate(projectId);
      setSuccess('Execution roadmap generated with validated milestone dependencies.');
      onRoadmapUpdated();
    } catch (err: any) {
      setError(err?.message || 'Failed to generate execution roadmap.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    try {
      await api.roadmap.updateTask(projectId, taskId, { status: newStatus as any });
      onRoadmapUpdated();
    } catch (err: any) {
      setError(err?.message || 'Failed to update task status.');
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;
    try {
      await api.roadmap.deleteTask(projectId, taskId);
      onRoadmapUpdated();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete task.');
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    setIsSubmittingTask(true);
    setError(null);
    try {
      await api.roadmap.createTask(projectId, {
        title: newTaskTitle,
        description: newTaskDesc,
        milestone: newTaskMilestone,
        priority: newTaskPriority as any,
        deliverable: newTaskDeliverable,
        stage: 'Planning',
        estimated_effort_days: 2.0,
        start_day: 1,
        duration_days: 7,
        dependencies: [],
      });
      setIsCreateOpen(false);
      setNewTaskTitle('');
      setNewTaskDesc('');
      setNewTaskDeliverable('');
      setSuccess('Custom execution task added.');
      onRoadmapUpdated();
    } catch (err: any) {
      setError(err?.message || 'Failed to create task.');
    } finally {
      setIsSubmittingTask(false);
    }
  };

  const tasks = roadmap?.tasks || [];
  const milestones = roadmap?.milestones || [];
  const filteredTasks = selectedMilestone === 'all'
    ? tasks
    : tasks.filter((t) => t.milestone.toLowerCase() === selectedMilestone.toLowerCase());

  if (!roadmap || tasks.length === 0) {
    return (
      <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-lg mx-auto space-y-4 my-8">
        <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
          <Calendar className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-slate-900">AI Execution Roadmap</h3>
          <p className="text-sm text-slate-500">
            Synthesize a phased 30-day, 60-day, and 90-day actionable roadmap with DAG dependency checks and deliverable tracking.
          </p>
        </div>
        {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
        <Button
          onClick={handleGenerate}
          isLoading={isGenerating}
          leftIcon={<Sparkles className="w-4 h-4" />}
          className="w-full justify-center"
        >
          Generate Execution Roadmap
        </Button>
      </div>
    );
  }

  const getPriorityBadgeVariant = (p: string) => {
    switch (p.toLowerCase()) {
      case 'critical':
        return 'rose';
      case 'high':
        return 'amber';
      case 'medium':
        return 'indigo';
      default:
        return 'slate';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Milestone className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-slate-900">Execution Plan & Sprints</h2>
              <Badge variant="indigo">{roadmap.completed_tasks} / {roadmap.total_tasks} Completed</Badge>
            </div>
            <p className="text-xs text-slate-500">
              Phased DAG execution graph • Overall Progress: {roadmap.overall_progress_pct}%
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsCreateOpen(true)}
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            Add Task
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleGenerate}
            isLoading={isGenerating}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Regenerate
          </Button>
        </div>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {/* Progress by Milestone */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {milestones.map((m) => (
          <Card key={m.milestone} className="border-slate-200">
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs uppercase tracking-wider text-slate-700">{m.milestone} Milestone</span>
                <span className="text-xs font-bold text-indigo-600">{m.completion_pct}%</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full mt-2 overflow-hidden">
                <div
                  className="bg-indigo-600 h-full rounded-full transition-all duration-300"
                  style={{ width: `${m.completion_pct}%` }}
                />
              </div>
              <div className="text-[11px] text-slate-500 mt-1 flex justify-between">
                <span>{m.completed_tasks} completed</span>
                <span>{m.total_tasks} total tasks</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <div className="flex items-center gap-2">
          {['all', '30-day', '60-day', '90-day'].map((phase) => (
            <button
              key={phase}
              onClick={() => setSelectedMilestone(phase)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                selectedMilestone === phase
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:text-slate-900'
              }`}
            >
              {phase}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-500">Showing {filteredTasks.length} tasks</span>
      </div>

      {/* Tasks List */}
      <div className="space-y-3">
        {filteredTasks.map((task) => (
          <div
            key={task.id}
            className="border border-slate-200 rounded-xl p-4 bg-white hover:border-slate-300 transition-all space-y-2.5 shadow-sm"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                  {task.task_key}
                </span>
                <Badge variant={getPriorityBadgeVariant(task.priority)} size="sm">
                  {task.priority}
                </Badge>
                <Badge variant="slate" size="sm">
                  {task.milestone}
                </Badge>
                <h4 className="font-bold text-sm text-slate-900">{task.title}</h4>
              </div>

              {/* Status Selector & Delete */}
              <div className="flex items-center gap-2">
                <select
                  value={task.status}
                  onChange={(e) => handleStatusChange(task.id, e.target.value)}
                  className="text-xs font-semibold border border-slate-200 rounded-lg px-2.5 py-1 bg-slate-50 text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="blocked">Blocked</option>
                </select>

                <button
                  onClick={() => handleDeleteTask(task.id)}
                  className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                  title="Delete Task"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">{task.description}</p>

            <div className="flex flex-wrap items-center gap-y-1 gap-x-4 pt-2 border-t border-slate-100 text-[11px] text-slate-500">
              {task.deliverable && (
                <div>
                  <strong className="text-slate-700">Deliverable:</strong> {task.deliverable}
                </div>
              )}
              {task.dependencies && task.dependencies.length > 0 && (
                <div className="flex items-center gap-1">
                  <strong className="text-slate-700">Depends on:</strong>
                  {task.dependencies.map((dep, dIdx) => (
                    <span key={dIdx} className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                      {dep}
                    </span>
                  ))}
                </div>
              )}
              <div>
                <strong className="text-slate-700">Effort:</strong> {task.estimated_effort_days} days
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Task Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Custom Execution Task"
      >
        <form onSubmit={handleCreateTask} className="space-y-4">
          <Input
            label="Task Title"
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
            placeholder="e.g. Conduct user interviews"
            required
          />

          <Textarea
            label="Description"
            value={newTaskDesc}
            onChange={(e) => setNewTaskDesc(e.target.value)}
            placeholder="Specify procedure and requirements..."
            rows={3}
          />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Milestone</label>
              <select
                value={newTaskMilestone}
                onChange={(e) => setNewTaskMilestone(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs bg-white text-slate-800"
              >
                <option value="30-day">30-day</option>
                <option value="60-day">60-day</option>
                <option value="90-day">90-day</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
              <select
                value={newTaskPriority}
                onChange={(e) => setNewTaskPriority(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs bg-white text-slate-800"
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <Input
            label="Deliverable (Optional)"
            value={newTaskDeliverable}
            onChange={(e) => setNewTaskDeliverable(e.target.value)}
            placeholder="e.g. Summary report"
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmittingTask}>
              Save Task
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
