import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2, AlertCircle } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { connectNotion } from "@/services/integrationApi";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function NotionCallbackPage() {
  const { accessToken } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const code = searchParams.get("code");
  // Notion uses 'state' to pass the project_id
  const projectId = searchParams.get("state");

  useEffect(() => {
    let active = true;

    async function handleCallback() {
      if (!accessToken) return;
      if (!code || !projectId) {
        setStatus("error");
        setErrorMsg("Missing OAuth authorization code or project context.");
        return;
      }

      try {
        await connectNotion(accessToken, { code, project_id: projectId });
        if (active) {
          setStatus("success");
          setTimeout(() => {
            navigate(`/projects/${projectId}`);
          }, 1500);
        }
      } catch (err) {
        if (active) {
          setStatus("error");
          const errorObj = err as { response?: { data?: { detail?: string } } };
          setErrorMsg(errorObj.response?.data?.detail ?? "Failed to connect to Notion.");
        }
      }
    }

    void handleCallback();

    return () => {
      active = false;
    };
  }, [accessToken, code, projectId, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md shadow-line">
        <CardHeader className="space-y-1">
          <CardTitle className="text-center text-2xl font-bold tracking-tight">
            Notion Connection
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center p-6 text-center">
          {status === "loading" && (
            <div className="space-y-4">
              <Loader2 className="mx-auto size-12 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Authorizing with Notion and securing credentials...
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="space-y-4">
              <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                ✓
              </div>
              <p className="text-sm font-medium text-emerald-600">
                Successfully connected! Redirecting back to project...
              </p>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-4 w-full">
              <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-red-100 text-red-600">
                <AlertCircle className="size-6" />
              </div>
              <p className="text-sm font-medium text-red-600">
                {errorMsg || "An error occurred during authentication."}
              </p>
              <Button
                className="mt-4 w-full"
                onClick={() => navigate(projectId ? `/projects/${projectId}` : "/projects")}
              >
                Go Back
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
