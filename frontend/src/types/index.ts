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
