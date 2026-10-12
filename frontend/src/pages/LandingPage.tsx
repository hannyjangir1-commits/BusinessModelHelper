import React, { useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
  Sparkles,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

interface LandingPageProps {
  onNavigate: (path: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const faqs = [
    {
      q: 'How does AI Business Architect generate business blueprints?',
      a: 'The platform takes your business idea, domain, budget, stage, and operational constraints through a structured intake form. Our Python-first AI orchestration pipeline then feeds this context to Google Gemini with versioned prompt templates, parses the output into strict Pydantic schemas, and runs deterministic business rule evaluations before saving the blueprint to PostgreSQL.',
    },
    {
      q: 'Can I edit the generated canvas and technology stack?',
      a: 'Yes. Every block in the 9-block Business Model Canvas and every recommendation in the Technology Stack can be directly modified and saved. You can also trigger regeneration at any time, with previous successful versions preserved in your version history.',
    },
    {
      q: 'Does this replace professional legal or financial advice?',
      a: 'No. The platform is designed for preliminary venture planning, conceptual ideation, and architectural exploration. AI recommendations and estimated costs do not constitute certified legal, financial, or tax counsel, and all vendor pricing should be independently verified before commercial commitments.',
    },
    {
      q: 'Are my business ideas kept private?',
      a: 'Yes. Your business ideas belong entirely to you. Data is transmitted securely over server-side TLS connections directly to the configured AI provider and stored in your private database. We do not sell your data or expose it to public scraping directories.',
    },
    {
      q: 'What format are exported blueprints provided in?',
      a: 'You can export complete project blueprints directly to professional multi-page PDF documents generated on the server using ReportLab. The PDF includes executive summaries, the 9-block canvas, full technology stack recommendations, and risk disclosures.',
    },
  ];

  return (
    <div className="space-y-24 pb-20">
      {/* Hero Section */}
      <section className="relative pt-20 pb-16 md:pt-28 md:pb-24 overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_top,theme(colors.indigo.100),theme(colors.slate.50))] opacity-60" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-200/80 text-indigo-700 text-xs font-semibold shadow-xs">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Turn your business idea into an actionable blueprint</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-[1.12]">
            Build your business blueprint with <span className="text-indigo-600">AI</span>.
          </h1>

          <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Transform your business idea into a structured <strong>Business Model Canvas</strong> and a practical{' '}
            <strong>technology-stack recommendation</strong>. Review, refine, save, and export your blueprint from one
            unified workspace.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Button
              size="lg"
              variant="primary"
              onClick={() => onNavigate('/register')}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Start building
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => {
                const el = document.getElementById('features');
                el?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Explore features
            </Button>
          </div>

          <div className="pt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500 font-medium">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Complete 9-Block Canvas
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Pragmatic Tech Stacks
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Full Version History
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Publication-Ready PDF
            </span>
          </div>
        </div>
      </section>

      {/* Interactive Canvas Preview Section */}
      <section id="canvas-preview" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-3 mb-12">
          <Badge variant="indigo">Structured Methodology</Badge>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">The 9-Block Business Model Canvas</h2>
          <p className="text-sm text-slate-600 max-w-2xl mx-auto">
            AI Business Architect generates actionable strategic plans tailored to your exact industry and target audience.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 p-4 bg-slate-100/80 rounded-2xl border border-slate-200 shadow-sm">
          {/* Key Partnerships */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/90 space-y-2 md:col-span-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">8. Partnerships</span>
            <h3 className="text-xs font-bold text-slate-900">Key Partnerships</h3>
            <p className="text-xs text-slate-600 leading-snug">
              Strategic cloud alliances, accelerator partnerships, and API model providers.
            </p>
          </div>

          {/* Key Activities & Resources */}
          <div className="md:col-span-1 space-y-3">
            <div className="bg-white p-4 rounded-xl border border-slate-200/90 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">7. Activities</span>
              <h3 className="text-xs font-bold text-slate-900">Key Activities</h3>
              <p className="text-xs text-slate-600 leading-snug">
                AI orchestration engineering, domain prompt validation, continuous user feedback.
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200/90 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">6. Resources</span>
              <h3 className="text-xs font-bold text-slate-900">Key Resources</h3>
              <p className="text-xs text-slate-600 leading-snug">
                Python architecture pipeline, PostgreSQL database, domain validation schemas.
              </p>
            </div>
          </div>

          {/* Value Propositions */}
          <div className="bg-indigo-50/60 p-4 rounded-xl border border-indigo-200 space-y-2 md:col-span-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700">2. Core Value</span>
            <h3 className="text-xs font-bold text-indigo-950">Value Propositions</h3>
            <p className="text-xs text-indigo-900 leading-snug">
              Transform raw startup concepts into rigorous business canvases and production-ready tech stacks in minutes.
            </p>
          </div>

          {/* Customer Relationships & Channels */}
          <div className="md:col-span-1 space-y-3">
            <div className="bg-white p-4 rounded-xl border border-slate-200/90 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">4. Relations</span>
              <h3 className="text-xs font-bold text-slate-900">Customer Relationships</h3>
              <p className="text-xs text-slate-600 leading-snug">
                Transparent self-service SaaS, guided intake wizard, instant blueprint export.
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200/90 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">3. Channels</span>
              <h3 className="text-xs font-bold text-slate-900">Channels</h3>
              <p className="text-xs text-slate-600 leading-snug">
                Developer communities, Product Hunt, technical case studies, and organic search.
              </p>
            </div>
          </div>

          {/* Customer Segments */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/90 space-y-2 md:col-span-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">1. Customers</span>
            <h3 className="text-xs font-bold text-slate-900">Customer Segments</h3>
            <p className="text-xs text-slate-600 leading-snug">
              Solo technical founders, student entrepreneurs, incubator cohort builders, small business owners.
            </p>
          </div>

          {/* Cost Structure & Revenue Streams */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/90 space-y-2 md:col-span-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">9. Costs</span>
            <h3 className="text-xs font-bold text-slate-900">Cost Structure</h3>
            <p className="text-xs text-slate-600 leading-snug">
              Containerized PaaS cloud hosting, database storage, upstream AI API inference tokens.
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200/90 space-y-2 md:col-span-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600">5. Revenue</span>
            <h3 className="text-xs font-bold text-slate-900">Revenue Streams</h3>
            <p className="text-xs text-slate-600 leading-snug">
              Freemium individual project tiers, subscription plans for multiple blueprints, team export licenses.
            </p>
          </div>
        </div>
      </section>

      {/* Feature Deep Dive */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-3 mb-16">
          <Badge variant="indigo">Platform Modules</Badge>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Two Specialized AI Engines</h2>
          <p className="text-sm text-slate-600 max-w-2xl mx-auto">
            Everything you need to turn ambiguous ideas into concrete, buildable blueprints.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card hover>
            <CardContent className="p-8 space-y-5">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">Module 1: Business Model Canvas</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Systematically analyzes your target audience, customer segments, channels, and revenue opportunities.
                Each block includes:
              </p>
              <ul className="space-y-2 text-xs text-slate-700">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Concise strategic executive summary
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Actionable, domain-specific recommendations
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Underlying assumptions requiring testing
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Low-cost empirical validation experiments
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card hover>
            <CardContent className="p-8 space-y-5">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">Module 2: Technology Stack Recommendation</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Recommends a pragmatic implementation architecture tailored to your stage, budget, and engineering skills.
                Covers:
              </p>
              <ul className="space-y-2 text-xs text-slate-700">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Frontend, Backend, and Database choices
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Hosting, Deployment, and Third-Party APIs
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Explicit alternatives and architectural trade-offs
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Transparent cost estimates with verification notes
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-3 mb-16">
          <Badge variant="indigo">User Journey</Badge>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">How The Platform Works</h2>
          <p className="text-sm text-slate-600 max-w-2xl mx-auto">From an initial spark of an idea to an investor-ready PDF in three steps.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 bg-white rounded-2xl border border-slate-200/90 shadow-xs space-y-4 text-center">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center mx-auto text-base">
              1
            </div>
            <h3 className="text-base font-bold text-slate-900">Guided Intake Wizard</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Answer structured questions about your business concept, target customer, budget range, and constraints.
              Save drafts at any stage.
            </p>
          </div>

          <div className="p-6 bg-white rounded-2xl border border-slate-200/90 shadow-xs space-y-4 text-center">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center mx-auto text-base">
              2
            </div>
            <h3 className="text-base font-bold text-slate-900">AI Architecture Engine</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              The Python backend validates input, calls Google Gemini with versioned prompts, enforces strict schema
              compliance, and evaluates business rules.
            </p>
          </div>

          <div className="p-6 bg-white rounded-2xl border border-slate-200/90 shadow-xs space-y-4 text-center">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center mx-auto text-base">
              3
            </div>
            <h3 className="text-base font-bold text-slate-900">Refine & Export PDF</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Edit any block directly in the dashboard, regenerate modules, track version history, and download a
              polished multi-page PDF blueprint.
            </p>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-3 mb-12">
          <Badge variant="indigo">Frequently Asked Questions</Badge>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Got Questions? We Have Answers</h2>
          <p className="text-sm text-slate-600 max-w-xl mx-auto">
            Everything you need to know about methodology, privacy, and outputs.
          </p>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div key={idx} className="bg-white border border-slate-200 rounded-xl overflow-hidden transition-all">
                <button
                  id={`faq-question-${idx}`}
                  type="button"
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${idx}`}
                  className="w-full text-left p-5 flex items-center justify-between text-sm font-semibold text-slate-900 hover:text-indigo-600 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 rounded-xl transition-colors cursor-pointer"
                >
                  <span>{faq.q}</span>
                  {isOpen ? (
                    <ChevronUp className="w-4 h-4 text-slate-500 shrink-0" aria-hidden="true" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" aria-hidden="true" />
                  )}
                </button>
                {isOpen && (
                  <div
                    id={`faq-answer-${idx}`}
                    role="region"
                    aria-labelledby={`faq-question-${idx}`}
                    className="px-5 pb-5 pt-1 text-xs text-slate-600 leading-relaxed border-t border-slate-100"
                  >
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Final Call to Action Banner */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-tr from-indigo-900 via-indigo-800 to-slate-900 rounded-3xl p-8 md:p-14 text-center text-white space-y-6 shadow-xl">
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight max-w-2xl mx-auto">
            Ready to turn your idea into an actionable blueprint?
          </h2>
          <p className="text-sm text-indigo-200 max-w-xl mx-auto leading-relaxed">
            Create an account in 60 seconds and generate your first complete Business Model Canvas and Technology Stack.
          </p>
          <div className="pt-2">
            <Button
              size="lg"
              className="bg-white text-indigo-900 hover:bg-indigo-50 font-bold px-8 shadow-md"
              onClick={() => onNavigate('/register')}
              rightIcon={<ArrowRight className="w-4 h-4 text-indigo-900" />}
            >
              Start building free
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};
