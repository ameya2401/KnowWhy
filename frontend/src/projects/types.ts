export type ProjectRole = "owner" | "maintainer" | "contributor" | "viewer";
export type ProjectVisibility = "public" | "private";
export type ProjectStatus = "active" | "archived";

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  visibility: ProjectVisibility;
  status: ProjectStatus;
  color: string | null;
  icon: string | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: ProjectRole;
  joined_at: string;
  full_name: string;
  email: string;
  profile_picture_url: string | null;
}

export interface ProjectCreatePayload {
  name: string;
  slug: string;
  description?: string | null;
  visibility?: ProjectVisibility;
  status?: ProjectStatus;
  color?: string | null;
  icon?: string | null;
}

export interface ProjectMemberInvitePayload {
  email: string;
  role: ProjectRole;
}
