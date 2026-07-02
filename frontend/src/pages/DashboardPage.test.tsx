import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { DashboardPage } from "@/pages/DashboardPage";

function renderDashboard() {
  const router = createMemoryRouter([{ path: "/", element: <DashboardPage /> }]);
  render(<RouterProvider router={router} />);
}

describe("DashboardPage", () => {
  it("renders the foundation dashboard", () => {
    renderDashboard();

    expect(screen.getByText("KnowWhy")).toBeInTheDocument();
    expect(screen.getByText("Milestone M01")).toBeInTheDocument();
    expect(screen.getByText("FastAPI")).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
  });
});
