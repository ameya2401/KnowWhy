import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useOrganizations } from "@/organizations/OrganizationContext";
import { listProjects } from "@/projects/projectApi";
import type { Project } from "@/projects/types";
import { ProjectContext } from "./ProjectContext";

export function ProjectProvider({ children }: { children: ReactNode }) {
  const { accessToken, isAuthenticated } = useAuth();
  const { activeOrganization } = useOrganizations();

  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const orgId = activeOrganization?.organization.id ?? null;

  const refreshProjects = useCallback(async () => {
    if (!accessToken || !isAuthenticated || !orgId) {
      setProjects([]);
      setActiveProjectId(null);
      return;
    }
    setIsLoading(true);
    try {
      const list = await listProjects(accessToken);
      setProjects(list);

      // Check localStorage for previously active project in this org
      const savedProjId = localStorage.getItem(`knowwhy:active_project:${orgId}`);
      if (savedProjId && list.some((p) => p.id === savedProjId)) {
        setActiveProjectId(savedProjId);
      } else {
        // Default to first project if available
        setActiveProjectId(list[0]?.id ?? null);
      }
    } catch (err) {
      console.error("Failed to fetch projects", err);
      setProjects([]);
      setActiveProjectId(null);
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, isAuthenticated, orgId]);

  useEffect(() => {
    void refreshProjects();
  }, [refreshProjects]);

  const switchProject = useCallback(
    (projectId: string) => {
      if (orgId) {
        localStorage.setItem(`knowwhy:active_project:${orgId}`, projectId);
      }
      setActiveProjectId(projectId);
    },
    [orgId],
  );

  const activeProject = useMemo(
    () => projects.find((p) => p.id === activeProjectId) ?? projects[0] ?? null,
    [activeProjectId, projects],
  );

  const value = useMemo(
    () => ({
      projects,
      activeProject,
      isLoading,
      refreshProjects,
      switchProject,
    }),
    [projects, activeProject, isLoading, refreshProjects, switchProject],
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}
