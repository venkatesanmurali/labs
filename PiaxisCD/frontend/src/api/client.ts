const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Projects
  listProjects: () => request<{ projects: import('../types').Project[]; total: number }>('/projects'),
  createProject: (data: { name: string; number?: string; client?: string; description?: string }) =>
    request<import('../types').Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  getProject: (id: string) => request<import('../types').Project>(`/projects/${id}`),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),

  // Requirements
  submitRequirements: (projectId: string, data: { rooms: import('../types').RoomRequirement[] }) =>
    request<{ id: string }>(`/projects/${projectId}/inputs/requirements`, { method: 'POST', body: JSON.stringify(data) }),
  submitRequirementsText: (projectId: string, text: string) =>
    request<{ id: string }>(`/projects/${projectId}/inputs/requirements-text`, { method: 'POST', body: JSON.stringify({ text }) }),

  // Generation
  generate: (projectId: string, config?: Partial<import('../types').GenerationConfig>) =>
    request<import('../types').GenerationStatus>(`/projects/${projectId}/generate`, {
      method: 'POST',
      body: JSON.stringify({ config: config || {} }),
    }),
  listRevisions: (projectId: string) =>
    request<{ revisions: import('../types').Revision[] }>(`/projects/${projectId}/revisions`),

  // Artifacts
  listArtifacts: (projectId: string, revisionId: string) =>
    request<{ artifacts: import('../types').Artifact[] }>(`/projects/${projectId}/revisions/${revisionId}/artifacts`),
  listQCIssues: (projectId: string, revisionId: string) =>
    request<{ qc_issues: import('../types').QCIssue[] }>(`/projects/${projectId}/revisions/${revisionId}/qc-issues`),
  downloadUrl: (projectId: string, revisionId: string) =>
    `${BASE}/projects/${projectId}/revisions/${revisionId}/download`,
  artifactDownloadUrl: (projectId: string, revisionId: string, artifactId: string) =>
    `${BASE}/projects/${projectId}/revisions/${revisionId}/artifacts/${artifactId}/download`,

  // Demo
  runDemo: (seed?: number) =>
    request<import('../types').DemoResult>(`/demo?seed=${seed || 42}`, { method: 'POST' }),
};
