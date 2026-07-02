import { render, screen, waitFor } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/auth/AuthProvider";
import { OrganizationProvider } from "@/organizations/OrganizationProvider";
import { DashboardPage } from "@/pages/DashboardPage";
import { apiClient } from "@/services/apiClient";

beforeEach(() => {
  vi.spyOn(apiClient, "post").mockRejectedValue(new Error("No refresh session."));
});

function renderDashboard() {
  const router = createMemoryRouter([{ path: "/", element: <DashboardPage /> }]);
  render(
    <AuthProvider>
      <OrganizationProvider>
        <RouterProvider router={router} />
      </OrganizationProvider>
    </AuthProvider>,
  );
}

describe("DashboardPage", () => {
  it("renders the authenticated dashboard shell", async () => {
    renderDashboard();

    expect(screen.getByText("Milestone M04")).toBeInTheDocument();
    expect(screen.getByText("JWT")).toBeInTheDocument();
    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith("/auth/refresh", {}));
  });
});
