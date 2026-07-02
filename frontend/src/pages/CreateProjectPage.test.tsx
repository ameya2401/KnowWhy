import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { CreateProjectPage } from "@/pages/CreateProjectPage";

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

function renderCreateProject() {
  const router = createMemoryRouter([{ path: "/projects/new", element: <CreateProjectPage /> }], {
    initialEntries: ["/projects/new"],
  });
  render(<RouterProvider router={router} />);
}

describe("CreateProjectPage", () => {
  it("renders the create project page form", () => {
    renderCreateProject();

    expect(screen.getByRole("heading", { name: "Create Project" })).toBeInTheDocument();
    expect(screen.getByLabelText("Project Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Slug")).toBeInTheDocument();
    expect(screen.getByLabelText("Description")).toBeInTheDocument();
    expect(screen.getByLabelText("Visibility")).toBeInTheDocument();
  });
});
