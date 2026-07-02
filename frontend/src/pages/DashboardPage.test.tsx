import { render, screen, waitFor } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardPage } from "@/pages/DashboardPage";
import { getGitHubDashboard } from "@/services/integrationApi";

// Mock auth context
vi.mock("@/auth/AuthContext", () => ({
  useAuth: () => ({
    accessToken: "fake-jwt-token",
    user: { id: "user_1", email: "user@example.com", full_name: "Test User" },
    isAuthenticated: true,
    isLoading: false,
    loginWithProviderToken: vi.fn(),
    logout: vi.fn(),
  }),
}));

// Mock organization context
vi.mock("@/organizations/OrganizationContext", () => ({
  useOrganizations: () => ({
    organizations: [
      { organization: { id: "org_1", name: "Test Org", slug: "test-org" }, role: "owner" },
    ],
    activeOrganization: {
      organization: { id: "org_1", name: "Test Org", slug: "test-org" },
      role: "owner",
    },
    isLoading: false,
    refreshOrganizations: vi.fn(),
    createWorkspace: vi.fn(),
    switchWorkspace: vi.fn(),
  }),
}));

// Mock projects context
vi.mock("@/projects/ProjectContext", () => ({
  useProjects: () => ({
    projects: [
      {
        id: "proj_1",
        name: "Test Project One",
        slug: "test-project-one",
        description: "First test project",
        visibility: "public",
        status: "active",
        color: "#6366f1",
        created_at: "2026-07-02T12:00:00Z",
        updated_at: "2026-07-02T12:00:00Z",
      },
    ],
    activeProject: {
      id: "proj_1",
      name: "Test Project One",
      slug: "test-project-one",
      description: "First test project",
      visibility: "public",
      status: "active",
      color: "#6366f1",
      created_at: "2026-07-02T12:00:00Z",
      updated_at: "2026-07-02T12:00:00Z",
    },
    isLoading: false,
    refreshProjects: vi.fn(),
    switchProject: vi.fn(),
  }),
}));

// Mock the API client and integrations APIs
vi.mock("@/services/integrationApi", () => ({
  getGitHubDashboard: vi.fn(),
  syncGitHubIntegration: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getGitHubDashboard).mockResolvedValue({
    connected: true,
    stats: {
      total_commits: 120,
      pull_requests: 15,
      open_issues: 4,
      contributors: 3,
    },
    activity: [
      {
        id: "act_1",
        type: "commit",
        title: "feat: add user authentication flow",
        author: "Ameya",
        timestamp: "2026-07-02T18:00:00Z",
        repository: "ameya2401/KnowWhy",
      },
      {
        id: "act_2",
        type: "pull_request",
        title: "Merged PR #12: Update landing design system",
        author: "Bob",
        timestamp: "2026-07-02T15:00:00Z",
        repository: "ameya2401/KnowWhy",
      },
    ],
    repositories: [
      {
        id: "repo_1",
        github_repo_id: "12345",
        name: "KnowWhy",
        owner: "ameya2401",
        default_branch: "main",
        visibility: "public",
        clone_url: "https://github.com/ameya2401/KnowWhy",
        last_sync: "2026-07-02T19:00:00Z",
      },
    ],
    integration: {
      id: "int_1",
      status: "connected",
      connected_at: "2026-07-02T12:00:00Z",
      last_sync: "2026-07-02T19:00:00Z",
      last_error: null,
    },
  });
});

function renderDashboard() {
  const router = createMemoryRouter([{ path: "/dashboard", element: <DashboardPage /> }], {
    initialEntries: ["/dashboard"],
  });
  render(<RouterProvider router={router} />);
}

describe("DashboardPage", () => {
  it("renders the workspace dashboard with real git integration details", async () => {
    renderDashboard();

    expect(screen.getByRole("heading", { name: "Test Project One" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("120")).toBeInTheDocument(); // Commits
      expect(screen.getByText("15")).toBeInTheDocument(); // PRs
      expect(screen.getByText("4")).toBeInTheDocument(); // Open Issues
      expect(screen.getByText("3")).toBeInTheDocument(); // Contributors
      expect(screen.getByText("feat: add user authentication flow")).toBeInTheDocument();
      expect(screen.getByText("Merged PR #12: Update landing design system")).toBeInTheDocument();
    });
  });
});
