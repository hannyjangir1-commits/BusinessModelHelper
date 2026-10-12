import React, { useEffect, useState } from 'react';
import {
  Bot,
  Check,
  FileEdit,
  History,
  Send,
  Sparkles,
  User,
  X,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  CopilotProposal,
  CopilotRevisionItem,
} from '../../types';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Alert } from '../ui/Alert';
import { MarkdownContent } from '../ui/MarkdownContent';

interface CopilotWorkspaceViewProps {
  projectId: string;
  onBlueprintModified: () => void;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'copilot';
  text: string;
  action_type?: string;
  proposal?: CopilotProposal;
  timestamp: string;
}

export const CopilotWorkspaceView: React.FC<CopilotWorkspaceViewProps> = ({
  projectId,
  onBlueprintModified,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'copilot',
      text: "Hello! I am your AI Business Architect Copilot. I have full read access to your saved business model, tech stack, and validation reports. Ask me questions or instruct me to propose targeted refinements to any section.",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputQuery, setInputQuery] = useState<string>('');
  const [actionType, setActionType] = useState<'answer_question' | 'propose_edit'>('answer_question');
  const [targetModule, setTargetModule] = useState<string>('business_model');
  const [targetSection, setTargetSection] = useState<string>('customer_segments');
  const [isSending, setIsSending] = useState<boolean>(false);
  const [activeProposal, setActiveProposal] = useState<CopilotProposal | null>(null);
  const [revisions, setRevisions] = useState<CopilotRevisionItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadRevisions = async () => {
    try {
      const items = await api.copilot.listRevisions(projectId);
      setRevisions(items);
    } catch {
      setRevisions([]);
    }
  };

  useEffect(() => {
    loadRevisions();
  }, [projectId]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isSending) return;

    const userText = inputQuery.trim();
    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsSending(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.copilot.chat(projectId, {
        query: userText,
        action_type: actionType,
        target_module: actionType === 'propose_edit' ? targetModule : undefined,
        target_section: actionType === 'propose_edit' ? targetSection : undefined,
      });

      if (res.action_type === 'answer_question') {
        const copilotMsg: ChatMessage = {
          id: String(Date.now() + 1),
          sender: 'copilot',
          text: res.answer || 'No response generated.',
          action_type: 'answer_question',
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages((prev) => [...prev, copilotMsg]);
      } else if (res.action_type === 'propose_edit' && res.proposal) {
        setActiveProposal(res.proposal);
        const copilotMsg: ChatMessage = {
          id: String(Date.now() + 1),
          sender: 'copilot',
          text: `I have generated a proposed revision for [${res.proposal.target_module} -> ${res.proposal.target_section}]. Please review the before/after preview below to accept or reject it.`,
          action_type: 'propose_edit',
          proposal: res.proposal,
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages((prev) => [...prev, copilotMsg]);
      }
      loadRevisions();
    } catch (err: any) {
      setError(err?.message || 'Copilot operation failed.');
    } finally {
      setIsSending(false);
    }
  };

  const handleAcceptProposal = async (proposalId: string) => {
    setError(null);
    try {
      await api.copilot.acceptProposal(projectId, proposalId);
      setSuccess('Proposal accepted! Blueprint successfully updated with audit record.');
      setActiveProposal(null);
      onBlueprintModified();
      loadRevisions();
    } catch (err: any) {
      setError(err?.message || 'Failed to accept proposal.');
    }
  };

  const handleRejectProposal = async (proposalId: string) => {
    setError(null);
    try {
      await api.copilot.rejectProposal(projectId, proposalId);
      setSuccess('Proposal rejected. Blueprint remains completely unchanged.');
      setActiveProposal(null);
      loadRevisions();
    } catch (err: any) {
      setError(err?.message || 'Failed to reject proposal.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-slate-900">Business Blueprint Copilot</h2>
              <Badge variant="indigo">Project Grounded</Badge>
            </div>
            <p className="text-xs text-slate-500">
              Interactive strategic advisor & controlled before/after blueprint editor
            </p>
          </div>
        </div>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {/* Active Proposal Review Banner */}
      {activeProposal && (
        <Card className="border-indigo-300 ring-2 ring-indigo-500/20 bg-indigo-50/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <FileEdit className="w-4 h-4 text-indigo-600" /> Proposed Modification Review
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant="indigo">{activeProposal.target_module}</Badge>
                <Badge variant="slate">{activeProposal.target_section}</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeProposal.reasoning && (
              <p className="text-xs text-slate-700 font-medium">
                <strong>Reasoning:</strong> {activeProposal.reasoning}
              </p>
            )}

            {/* Before vs After Side-by-Side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="border border-slate-200 rounded-xl p-3 bg-white space-y-1">
                <span className="font-bold text-[10px] uppercase tracking-wider text-slate-500 block">
                  Current Saved Content
                </span>
                <pre className="text-[11px] text-slate-700 bg-slate-50 p-2.5 rounded-lg overflow-x-auto whitespace-pre-wrap max-h-48">
                  {JSON.stringify(activeProposal.previous_content || 'None currently saved', null, 2)}
                </pre>
              </div>

              <div className="border border-emerald-200 rounded-xl p-3 bg-white space-y-1">
                <span className="font-bold text-[10px] uppercase tracking-wider text-emerald-700 block">
                  Proposed Replacement
                </span>
                <pre className="text-[11px] text-emerald-900 bg-emerald-50/50 p-2.5 rounded-lg overflow-x-auto whitespace-pre-wrap max-h-48 font-semibold">
                  {JSON.stringify(activeProposal.proposed_content, null, 2)}
                </pre>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleRejectProposal(activeProposal.proposal_id)}
                leftIcon={<X className="w-3.5 h-3.5 text-rose-500" />}
              >
                Reject Proposal (Keep Existing)
              </Button>
              <Button
                size="sm"
                onClick={() => handleAcceptProposal(activeProposal.proposal_id)}
                leftIcon={<Check className="w-3.5 h-3.5 text-emerald-500" />}
              >
                Accept & Apply to Blueprint
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Chat Interface */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          {/* Chat Messages Log */}
          <div className="space-y-4 max-h-[420px] overflow-y-auto pr-2">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 text-xs ${
                  msg.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.sender === 'copilot' && (
                  <div className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-2xl p-3.5 space-y-1 shadow-sm ${
                    msg.sender === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-none'
                      : 'bg-slate-50 text-slate-800 rounded-tl-none border border-slate-200/80'
                  }`}
                >
                  {msg.sender === 'copilot' ? (
                    <MarkdownContent content={msg.text} />
                  ) : (
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                  )}
                  <span
                    className={`text-[9px] block text-right pt-1 ${
                      msg.sender === 'user' ? 'text-indigo-200' : 'text-slate-400'
                    }`}
                  >
                    {msg.timestamp}
                  </span>
                </div>
                {msg.sender === 'user' && (
                  <div className="w-7 h-7 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}
            {isSending && (
              <div className="flex gap-3 text-xs items-center text-slate-500 italic">
                <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 animate-pulse">
                  <Sparkles className="w-4 h-4" />
                </div>
                <span>Analyzing project context and reasoning...</span>
              </div>
            )}
          </div>

          {/* Operation Selector & Input Form */}
          <form onSubmit={handleSendMessage} className="space-y-3 pt-3 border-t border-slate-200">
            <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
              {/* Mode Toggle */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
                <button
                  type="button"
                  onClick={() => setActionType('answer_question')}
                  className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                    actionType === 'answer_question'
                      ? 'bg-white text-indigo-700 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Ask Question (Advisory)
                </button>
                <button
                  type="button"
                  onClick={() => setActionType('propose_edit')}
                  className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                    actionType === 'propose_edit'
                      ? 'bg-white text-indigo-700 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Propose Edit (Section Change)
                </button>
              </div>

              {/* Target Section Selector (Only in propose_edit mode) */}
              {actionType === 'propose_edit' && (
                <div className="flex items-center gap-2">
                  <select
                    value={targetModule}
                    onChange={(e) => setTargetModule(e.target.value)}
                    className="border border-slate-200 rounded-lg px-2 py-1 text-xs bg-white text-slate-800"
                  >
                    <option value="business_model">Business Model</option>
                    <option value="technology_stack">Technology Stack</option>
                  </select>

                  <select
                    value={targetSection}
                    onChange={(e) => setTargetSection(e.target.value)}
                    className="border border-slate-200 rounded-lg px-2 py-1 text-xs bg-white text-slate-800"
                  >
                    <option value="customer_segments">Customer Segments</option>
                    <option value="value_propositions">Value Propositions</option>
                    <option value="revenue_streams">Revenue Streams</option>
                    <option value="channels">Channels</option>
                    <option value="cost_structure">Cost Structure</option>
                    <option value="frontend">Frontend Architecture</option>
                    <option value="backend">Backend Architecture</option>
                    <option value="database">Database Strategy</option>
                  </select>
                </div>
              )}
            </div>

            {/* Input & Send Button */}
            <div className="relative">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder={
                  actionType === 'answer_question'
                    ? "Ask a strategic question about your business plan, unit economics, or tech choices..."
                    : `Instruct copilot how to refine [${targetModule} -> ${targetSection}]...`
                }
                className="w-full pl-3 pr-20 py-2.5 text-xs border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                disabled={isSending}
              />
              <Button
                type="submit"
                size="sm"
                className="absolute right-1.5 top-1.5"
                isLoading={isSending}
                disabled={!inputQuery.trim() || isSending}
              >
                <Send className="w-3.5 h-3.5" />
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Revision History Log */}
      {revisions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <History className="w-4 h-4 text-slate-500" /> Copilot Revision History ({revisions.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-slate-100 text-xs">
              {revisions.map((rev) => (
                <div key={rev.id} className="py-2.5 flex items-center justify-between gap-4">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900">
                        [{rev.target_module} &rarr; {rev.target_section}]
                      </span>
                      <Badge
                        variant={rev.status === 'accepted' ? 'emerald' : rev.status === 'rejected' ? 'rose' : 'amber'}
                        size="sm"
                      >
                        {rev.status}
                      </Badge>
                    </div>
                    <p className="text-slate-600">{rev.user_query}</p>
                  </div>
                  <span className="text-xs font-medium text-slate-600 whitespace-nowrap">
                    {new Date(rev.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
