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
