import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { useAuth } from "@/auth/AuthContext";
import { OrganizationContext } from "@/organizations/OrganizationContext";
import {
  createOrganization,
  listOrganizations,
  setActiveOrganization,
  type OrganizationCreatePayload,
} from "@/organizations/organizationApi";
import type { OrganizationListItem } from "@/organizations/types";

export function OrganizationProvider({ children }: { children: ReactNode }) {
  const { accessToken, isAuthenticated } = useAuth();
  const [organizations, setOrganizations] = useState<OrganizationListItem[]>([]);
  const [activeOrganizationId, setActiveOrganizationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshOrganizations = useCallback(async () => {
    if (!accessToken || !isAuthenticated) {
      setOrganizations([]);
      setActiveOrganizationId(null);
      return;
    }
    setIsLoading(true);
    try {
      const nextOrganizations = await listOrganizations(accessToken);
      setOrganizations(nextOrganizations);
      setActiveOrganizationId((current) => {
        if (current && nextOrganizations.some((item) => item.organization.id === current)) {
          return current;
        }
        return nextOrganizations[0]?.organization.id ?? null;
      });
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, isAuthenticated]);

  useEffect(() => {
    void refreshOrganizations();
  }, [refreshOrganizations]);

  const switchWorkspace = useCallback(
    async (organizationId: string) => {
      if (!accessToken) {
        return;
      }
      await setActiveOrganization(accessToken, organizationId);
      setActiveOrganizationId(organizationId);
    },
    [accessToken],
  );

  const createWorkspace = useCallback(
    async (payload: OrganizationCreatePayload) => {
      if (!accessToken) {
        return;
      }
      const organization = await createOrganization(accessToken, payload);
      await refreshOrganizations();
      setActiveOrganizationId(organization.id);
    },
    [accessToken, refreshOrganizations],
  );

  const activeOrganization = useMemo(
    () =>
      organizations.find((item) => item.organization.id === activeOrganizationId) ??
      organizations[0] ??
      null,
    [activeOrganizationId, organizations],
  );

  const value = useMemo(
    () => ({
      organizations,
      activeOrganization,
      isLoading,
      refreshOrganizations,
      createWorkspace,
      switchWorkspace,
    }),
    [
      activeOrganization,
      createWorkspace,
      isLoading,
      organizations,
      refreshOrganizations,
      switchWorkspace,
    ],
  );

  return <OrganizationContext.Provider value={value}>{children}</OrganizationContext.Provider>;
}
