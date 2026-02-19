export interface Project {
  id: string;
  name: string;
  number: string;
  client: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Revision {
  id: string;
  revision_number: number;
  status: string;
  created_at: string | null;
}

export interface Artifact {
  id: string;
  revision_id: string;
  artifact_type: string;
  filename: string;
  file_path: string;
  file_size: number;
  sheet_number: string;
  description: string;
  created_at: string;
}

export interface QCIssue {
  id: string;
  severity: string;
  category: string;
  message: string;
  element_id: string;
}

export interface RoomRequirement {
  name: string;
  function: string;
  area: number;
  count: number;
  adjacencies: string[];
  must_have_window: boolean | null;
}

export interface GenerationConfig {
  formats: string[];
  paper_size: string;
  scale: string;
  seed: number;
  include_schedules: boolean;
  include_qc: boolean;
}

export interface GenerationStatus {
  revision_id: string;
  status: string;
  progress: number;
  message: string;
  artifacts_count: number;
  qc_issues_count: number;
}

export interface DemoResult {
  status: string;
  project_name: string;
  rooms: number;
  walls: number;
  doors: number;
  windows: number;
  sheets: number;
  files: string[];
  qc_issues: string[];
  output_dir: string;
  zip_path: string | null;
}
