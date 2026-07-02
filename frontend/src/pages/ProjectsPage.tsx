import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Folder, Plus, Search, Eye, EyeOff, Archive, CheckCircle } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useOrganizations } from "@/organizations/OrganizationContext";
import { listProjects } from "@/projects/projectApi";
import type { Project } from "@/projects/types";

export function ProjectsPage() {
  const { accessToken } = useAuth();
  const { activeOrganization } = useOrganizations();
  const [projects, setProjects] = useState<Project[]>([]);
  const [search, setSearch] = useState("");
  const [filterVisibility, setFilterVisibility] = useState<"all" | "public" | "private">("all");
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "archived">("all");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    async function loadProjects() {
      if (!accessToken || !activeOrganization) {
        setProjects([]);
        return;
      }
      setIsLoading(true);
      try {
        const data = await listProjects(accessToken);
        setProjects(data);
      } catch (err) {
        console.error("Failed to load projects", err);
      } finally {
        setIsLoading(false);
      }
    }

    void loadProjects();
  }, [accessToken, activeOrganization]);

  const filteredProjects = projects.filter((project) => {
    const matchesSearch =
      project.name.toLowerCase().includes(search.toLowerCase()) ||
      project.slug.toLowerCase().includes(search.toLowerCase()) ||
      (project.description && project.description.toLowerCase().includes(search.toLowerCase()));

    const matchesVisibility = filterVisibility === "all" || project.visibility === filterVisibility;

    const matchesStatus = filterStatus === "all" || project.status === filterStatus;

    return matchesSearch && matchesVisibility && matchesStatus;
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-display text-3xl font-semibold tracking-tight">Projects</h2>
            <p className="text-sm text-muted-foreground">
              Manage organization projects and members.
            </p>
          </div>
          <Link to="/projects/new">
            <Button className="w-full sm:w-auto">
              <Plus className="mr-2 size-4" />
              New Project
            </Button>
          </Link>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4 md:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-3 size-4 text-muted-foreground" />
                <input
                  className="h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search projects..."
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={filterVisibility}
                  onChange={(e) =>
                    setFilterVisibility(e.target.value as "all" | "public" | "private")
                  }
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="all">All Visibilities</option>
                  <option value="public">Public</option>
                  <option value="private">Private</option>
                </select>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as "all" | "active" | "archived")}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="all">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {isLoading ? (
          <div className="flex h-32 items-center justify-center">
            <p className="text-muted-foreground">Loading projects...</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredProjects.map((project) => (
              <Card
                key={project.id}
                className="overflow-hidden border-t-4 transition-shadow hover:shadow-md"
                style={{ borderTopColor: project.color || "#cbd5e1" }}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <div className="grid size-10 place-items-center rounded-md bg-secondary text-secondary-foreground">
                        <Folder className="size-5" />
                      </div>
                      <div>
                        <h3 className="font-semibold leading-none">{project.name}</h3>
                        <p className="mt-1 text-xs text-muted-foreground">/{project.slug}</p>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      {project.visibility === "public" ? (
                        <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10">
                          <Eye className="mr-1 size-3" /> Public
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-700/10">
                          <EyeOff className="mr-1 size-3" /> Private
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="mt-4 min-h-[40px] text-sm text-muted-foreground line-clamp-2">
                    {project.description || "No description provided."}
                  </p>

                  <div className="mt-5 flex items-center justify-between border-t border-border pt-4">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      {project.status === "active" ? (
                        <span className="flex items-center gap-1 text-emerald-600">
                          <CheckCircle className="size-3" /> Active
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-zinc-500">
                          <Archive className="size-3" /> Archived
                        </span>
                      )}
                    </div>
                    <Link to={`/projects/${project.id}`}>
                      <Button variant="outline" size="sm">
                        Details
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}

            {filteredProjects.length === 0 ? (
              <div className="col-span-full rounded-lg border border-dashed border-border p-12 text-center">
                <Folder className="mx-auto size-12 text-muted-foreground" />
                <h3 className="mt-4 text-lg font-semibold">No projects found</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Get started by creating a new project in this workspace.
                </p>
                <Link to="/projects/new" className="mt-4 inline-block">
                  <Button size="sm">
                    <Plus className="mr-2 size-4" /> Create Project
                  </Button>
                </Link>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
