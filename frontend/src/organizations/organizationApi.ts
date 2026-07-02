import { apiClient } from "@/services/apiClient";
import type { Organization, OrganizationListItem, OrganizationMember } from "@/organizations/types";

export interface OrganizationCreatePayload {
  name: string;
  slug: string;
  logo_url?: string | null;
  description?: string | null;
}

export async function listOrganizations(accessToken: string): Promise<OrganizationListItem[]> {
  const response = await apiClient.get<OrganizationListItem[]>("/organizations", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function createOrganization(
  accessToken: string,
  payload: OrganizationCreatePayload,
): Promise<Organization> {
  const response = await apiClient.post<Organization>("/organizations", payload, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function updateOrganization(
  accessToken: string,
  organizationId: string,
  payload: Partial<OrganizationCreatePayload>,
): Promise<Organization> {
  const response = await apiClient.put<Organization>(`/organizations/${organizationId}`, payload, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function setActiveOrganization(
  accessToken: string,
  organizationId: string,
): Promise<void> {
  await apiClient.put(
    "/organizations/active",
    { organization_id: organizationId },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
}

export async function listMembers(
  accessToken: string,
  organizationId: string,
): Promise<OrganizationMember[]> {
  const response = await apiClient.get<OrganizationMember[]>(
    `/organizations/${organizationId}/members`,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    },
  );
  return response.data;
}
