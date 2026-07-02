import { createBrowserRouter } from "react-router-dom";

import { App } from "@/App";
import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { MembersPage } from "@/pages/MembersPage";
import { OrganizationSettingsPage } from "@/pages/OrganizationSettingsPage";
import { OrganizationSelectionPage } from "@/pages/OrganizationSelectionPage";
import { ProjectsPage } from "@/pages/ProjectsPage";
import { CreateProjectPage } from "@/pages/CreateProjectPage";
import { ProjectDetailPage } from "@/pages/ProjectDetailPage";
import { ProjectSettingsPage } from "@/pages/ProjectSettingsPage";
import { GitHubCallbackPage } from "@/pages/GitHubCallbackPage";
import { NotionCallbackPage } from "@/pages/NotionCallbackPage";
import { GoogleDriveCallbackPage } from "@/pages/GoogleDriveCallbackPage";
import { ActivityPage } from "@/pages/ActivityPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      {
        path: "/login",
        element: <LoginPage />,
      },
      {
        index: true,
        element: (
          <ProtectedRoute>
            <OrganizationSelectionPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/dashboard",
        element: (
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/activity",
        element: (
          <ProtectedRoute>
            <ActivityPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/settings",
        element: (
          <ProtectedRoute>
            <OrganizationSettingsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/members",
        element: (
          <ProtectedRoute>
            <MembersPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/projects",
        element: (
          <ProtectedRoute>
            <ProjectsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/projects/new",
        element: (
          <ProtectedRoute>
            <CreateProjectPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/projects/:projectId",
        element: (
          <ProtectedRoute>
            <ProjectDetailPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/projects/:projectId/settings",
        element: (
          <ProtectedRoute>
            <ProjectSettingsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/integrations/github/callback",
        element: (
          <ProtectedRoute>
            <GitHubCallbackPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/integrations/notion/callback",
        element: (
          <ProtectedRoute>
            <NotionCallbackPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/integrations/drive/callback",
        element: (
          <ProtectedRoute>
            <GoogleDriveCallbackPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
]);
