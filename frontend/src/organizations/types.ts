export type OrganizationRole = "owner" | "admin" | "member";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  logo_url: string | null;
  description: string | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface OrganizationListItem {
  organization: Organization;
  role: OrganizationRole;
}

export interface OrganizationMember {
  id: string;
  user_id: string;
  organization_id: string;
  role: OrganizationRole;
  joined_at: string;
  full_name: string;
  email: string;
  profile_picture_url: string | null;
}
