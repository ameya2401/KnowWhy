import { render, screen, waitFor } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "@/auth/AuthProvider";
import { LoginPage } from "@/pages/LoginPage";
import { apiClient } from "@/services/apiClient";

beforeEach(() => {
  vi.spyOn(apiClient, "post").mockRejectedValue(new Error("No refresh session."));
});

function renderLogin() {
  const router = createMemoryRouter([{ path: "/login", element: <LoginPage /> }], {
    initialEntries: ["/login"],
  });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
}

describe("LoginPage", () => {
  it("renders OAuth login actions", async () => {
    renderLogin();

    expect(screen.getByText("KnowWhy")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue with google/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue with github/i })).toBeInTheDocument();
    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith("/auth/refresh", {}));
  });
});
