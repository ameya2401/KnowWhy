import { createContext, useContext } from "react";
import type { Project } from "./types";

export interface ProjectContextValue {
  projects: Project[];
  activeProject: Project | null;
  isLoading: boolean;
  refreshProjects: () => Promise<void>;
  switchProject: (projectId: string) => void;
}

export const ProjectContext = createContext<ProjectContextValue | undefined>(undefined);

export function useProjects() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error("useProjects must be used within ProjectProvider.");
  }
  return context;
}
