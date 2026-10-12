/**
 * Centralized API client for AI Business Architect.
 * Uses relative URLs and HTTP-only session cookies with CSRF validation.
 */

import type {
  ApiResponse,
  Blueprint,
  BlueprintVersionItem,
  BusinessModelCanvasData,
  ChangePasswordPayload,
  CopilotChatResponse,
  CopilotProposal,
  CopilotRevisionItem,
  CreateProjectPayload,
  DeleteAccountPayload,
  GenerationRun,
  LoginPayload,
  MarketResearchResponse,
  PaginatedResponse,
  Project,
  RegisterPayload,
  RoadmapResponse,
  RoadmapTask,
  TechnologyStackData,
  UpdateProfilePayload,
  UpdateProjectPayload,
  User,
  ValidationReportResponse,
} from '../types/index.ts';

let currentCsrfToken: string | null = null;

export function setCsrfToken(token: string | null) {
  currentCsrfToken = token;
}

import { normalizeValidationReportData } from '../utils/validator.ts';
export { normalizeValidationReportData };

export function getCsrfToken(): string | null {
  return currentCsrfToken;
}

export interface RequestOptions {
  signal?: AbortSignal;
}

export function isNotFoundError(err: unknown): boolean {
  if (err && typeof err === 'object') {
    const errorObj = err as { status?: number; code?: string };
    return errorObj.status === 404 || errorObj.code === 'NOT_FOUND';
  }
  return false;
}

export function isAbortError(err: unknown): boolean {
  if (err && typeof err === 'object') {
    const errorObj = err as { name?: string; code?: string; message?: string };
    return (
      errorObj.name === 'AbortError' ||
      errorObj.code === 'ABORT_ERR' ||
      Boolean(typeof errorObj.message === 'string' && errorObj.message.toLowerCase().includes('aborted'))
    );
  }
  return false;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown> | null;

  constructor(
    message: string,
    code: string = 'API_ERROR',
    status: number = 400,
    details?: Record<string, unknown> | null
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  if (currentCsrfToken && ['POST', 'PATCH', 'PUT', 'DELETE'].includes(options.method?.toUpperCase() || '')) {
    headers.set('X-CSRF-Token', currentCsrfToken);
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Ensure session cookies are always transmitted
  };

  const response = await fetch(endpoint, config);

  // Handle PDF or binary downloads
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/pdf')) {
    if (!response.ok) {
      throw new ApiError('Failed to download PDF document.', 'EXPORT_FAILED', response.status);
    }
    return (await response.blob()) as unknown as T;
  }

  const csrfHeader = response.headers.get('X-CSRF-Token');
  if (csrfHeader) {
    setCsrfToken(csrfHeader);
  }

  let data: any = null;
  try {
    data = await response.json();
  } catch (err) {
    if (!response.ok) {
      throw new ApiError(`Server error (${response.status})`, 'SERVER_ERROR', response.status);
    }
    return null as unknown as T;
  }

  if (!response.ok || data.success === false) {
    const errorMsg = data?.error?.message || data?.message || `Request failed with status ${response.status}`;
    const errorCode = data?.error?.code || 'REQUEST_FAILED';
    throw new ApiError(errorMsg, errorCode, response.status, data?.error?.details);
  }

  return data;
}

export const api = {
  auth: {
    async register(data: RegisterPayload, options?: RequestOptions): Promise<{ user: User; csrf_token: string }> {
      const res = await request<ApiResponse<{ user: User; csrf_token: string }>>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
        signal: options?.signal,
      });
      if (res.data?.csrf_token) {
        setCsrfToken(res.data.csrf_token);
      }
      return res.data!;
    },

    async login(data: LoginPayload, options?: RequestOptions): Promise<{ user: User; csrf_token: string }> {
      const res = await request<ApiResponse<{ user: User; csrf_token: string }>>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
        signal: options?.signal,
      });
      if (res.data?.csrf_token) {
        setCsrfToken(res.data.csrf_token);
      }
      return res.data!;
    },

    async logout(options?: RequestOptions): Promise<void> {
      try {
        await request<ApiResponse>('/api/auth/logout', { method: 'POST', signal: options?.signal });
      } finally {
        setCsrfToken(null);
      }
    },

    async me(options?: RequestOptions): Promise<User> {
      const res = await request<ApiResponse<User & { csrf_token?: string }>>('/api/auth/me', {
        method: 'GET',
        signal: options?.signal,
      });
      if (res.data?.csrf_token) {
        setCsrfToken(res.data.csrf_token);
      }
      return res.data!;
    },

    async changePassword(data: ChangePasswordPayload, options?: RequestOptions): Promise<void> {
      await request<ApiResponse>('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify(data),
        signal: options?.signal,
      });
    },
  },

  profile: {
    async get(options?: RequestOptions): Promise<User> {
      const res = await request<ApiResponse<User>>('/api/profile', { method: 'GET', signal: options?.signal });
      return res.data!;
    },

    async update(data: UpdateProfilePayload, options?: RequestOptions): Promise<User> {
      const res = await request<ApiResponse<User>>('/api/profile', {
        method: 'PATCH',
        body: JSON.stringify(data),
        signal: options?.signal,
      });
      return res.data!;
    },

    async deleteAccount(data: DeleteAccountPayload, options?: RequestOptions): Promise<void> {
      await request<ApiResponse>('/api/profile', {
        method: 'DELETE',
        body: JSON.stringify(data),
        signal: options?.signal,
      });
      setCsrfToken(null);
    },
  },

  projects: {
    async list(
      params: { page?: number; pageSize?: number; search?: string; industry?: string } = {},
      options?: RequestOptions
    ): Promise<PaginatedResponse<Project>> {
      const query = new URLSearchParams();
      if (params.page) query.set('page', params.page.toString());
      if (params.pageSize) query.set('page_size', params.pageSize.toString());
      if (params.search) query.set('search', params.search);
      if (params.industry) query.set('industry', params.industry);

      const qs = query.toString();
      return request<PaginatedResponse<Project>>(`/api/projects${qs ? `?${qs}` : ''}`, {
        method: 'GET',
        signal: options?.signal,
      });
    },

    async create(data: CreateProjectPayload, options?: RequestOptions): Promise<Project> {
      const res = await request<ApiResponse<Project>>('/api/projects', {
        method: 'POST',
        body: JSON.stringify(data),
        signal: options?.signal,
      });
      return res.data!;
    },

    async get(id: string, options?: RequestOptions): Promise<Project> {
      const res = await request<ApiResponse<Project>>(`/api/projects/${id}`, { method: 'GET', signal: options?.signal });
      return res.data!;
    },

    async update(id: string, data: UpdateProjectPayload, options?: RequestOptions): Promise<Project> {
      const res = await request<ApiResponse<Project>>(`/api/projects/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
        signal: options?.signal,
      });
      return res.data!;
    },

    async delete(id: string, options?: RequestOptions): Promise<void> {
      await request<ApiResponse>(`/api/projects/${id}`, { method: 'DELETE', signal: options?.signal });
    },
  },

  bmc: {
    async generate(projectId: string, options?: RequestOptions): Promise<Blueprint> {
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/business-model/generate`, {
        method: 'POST',
        signal: options?.signal,
      });
      return res.data!;
    },

    async get(projectId: string, versionOrOptions?: number | RequestOptions, options?: RequestOptions): Promise<Blueprint> {
      let version: number | undefined;
      let opts = options;
      if (typeof versionOrOptions === 'number') {
        version = versionOrOptions;
      } else if (versionOrOptions && typeof versionOrOptions === 'object' && 'signal' in versionOrOptions) {
        opts = versionOrOptions as RequestOptions;
      }
      const qs = version ? `?version=${version}` : '';
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/business-model${qs}`, {
        method: 'GET',
        signal: opts?.signal,
      });
      return res.data!;
    },

    async listVersions(projectId: string, options?: RequestOptions): Promise<BlueprintVersionItem[]> {
      const res = await request<ApiResponse<BlueprintVersionItem[]>>(`/api/projects/${projectId}/business-model/versions`, {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data || [];
    },

    async update(projectId: string, content: BusinessModelCanvasData, options?: RequestOptions): Promise<Blueprint> {
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/business-model`, {
        method: 'PATCH',
        body: JSON.stringify({ content }),
        signal: options?.signal,
      });
      return res.data!;
    },
  },

  techStack: {
    async generate(projectId: string, options?: RequestOptions): Promise<Blueprint> {
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/technology-stack/generate`, {
        method: 'POST',
        signal: options?.signal,
      });
      return res.data!;
    },

    async get(projectId: string, versionOrOptions?: number | RequestOptions, options?: RequestOptions): Promise<Blueprint> {
      let version: number | undefined;
      let opts = options;
      if (typeof versionOrOptions === 'number') {
        version = versionOrOptions;
      } else if (versionOrOptions && typeof versionOrOptions === 'object' && 'signal' in versionOrOptions) {
        opts = versionOrOptions as RequestOptions;
      }
      const qs = version ? `?version=${version}` : '';
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/technology-stack${qs}`, {
        method: 'GET',
        signal: opts?.signal,
      });
      return res.data!;
    },

    async listVersions(projectId: string, options?: RequestOptions): Promise<BlueprintVersionItem[]> {
      const res = await request<ApiResponse<BlueprintVersionItem[]>>(`/api/projects/${projectId}/technology-stack/versions`, {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data || [];
    },

    async update(projectId: string, content: TechnologyStackData, options?: RequestOptions): Promise<Blueprint> {
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/technology-stack`, {
        method: 'PATCH',
        body: JSON.stringify({ content }),
        signal: options?.signal,
      });
      return res.data!;
    },
  },

  generations: {
    async listForProject(projectId: string, options?: RequestOptions): Promise<GenerationRun[]> {
      const res = await request<ApiResponse<GenerationRun[]>>(`/api/projects/${projectId}/generations`, {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data || [];
    },
  },

  exports: {
    getPdfDownloadUrl(projectId: string): string {
      return `/api/projects/${projectId}/export/pdf`;
    },

    async downloadPdf(projectId: string, options?: RequestOptions): Promise<Blob> {
      return request<Blob>(`/api/projects/${projectId}/export/pdf`, { method: 'GET', signal: options?.signal });
    },
  },

  validator: {
    async generate(projectId: string, options?: RequestOptions): Promise<ValidationReportResponse> {
      const res = await request<ApiResponse<ValidationReportResponse>>(`/api/projects/${projectId}/validator/generate`, {
        method: 'POST',
        signal: options?.signal,
      });
      const data = res.data!;
      if (data) {
        if (data.content_json) data.content_json = normalizeValidationReportData(data.content_json)!;
        if (data.content) data.content = normalizeValidationReportData(data.content)!;
      }
      return data;
    },

    async get(projectId: string, versionOrOptions?: number | RequestOptions, options?: RequestOptions): Promise<ValidationReportResponse> {
      let version: number | undefined;
      let opts = options;
      if (typeof versionOrOptions === 'number') {
        version = versionOrOptions;
      } else if (versionOrOptions && typeof versionOrOptions === 'object' && 'signal' in versionOrOptions) {
        opts = versionOrOptions as RequestOptions;
      }
      const qs = version ? `?version=${version}` : '';
      const res = await request<ApiResponse<ValidationReportResponse>>(`/api/projects/${projectId}/validator${qs}`, {
        method: 'GET',
        signal: opts?.signal,
      });
      const data = res.data!;
      if (data) {
        if (data.content_json) data.content_json = normalizeValidationReportData(data.content_json)!;
        if (data.content) data.content = normalizeValidationReportData(data.content)!;
      }
      return data;
    },

    async listVersions(projectId: string, options?: RequestOptions): Promise<BlueprintVersionItem[]> {
      const res = await request<ApiResponse<BlueprintVersionItem[]>>(`/api/projects/${projectId}/validator/versions`, {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data || [];
    },
  },

  marketResearch: {
    async generate(projectId: string, options?: RequestOptions): Promise<MarketResearchResponse> {
      const res = await request<ApiResponse<MarketResearchResponse>>(`/api/projects/${projectId}/market-research/generate`, {
        method: 'POST',
        signal: options?.signal,
      });
      return res.data!;
    },

    async get(projectId: string, versionOrOptions?: number | RequestOptions, options?: RequestOptions): Promise<MarketResearchResponse> {
      let version: number | undefined;
      let opts = options;
      if (typeof versionOrOptions === 'number') {
        version = versionOrOptions;
      } else if (versionOrOptions && typeof versionOrOptions === 'object' && 'signal' in versionOrOptions) {
        opts = versionOrOptions as RequestOptions;
      }
      const qs = version ? `?version=${version}` : '';
      const res = await request<ApiResponse<MarketResearchResponse>>(`/api/projects/${projectId}/market-research${qs}`, {
        method: 'GET',
        signal: opts?.signal,
      });
      return res.data!;
    },

    async listVersions(projectId: string, options?: RequestOptions): Promise<BlueprintVersionItem[]> {
      const res = await request<ApiResponse<BlueprintVersionItem[]>>(`/api/projects/${projectId}/market-research/versions`, {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data || [];
    },
  },

  roadmap: {
    async generate(projectId: string, options?: RequestOptions): Promise<RoadmapResponse> {
      const res = await request<ApiResponse<RoadmapResponse>>(`/api/projects/${projectId}/roadmap/generate`, {
        method: 'POST',
        signal: options?.signal,
      });
      return res.data!;
    },

    async get(projectId: string, options?: RequestOptions): Promise<RoadmapResponse> {
      const res = await request<ApiResponse<RoadmapResponse>>(`/api/projects/${projectId}/roadmap`, {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data!;
    },

    async createTask(projectId: string, task: Partial<RoadmapTask>, options?: RequestOptions): Promise<RoadmapTask> {
      const res = await request<ApiResponse<RoadmapTask>>(`/api/projects/${projectId}/roadmap/tasks`, {
        method: 'POST',
        body: JSON.stringify(task),
        signal: options?.signal,
      });
      return res.data!;
    },

    async updateTask(projectId: string, taskId: string, updates: Partial<RoadmapTask>, options?: RequestOptions): Promise<RoadmapTask> {
      const res = await request<ApiResponse<RoadmapTask>>(`/api/projects/${projectId}/roadmap/tasks/${taskId}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
        signal: options?.signal,
      });
      return res.data!;
    },

    async deleteTask(projectId: string, taskId: string, options?: RequestOptions): Promise<boolean> {
      await request<ApiResponse<any>>(`/api/projects/${projectId}/roadmap/tasks/${taskId}`, {
        method: 'DELETE',
        signal: options?.signal,
      });
      return true;
    },
  },

  copilot: {
    async chat(
      projectId: string,
      payload: { query: string; action_type: 'answer_question' | 'propose_edit'; target_module?: string; target_section?: string },
      options?: RequestOptions
    ): Promise<CopilotChatResponse> {
      const res = await request<ApiResponse<CopilotChatResponse>>(`/api/projects/${projectId}/copilot/chat`, {
        method: 'POST',
        body: JSON.stringify(payload),
        signal: options?.signal,
      });
      return res.data!;
    },

    async acceptProposal(projectId: string, proposalId: string, options?: RequestOptions): Promise<CopilotProposal> {
      const res = await request<ApiResponse<CopilotProposal>>(`/api/projects/${projectId}/copilot/proposals/${proposalId}/accept`, {
        method: 'POST',
        signal: options?.signal,
      });
      return res.data!;
    },

    async rejectProposal(projectId: string, proposalId: string, options?: RequestOptions): Promise<CopilotProposal> {
      const res = await request<ApiResponse<CopilotProposal>>(`/api/projects/${projectId}/copilot/proposals/${proposalId}/reject`, {
        method: 'POST',
        signal: options?.signal,
      });
      return res.data!;
    },

    async listRevisions(projectId: string, options?: RequestOptions): Promise<CopilotRevisionItem[]> {
      const res = await request<ApiResponse<CopilotRevisionItem[]>>(`/api/projects/${projectId}/copilot/revisions`, {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data || [];
    },
  },

  legal: {
    async getDocuments(options?: RequestOptions): Promise<Record<string, any>> {
      const res = await request<ApiResponse<Record<string, any>>>('/api/legal/documents', {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data || {};
    },

    async getStatus(options?: RequestOptions): Promise<Record<string, boolean>> {
      const res = await request<ApiResponse<Record<string, boolean>>>('/api/legal/status', {
        method: 'GET',
        signal: options?.signal,
      });
      return res.data || {};
    },
  },
};
