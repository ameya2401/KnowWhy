import { createContext, useContext } from "react";

import type { OrganizationCreatePayload } from "@/organizations/organizationApi";
import type { OrganizationListItem } from "@/organizations/types";

export interface OrganizationContextValue {
  organizations: OrganizationListItem[];
  activeOrganization: OrganizationListItem | null;
  isLoading: boolean;
  refreshOrganizations: () => Promise<void>;
  createWorkspace: (payload: OrganizationCreatePayload) => Promise<void>;
  switchWorkspace: (organizationId: string) => Promise<void>;
}

export const OrganizationContext = createContext<OrganizationContextValue | undefined>(undefined);

export function useOrganizations() {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error("useOrganizations must be used within OrganizationProvider.");
  }
  return context;
}
