import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Settings,
  Users,
  Info,
  Archive,
  UserPlus,
  Trash2,
  Shield,
  Link2,
  Database,
  Cpu,
  Brain,
  MessageSquare,
  GitBranch,
} from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import {
  getProject,
  archiveProject,
  listProjectMembers,
  inviteProjectMember,
  updateProjectMemberRole,
  removeProjectMember,
} from "@/projects/projectApi";
import type { Project, ProjectMember, ProjectRole } from "@/projects/types";
import { ProjectIntegrations } from "@/components/ProjectIntegrations";
import { KnowledgeBrowser } from "@/components/KnowledgeBrowser";
import { EmbeddingControls } from "@/components/EmbeddingControls";
import { AIDebugDashboard } from "@/components/AIDebugDashboard";
import { AIChatAssistant } from "@/components/AIChatAssistant";
import { KnowledgeGraphAndTimeline } from "@/components/KnowledgeGraphAndTimeline";
import { EngineeringIntelligence } from "@/components/EngineeringIntelligence";

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { accessToken, user } = useAuth();

  const [project, setProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [activeTab, setActiveTab] = useState<
    "overview" | "members" | "integrations" | "knowledge" | "embeddings" | "assistant" | "ai" | "graph_timeline" | "intelligence"
  >("overview");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Invite state
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<ProjectRole>("viewer");
  const [isInviting, setIsInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
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
        setMembers(membersData);
      } catch (err) {
        console.error("Failed to load project details", err);
        setError("Failed to load project details.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadData();
  }, [accessToken, projectId]);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex h-64 items-center justify-center">
          <p className="text-muted-foreground">Loading project details...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !project) {
    return (
      <DashboardLayout>
        <div className="space-y-4">
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-700/10">
            {error || "Project not found."}
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

  // Find user's role in this project
  const userMember = members.find((m) => m.user_id === user?.id);
  const userRole = userMember?.role;
  const isOwner = userRole === "owner";
  const isMaintainer = userRole === "maintainer" || isOwner;

  const handleArchive = async () => {
    if (!accessToken || !projectId) {
      return;
    }
    if (!confirm("Are you sure you want to archive this project?")) {
      return;
    }
    try {
      const updated = await archiveProject(accessToken, projectId);
      setProject(updated);
    } catch {
      alert("Failed to archive project.");
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken || !projectId || !inviteEmail) {
      return;
    }
    setIsInviting(true);
    setInviteError(null);
    try {
      const newMember = await inviteProjectMember(accessToken, projectId, {
        email: inviteEmail,
        role: inviteRole,
      });
      setMembers((prev) => [...prev, newMember]);
      setInviteEmail("");
      setInviteRole("viewer");
    } catch (err) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      setInviteError(errorObj.response?.data?.detail ?? "Failed to invite member.");
    } finally {
      setIsInviting(false);
    }
  };

  const handleRoleChange = async (membershipId: string, role: ProjectRole) => {
    if (!accessToken || !projectId) {
      return;
    }
    try {
      const updated = await updateProjectMemberRole(accessToken, projectId, membershipId, role);
      setMembers((prev) => prev.map((m) => (m.id === membershipId ? updated : m)));
    } catch {
      alert("Failed to update role.");
    }
  };

  const handleRemoveMember = async (membershipId: string, memberName: string) => {
    if (!accessToken || !projectId) {
      return;
    }
    if (!confirm(`Are you sure you want to remove ${memberName} from this project?`)) {
      return;
    }
    try {
      await removeProjectMember(accessToken, projectId, membershipId);
      setMembers((prev) => prev.filter((m) => m.id !== membershipId));
    } catch {
      alert("Failed to remove member.");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Link to="/projects">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="size-4" />
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-display text-3xl font-semibold tracking-tight">
                  {project.name}
                </h2>
                <span
                  className="size-3 rounded-full"
                  style={{ backgroundColor: project.color || "#6366f1" }}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                /{project.slug} • {project.visibility}
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            {isMaintainer && (
              <Link to={`/projects/${project.id}/settings`}>
                <Button variant="outline">
                  <Settings className="mr-2 size-4" /> Settings
                </Button>
              </Link>
            )}
            {isOwner && project.status === "active" && (
              <Button variant="outline" onClick={handleArchive}>
                <Archive className="mr-2 size-4" /> Archive
              </Button>
            )}
          </div>
        </div>

        {/* Tab Headers */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "overview"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Info className="size-4" /> Overview
          </button>
          <button
            onClick={() => setActiveTab("members")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "members"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Users className="size-4" /> Members ({members.length})
          </button>
          <button
            onClick={() => setActiveTab("integrations")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "integrations"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Link2 className="size-4" /> Integrations
          </button>
          <button
            onClick={() => setActiveTab("knowledge")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "knowledge"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Database className="size-4" /> Knowledge Base
          </button>
          <button
            onClick={() => setActiveTab("embeddings")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "embeddings"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Cpu className="size-4" /> Semantic Indexing
          </button>
          <button
            onClick={() => setActiveTab("assistant")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "assistant"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <MessageSquare className="size-4" /> AI Assistant
          </button>
          <button
            onClick={() => setActiveTab("ai")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "ai"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Brain className="size-4" /> Intelligence Engine
          </button>
          <button
            onClick={() => setActiveTab("intelligence")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "intelligence"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Shield className="size-4" /> Engineering Intelligence
          </button>
          <button
            onClick={() => setActiveTab("graph_timeline")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === "graph_timeline"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <GitBranch className="size-4" /> Graph & Timeline
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
            <Card>
              <CardHeader>
                <CardTitle>Project Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Description
                  </h4>
                  <p className="mt-1 text-sm text-foreground">
                    {project.description || "No description provided."}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Status
                    </h4>
                    <p className="mt-1 text-sm font-medium capitalize">{project.status}</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Visibility
                    </h4>
                    <p className="mt-1 text-sm font-medium capitalize">{project.visibility}</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Created At
                    </h4>
                    <p className="mt-1 text-sm font-medium">
                      {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Your Role
                    </h4>
                    <p className="mt-1 text-sm font-medium capitalize">{userRole || "Viewer"}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Team Size</span>
                  <span className="font-medium">{members.length} members</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Visibility</span>
                  <span className="font-medium capitalize">{project.visibility}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "members" && (
          <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
            <Card>
              <CardHeader>
                <CardTitle>Project Members</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between rounded-md border border-border p-3"
                  >
                    <div className="flex items-center gap-3">
                      {member.profile_picture_url ? (
                        <img
                          src={member.profile_picture_url}
                          alt={member.full_name}
                          className="size-9 rounded-full"
                        />
                      ) : (
                        <div className="grid size-9 place-items-center rounded-full bg-secondary text-secondary-foreground text-sm font-bold">
                          {member.full_name.charAt(0)}
                        </div>
                      )}
                      <div>
                        <p className="font-medium">{member.full_name}</p>
                        <p className="text-xs text-muted-foreground">{member.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {isOwner && member.user_id !== user?.id ? (
                        <select
                          value={member.role}
                          onChange={(e) =>
                            handleRoleChange(member.id, e.target.value as ProjectRole)
                          }
                          className="h-8 rounded-md border border-input bg-background px-2 text-xs outline-none focus:ring-1 focus:ring-ring"
                        >
                          <option value="owner">Owner</option>
                          <option value="maintainer">Maintainer</option>
                          <option value="contributor">Contributor</option>
                          <option value="viewer">Viewer</option>
                        </select>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2 py-1 text-xs font-medium capitalize text-secondary-foreground">
                          <Shield className="size-3" /> {member.role}
                        </span>
                      )}

                      {isOwner && member.user_id !== user?.id && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemoveMember(member.id, member.full_name)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {isMaintainer && (
              <Card>
                <CardHeader>
                  <CardTitle>Invite Member</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleInvite} className="space-y-4">
                    {inviteError && (
                      <div className="rounded-md bg-red-50 p-3 text-xs text-red-700 ring-1 ring-red-700/10">
                        {inviteError}
                      </div>
                    )}
                    <div className="space-y-2">
                      <label
                        htmlFor="invite-email"
                        className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                      >
                        Email Address
                      </label>
                      <input
                        id="invite-email"
                        type="email"
                        className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="user@example.com"
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <label
                        htmlFor="invite-role"
                        className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block"
                      >
                        Project Role
                      </label>
                      <select
                        id="invite-role"
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value as ProjectRole)}
                        className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                      >
                        <option value="viewer">Viewer (Read-only)</option>
                        <option value="contributor">Contributor (Normal write)</option>
                        <option value="maintainer">Maintainer (Manage details)</option>
                        <option value="owner">Owner (Full control)</option>
                      </select>
                    </div>

                    <Button type="submit" className="w-full" disabled={isInviting || !inviteEmail}>
                      <UserPlus className="mr-2 size-4" />
                      {isInviting ? "Inviting..." : "Invite Member"}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {activeTab === "integrations" && projectId && accessToken && (
          <ProjectIntegrations
            projectId={projectId}
            accessToken={accessToken}
            isMaintainer={isMaintainer}
          />
        )}

        {activeTab === "knowledge" && projectId && accessToken && (
          <KnowledgeBrowser projectId={projectId} accessToken={accessToken} />
        )}

        {activeTab === "embeddings" && projectId && accessToken && (
          <EmbeddingControls
            projectId={projectId}
            accessToken={accessToken}
            isMaintainer={isMaintainer}
          />
        )}

        {activeTab === "assistant" && projectId && accessToken && (
          <AIChatAssistant
            projectId={projectId}
            accessToken={accessToken}
            isMaintainer={isMaintainer}
          />
        )}

        {activeTab === "ai" && projectId && accessToken && (
          <AIDebugDashboard
            projectId={projectId}
            accessToken={accessToken}
            isMaintainer={isMaintainer}
          />
        )}

        {activeTab === "intelligence" && projectId && accessToken && (
          <EngineeringIntelligence
            projectId={projectId}
            accessToken={accessToken}
            isMaintainer={isMaintainer}
          />
        )}

        {activeTab === "graph_timeline" && projectId && (
          <KnowledgeGraphAndTimeline projectId={projectId} />
        )}
      </div>
    </DashboardLayout>
  );
}
