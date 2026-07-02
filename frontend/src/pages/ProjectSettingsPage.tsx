import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Save, Trash2 } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import {
  getProject,
  updateProject,
  deleteProject,
  listProjectMembers,
} from "@/projects/projectApi";
import type { Project, ProjectVisibility, ProjectStatus, ProjectRole } from "@/projects/types";

const colorPresets = [
  { name: "Indigo", value: "#6366f1" },
  { name: "Blue", value: "#3b82f6" },
  { name: "Emerald", value: "#10b981" },
  { name: "Amber", value: "#f59e0b" },
  { name: "Rose", value: "#f43f5e" },
  { name: "Violet", value: "#8b5cf6" },
  { name: "Zinc", value: "#71717a" },
];

export function ProjectSettingsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { accessToken, user } = useAuth();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [userRole, setUserRole] = useState<ProjectRole | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<ProjectVisibility>("private");
  const [status, setStatus] = useState<ProjectStatus>("active");
  const [selectedColor, setSelectedColor] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Delete state
  const [confirmSlug, setConfirmSlug] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    async function loadProjectDetails() {
      if (!accessToken || !projectId) {
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const [projData, membersData] = await Promise.all([
          getProject(accessToken, projectId),
          listProjectMembers(accessToken, projectId),
        ]);

        setProject(projData);
        setName(projData.name);
        setDescription(projData.description || "");
        setVisibility(projData.visibility);
        setStatus(projData.status);
        setSelectedColor(projData.color || colorPresets[0].value);

        const selfMember = membersData.find((m) => m.user_id === user?.id);
        setUserRole(selfMember?.role ?? null);
      } catch (err) {
        console.error("Failed to load project settings", err);
        setError("Failed to load project settings.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadProjectDetails();
  }, [accessToken, projectId, user]);

  const isOwner = userRole === "owner";
  const isMaintainer = userRole === "maintainer" || isOwner;

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken || !projectId || !isMaintainer) {
      return;
    }
    setIsSubmitting(true);
    setSubmitSuccess(false);
    setError(null);
    try {
      const payload: {
        name: string;
        description: string | null;
        color: string;
        visibility?: ProjectVisibility;
        status?: ProjectStatus;
      } = {
        name,
        description: description || null,
        color: selectedColor,
      };

      // Only owner can update visibility & status
      if (isOwner) {
        payload.visibility = visibility;
        payload.status = status;
      }

      const updated = await updateProject(accessToken, projectId, payload);
      setProject(updated);
      setSubmitSuccess(true);
    } catch (err) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      setError(errorObj.response?.data?.detail ?? "Failed to update project settings.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!accessToken || !projectId || !isOwner || !project) {
      return;
    }
    if (confirmSlug !== project.slug) {
      alert("Project slug does not match.");
      return;
    }
    setIsDeleting(true);
    try {
      await deleteProject(accessToken, projectId);
      navigate("/projects");
    } catch {
      alert("Failed to delete project.");
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex h-64 items-center justify-center">
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !project || !isMaintainer) {
    return (
      <DashboardLayout>
        <div className="space-y-4">
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-700/10">
            {error ||
              (!isMaintainer
                ? "Access denied. You must be a project maintainer."
                : "Project not found.")}
          </div>
          <Link to="/projects">
            <Button>
              <ArrowLeft className="mr-2 size-4" /> Back to Projects
            </Button>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link to={`/projects/${project.id}`}>
            <Button variant="ghost" size="icon">
              <ArrowLeft className="size-4" />
            </Button>
          </Link>
          <div>
            <h2 className="font-display text-3xl font-semibold tracking-tight">Project Settings</h2>
            <p className="text-sm text-muted-foreground">Configure details for {project.name}</p>
          </div>
        </div>

        <form onSubmit={handleUpdate} className="space-y-6 max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {submitSuccess && (
                <div className="rounded-md bg-emerald-50 p-4 text-sm text-emerald-700 ring-1 ring-emerald-700/10">
                  Settings updated successfully.
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="settings-name" className="text-sm font-medium">
                  Project Name
                </label>
                <input
                  id="settings-name"
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="settings-description" className="text-sm font-medium">
                  Description
                </label>
                <textarea
                  id="settings-description"
                  className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              {isOwner ? (
                <>
                  <div className="space-y-2">
                    <label htmlFor="settings-visibility" className="text-sm font-medium">
                      Visibility
                    </label>
                    <select
                      id="settings-visibility"
                      value={visibility}
                      onChange={(e) => setVisibility(e.target.value as ProjectVisibility)}
                      className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                    >
                      <option value="private">Private (Only project members can access)</option>
                      <option value="public">Public (Everyone in organization can access)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="settings-status" className="text-sm font-medium">
                      Status
                    </label>
                    <select
                      id="settings-status"
                      value={status}
                      onChange={(e) => setStatus(e.target.value as ProjectStatus)}
                      className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                    >
                      <option value="active">Active</option>
                      <option value="archived">Archived</option>
                    </select>
                  </div>
                </>
              ) : (
                <div className="rounded-md bg-yellow-50 p-4 text-xs text-yellow-800 border border-yellow-200">
                  Only the project owner can change project visibility or status.
                </div>
              )}

              <div className="space-y-2">
                <span className="text-sm font-medium block">Project Color Accent</span>
                <div className="flex gap-2">
                  {colorPresets.map((preset) => (
                    <button
                      key={preset.value}
                      type="button"
                      onClick={() => setSelectedColor(preset.value)}
                      className="size-8 rounded-full border-2 transition-transform focus:outline-none"
                      style={{
                        backgroundColor: preset.value,
                        borderColor: selectedColor === preset.value ? "#000" : "transparent",
                        transform: selectedColor === preset.value ? "scale(1.1)" : "scale(1)",
                      }}
                      title={preset.name}
                      aria-label={`Select ${preset.name} color`}
                    />
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <Button type="submit" disabled={isSubmitting}>
                  <Save className="mr-2 size-4" />
                  {isSubmitting ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>

        {isOwner && (
          <Card className="max-w-2xl border-red-200 bg-red-50/5">
            <CardHeader>
              <CardTitle className="text-red-700">Danger Zone</CardTitle>
              <CardDescription>
                Permanently delete this project and all its members. This action cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="confirm-slug" className="text-sm font-medium text-red-900">
                  Please type <span className="font-mono font-bold">{project.slug}</span> to
                  confirm.
                </label>
                <input
                  id="confirm-slug"
                  className="h-10 w-full rounded-md border border-red-300 bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-red-500"
                  value={confirmSlug}
                  onChange={(e) => setConfirmSlug(e.target.value)}
                  placeholder={project.slug}
                />
              </div>

              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={confirmSlug !== project.slug || isDeleting}
              >
                <Trash2 className="mr-2 size-4" />
                {isDeleting ? "Deleting..." : "Permanently Delete Project"}
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
