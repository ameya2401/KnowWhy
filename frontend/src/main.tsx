import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";

import { AuthProvider } from "@/auth/AuthProvider";
import { OrganizationProvider } from "@/organizations/OrganizationProvider";
import { ProjectProvider } from "@/projects/ProjectProvider";
import { queryClient } from "@/services/queryClient";
import { router } from "@/routes/router";
import "@/styles/globals.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <OrganizationProvider>
          <ProjectProvider>
            <RouterProvider router={router} />
          </ProjectProvider>
        </OrganizationProvider>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
