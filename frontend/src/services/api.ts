/**
 * Centralized API client for AI Business Architect.
 * Uses relative URLs and HTTP-only session cookies with CSRF validation.
 */

import {
  ApiResponse,
  Blueprint,
  BlueprintVersionItem,
  BusinessModelCanvasData,
  GenerationRun,
  PaginatedResponse,
  Project,
  TechnologyStackData,
  User,
} from '../types';

let currentCsrfToken: string | null = null;

export function setCsrfToken(token: string | null) {
  currentCsrfToken = token;
}

export function getCsrfToken(): string | null {
  return currentCsrfToken;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(message: string, code: string = 'API_ERROR', status: number = 400, details?: any) {
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
    async register(data: any): Promise<{ user: User; csrf_token: string }> {
      const res = await request<ApiResponse<{ user: User; csrf_token: string }>>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      if (res.data?.csrf_token) {
        setCsrfToken(res.data.csrf_token);
      }
      return res.data!;
    },

    async login(data: any): Promise<{ user: User; csrf_token: string }> {
      const res = await request<ApiResponse<{ user: User; csrf_token: string }>>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      if (res.data?.csrf_token) {
        setCsrfToken(res.data.csrf_token);
      }
      return res.data!;
    },

    async logout(): Promise<void> {
      await request<ApiResponse>('/api/auth/logout', { method: 'POST' });
      setCsrfToken(null);
    },

    async me(): Promise<User> {
      const res = await request<ApiResponse<User>>('/api/auth/me', { method: 'GET' });
      return res.data!;
    },

    async changePassword(data: any): Promise<void> {
      await request<ApiResponse>('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
  },

  profile: {
    async get(): Promise<User> {
      const res = await request<ApiResponse<User>>('/api/profile', { method: 'GET' });
      return res.data!;
    },

    async update(data: any): Promise<User> {
      const res = await request<ApiResponse<User>>('/api/profile', {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return res.data!;
    },

    async deleteAccount(data: any): Promise<void> {
      await request<ApiResponse>('/api/profile', {
        method: 'DELETE',
        body: JSON.stringify(data),
      });
      setCsrfToken(null);
    },
  },

  projects: {
    async list(params: { page?: number; pageSize?: number; search?: string; industry?: string } = {}): Promise<PaginatedResponse<Project>> {
      const query = new URLSearchParams();
      if (params.page) query.set('page', params.page.toString());
      if (params.pageSize) query.set('page_size', params.pageSize.toString());
      if (params.search) query.set('search', params.search);
      if (params.industry) query.set('industry', params.industry);

      const qs = query.toString();
      return request<PaginatedResponse<Project>>(`/api/projects${qs ? `?${qs}` : ''}`, { method: 'GET' });
    },

    async create(data: any): Promise<Project> {
      const res = await request<ApiResponse<Project>>('/api/projects', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return res.data!;
    },

    async get(id: string): Promise<Project> {
      const res = await request<ApiResponse<Project>>(`/api/projects/${id}`, { method: 'GET' });
      return res.data!;
    },

    async update(id: string, data: any): Promise<Project> {
      const res = await request<ApiResponse<Project>>(`/api/projects/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return res.data!;
    },

    async delete(id: string): Promise<void> {
      await request<ApiResponse>(`/api/projects/${id}`, { method: 'DELETE' });
    },
  },

  bmc: {
    async generate(projectId: string): Promise<Blueprint> {
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/business-model/generate`, {
        method: 'POST',
      });
      return res.data!;
    },

    async get(projectId: string, version?: number): Promise<Blueprint> {
      const qs = version ? `?version=${version}` : '';
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/business-model${qs}`, {
        method: 'GET',
      });
      return res.data!;
    },

    async listVersions(projectId: string): Promise<BlueprintVersionItem[]> {
      const res = await request<ApiResponse<BlueprintVersionItem[]>>(`/api/projects/${projectId}/business-model/versions`, {
        method: 'GET',
      });
      return res.data || [];
    },

    async update(projectId: string, content: BusinessModelCanvasData): Promise<Blueprint> {
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/business-model`, {
        method: 'PATCH',
        body: JSON.stringify({ content }),
      });
      return res.data!;
    },
  },

  techStack: {
    async generate(projectId: string): Promise<Blueprint> {
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/technology-stack/generate`, {
        method: 'POST',
      });
      return res.data!;
    },

    async get(projectId: string, version?: number): Promise<Blueprint> {
      const qs = version ? `?version=${version}` : '';
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/technology-stack${qs}`, {
        method: 'GET',
      });
      return res.data!;
    },

    async listVersions(projectId: string): Promise<BlueprintVersionItem[]> {
      const res = await request<ApiResponse<BlueprintVersionItem[]>>(`/api/projects/${projectId}/technology-stack/versions`, {
        method: 'GET',
      });
      return res.data || [];
    },

    async update(projectId: string, content: TechnologyStackData): Promise<Blueprint> {
      const res = await request<ApiResponse<Blueprint>>(`/api/projects/${projectId}/technology-stack`, {
        method: 'PATCH',
        body: JSON.stringify({ content }),
      });
      return res.data!;
    },
  },

  generations: {
    async listForProject(projectId: string): Promise<GenerationRun[]> {
      const res = await request<ApiResponse<GenerationRun[]>>(`/api/projects/${projectId}/generations`, {
        method: 'GET',
      });
      return res.data || [];
    },
  },

  exports: {
    getPdfDownloadUrl(projectId: string): string {
      return `/api/projects/${projectId}/export/pdf`;
    },

    async downloadPdf(projectId: string): Promise<Blob> {
      return request<Blob>(`/api/projects/${projectId}/export/pdf`, { method: 'GET' });
    },
  },

  legal: {
    async getDocuments(): Promise<Record<string, any>> {
      const res = await request<ApiResponse<Record<string, any>>>('/api/legal/documents', { method: 'GET' });
      return res.data || {};
    },

    async getStatus(): Promise<Record<string, boolean>> {
      const res = await request<ApiResponse<Record<string, boolean>>>('/api/legal/status', { method: 'GET' });
      return res.data || {};
    },
  },
};
