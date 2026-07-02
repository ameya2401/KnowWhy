import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

// Mock auth and organization contexts BEFORE importing components
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

vi.mock("@/projects/projectApi", () => ({
  listProjects: vi.fn().mockResolvedValue([
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
  ]),
}));

// Now import the component under test
import { ProjectsPage } from "@/pages/ProjectsPage";

beforeEach(() => {
  vi.clearAllMocks();
});

function renderProjects() {
  const router = createMemoryRouter([{ path: "/projects", element: <ProjectsPage /> }], {
    initialEntries: ["/projects"],
  });
  render(<RouterProvider router={router} />);
}

describe("ProjectsPage", () => {
  it("renders projects list page with projects", async () => {
    renderProjects();

    expect(screen.getByRole("heading", { name: "Projects" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Test Project One" })).toBeInTheDocument();
      expect(screen.getByText("/test-project-one")).toBeInTheDocument();
    });
  });
});
