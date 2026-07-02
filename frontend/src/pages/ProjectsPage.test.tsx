import { render, screen, waitFor } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectsPage } from "@/pages/ProjectsPage";
import { apiClient } from "@/services/apiClient";

// Mock auth and organization contexts
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
    organizations: [{ id: "org_1", name: "Test Org", slug: "test-org" }],
    activeOrganization: { id: "org_1", name: "Test Org", slug: "test-org" },
    isLoading: false,
    refreshOrganizations: vi.fn(),
    createWorkspace: vi.fn(),
    switchWorkspace: vi.fn(),
  }),
}));

beforeEach(() => {
  vi.spyOn(apiClient, "get").mockImplementation((url) => {
    if (url === "/projects") {
      return Promise.resolve({
        data: [
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
      });
    }
    return Promise.reject(new Error(`Not mocked URL: ${url}`));
  });
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
      expect(screen.getByText("Test Project One")).toBeInTheDocument();
      expect(screen.getByText("/test-project-one")).toBeInTheDocument();
    });
  });
});
