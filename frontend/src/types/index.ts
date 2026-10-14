/**
 * TypeScript data models and API response types.
 */

export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string;
  bio?: string | null;
  country?: string | null;
  preferred_currency: string;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
  is_active: boolean;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  idea_description: string;
  industry: string;
  business_stage: string;
  target_market?: string | null;
  target_audience?: string | null;
  budget_amount?: number | null;
  budget_currency: string;
  team_size?: string | null;
  technical_preferences?: string | null;
  constraints?: string | null;
  created_at: string;
  updated_at: string;
  has_business_model: boolean;
  has_technology_stack: boolean;
  has_validator_report?: boolean;
  has_financial_model?: boolean;
  has_market_research?: boolean;
  has_roadmap?: boolean;
  latest_bmc_version?: number | null;
  latest_tech_version?: number | null;
}

export interface BMCBlock {
  block_title: string;
  summary: string;
  recommendations: string[];
  rationale: string;
  assumptions: string[];
  risks_uncertainties: string[];
  validation_experiments: string[];
}

export interface BusinessModelCanvasData {
  overview: string;
  key_strategic_focus: string;
  customer_segments: BMCBlock;
  value_propositions: BMCBlock;
  channels: BMCBlock;
  customer_relationships: BMCBlock;
  revenue_streams: BMCBlock;
  key_resources: BMCBlock;
  key_activities: BMCBlock;
  key_partnerships: BMCBlock;
  cost_structure: BMCBlock;
}

export interface TechRecommendationItem {
  category: string;
  technology: string;
  purpose: string;
  reason: string;
  alternatives: string[];
  tradeoffs: string[];
  estimated_cost: string;
  cost_period: string;
  cost_assumptions: string[];
  constraints: string[];
  verification_notes: string;
}

export interface TechnologyStackData {
  architecture_summary: string;
  estimated_monthly_infrastructure_total: string;
  frontend: TechRecommendationItem;
  backend: TechRecommendationItem;
  database: TechRecommendationItem;
  hosting_infrastructure: TechRecommendationItem;
  third_party_services: TechRecommendationItem;
  scalability_considerations: string[];
  security_considerations: string[];
}

export interface Blueprint {
  id: string;
  project_id: string;
  module_type: 'business_model' | 'technology_stack';
  version: number;
  content_json: BusinessModelCanvasData | TechnologyStackData;
  created_at: string;
  updated_at: string;
}

export interface BlueprintVersionItem {
  id: string;
  version: number;
  module_type: string;
  created_at: string;
  updated_at: string;
}

export interface GenerationRun {
  id: string;
  project_id: string;
  user_id: string;
  module_type: string;
  status: 'running' | 'success' | 'failed';
  model: string;
  prompt_version: string;
  latency_ms?: number | null;
  input_token_count?: number | null;
  output_token_count?: number | null;
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface PaginationMetadata {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  success: boolean;
  items: T[];
  pagination: PaginationMetadata;
}

// ============================================================================
// MODULE 1: AI BUSINESS IDEA VALIDATOR
// ============================================================================
export interface ProblemSolutionFit {
  problem_statement: string;
  who_experiences_it: string;
  frequency_and_severity: string;
  existing_alternatives: string[];
  supporting_evidence: string[];
  missing_evidence: string[];
}

export interface TargetCustomerClarity {
  primary_segment: string;
  secondary_segments: string[];
  buyer_vs_end_user: string;
  customer_pain_points: string[];
  adoption_barriers: string[];
  unvalidated_assumptions: string[];
}

export interface ValuePropositionAssessment {
  core_benefit: string;
  differentiation_hypotheses: string[];
  potential_weaknesses: string[];
  critical_dependencies: string[];
  key_evidence_needed: string[];
}

export interface SWOTAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface BusinessRisk {
  category: string;
  description: string;
  why_it_matters: string;
  likelihood: 'Low' | 'Medium' | 'High';
  impact: 'Low' | 'Medium' | 'High';
  supporting_info?: string;
  suggested_mitigation: string;
  recommended_next_action: string;
}

export interface ValidationExperiment {
  experiment_name: string;
  experiment_type: string;
  hypothesis: string;
  target_audience: string;
  procedure: string;
  estimated_duration: string;
  estimated_cost: string;
  success_criteria: string;
  interpretation_guidance: string;
}

export interface CustomerInterviewQuestion {
  question_text: string;
  focus_category?: string;
  rationale?: string;
}

export type InterviewQuestionItem = string | CustomerInterviewQuestion;

export interface ValidationSummary {
  strongest_supporting_evidence?: string[] | string;
  largest_uncertainties?: string[];
  highest_priority_risks?: string[];
  most_useful_next_experiment?: string;
  unverified_assumptions?: string[];
  qualitative_readiness_assessment?: string;
}

export interface ValidationReportData {
  overview: string;
  problem_solution_fit: ProblemSolutionFit;
  target_customer_clarity: TargetCustomerClarity;
  value_proposition_assessment?: ValuePropositionAssessment;
  swot_analysis: SWOTAnalysis;
  business_risks: BusinessRisk[];
  validation_experiments: ValidationExperiment[];
  interview_questions: InterviewQuestionItem[];
  summary: ValidationSummary;
}

export interface ValidationReportResponse {
  id: string;
  project_id: string;
  module_type?: string;
  version: number;
  content?: ValidationReportData;
  content_json?: ValidationReportData;
  created_at: string;
  updated_at: string;
}


// ============================================================================
// MODULE 3: MARKET & COMPETITOR RESEARCH
// ============================================================================
export interface SourceItem {
  url: string;
  title: string;
  snippet: string;
  domain?: string;
  retrieved_at: string;
}

export interface MarketTrend {
  trend_title: string;
  description: string;
  implications_for_founder: string;
  supporting_sources: string[];
}

export interface CompetitorProfile {
  name: string;
  website: string;
  product_summary: string;
  target_audience: string;
  pricing_model: string;
  estimated_pricing: string;
  key_features: string[];
  positioning: string;
  differentiators: string[];
  strengths: string[];
  weaknesses: string[];
  source_urls: string[];
}

export interface ComparisonCriterion {
  criterion: string;
  founder_solution: string;
  competitor_comparison: Record<string, string>;
}

export interface MarketResearchReportData {
  executive_summary: string;
  industry_definition: string;
  market_trends: MarketTrend[];
  barriers_to_entry: string[];
  distribution_channels: string[];
  competitors: CompetitorProfile[];
  comparison_matrix: ComparisonCriterion[];
  market_sizing: {
    market_definition: string;
    tam_description: string;
    sam_description: string;
    som_description: string;
    sizing_caveats: string;
  };
  research_methodology_disclaimer: string;
  sources?: SourceItem[];
}

export interface MarketResearchResponse {
  id: string;
  project_id: string;
  module_type?: string;
  version: number;
  content?: MarketResearchReportData;
  content_json?: MarketResearchReportData;
  sources?: SourceItem[];
  created_at: string;
  updated_at: string;
}

// ============================================================================
// MODULE 4: AI EXECUTION ROADMAP
// ============================================================================
export interface RoadmapTask {
  id: string;
  project_id: string;
  task_key: string;
  milestone: '30-day' | '60-day' | '90-day' | string;
  stage: string;
  title: string;
  description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  estimated_effort_days: number;
  start_day: number;
  duration_days: number;
  dependencies: string[];
  deliverable?: string | null;
  success_criteria?: string | null;
  related_risk?: string | null;
  kpi?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MilestoneProgressItem {
  milestone: string;
  total_tasks: number;
  completed_tasks: number;
  completion_pct: number;
}

export interface RoadmapResponse {
  project_id: string;
  tasks: RoadmapTask[];
  milestones: MilestoneProgressItem[];
  total_tasks: number;
  completed_tasks: number;
  overall_progress_pct: number;
}

// ============================================================================
// MODULE 5: BUSINESS BLUEPRINT COPILOT
// ============================================================================
export interface CopilotProposal {
  proposal_id: string;
  target_module: string;
  target_section: string;
  previous_content?: any;
  proposed_content: any;
  reasoning?: string;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
}

export interface CopilotChatResponse {
  action_type: 'answer_question' | 'propose_edit';
  answer?: string;
  proposal?: CopilotProposal;
}

export interface CopilotRevisionItem {
  id: string;
  target_module: string;
  target_section: string;
  action_type: string;
  status: 'pending' | 'accepted' | 'rejected';
  user_query: string;
  reasoning?: string;
  created_at: string;
  resolved_at?: string | null;
}

export interface LoginPayload {
  username_or_email?: string;
  username?: string;
  email?: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  terms_accepted: boolean;
  privacy_acknowledged: boolean;
  privacy_accepted?: boolean;
  display_name?: string;
  agreements_version?: string;
}

export interface UpdateProfilePayload {
  display_name?: string;
  bio?: string | null;
  country?: string | null;
  preferred_currency?: string;
}

export interface ChangePasswordPayload {
  current_password?: string;
  old_password?: string;
  new_password?: string;
  confirm_new_password?: string;
  password?: string;
}

export interface DeleteAccountPayload {
  password: string;
  confirmation_text: string;
}

export interface CreateProjectPayload {
  name: string;
  idea_description: string;
  industry: string;
  business_stage: string;
  target_market?: string | null;
  target_audience?: string | null;
  budget_amount?: number | null;
  budget_currency?: string;
  team_size?: string | null;
  technical_preferences?: string | null;
  constraints?: string | null;
}

export type UpdateProjectPayload = Partial<CreateProjectPayload>;

