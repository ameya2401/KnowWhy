import { Github, KeyRound } from "lucide-react";
import { useState } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import type { AuthProviderName } from "@/auth/types";
import { Button } from "@/components/ui/button";

export function LoginPage() {
  const { isAuthenticated, isLoading, loginWithProviderToken } = useAuth();
  const [providerToken, setProviderToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<AuthProviderName | null>(null);

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function handleLogin(provider: AuthProviderName) {
    setError(null);
    setIsSubmitting(provider);
    try {
      await loginWithProviderToken(provider, providerToken.trim());
    } catch {
      setError("The provider token could not be verified.");
    } finally {
      setIsSubmitting(null);
    }
  }

  return (
    <main className="grid min-h-screen bg-background text-foreground lg:grid-cols-[1.1fr_0.9fr]">
      <section className="flex items-center px-6 py-10 sm:px-10 lg:px-16">
        <div className="max-w-2xl">
          <div className="flex items-center gap-3">
            <div className="grid size-11 place-items-center rounded-md bg-primary text-primary-foreground">
              <KeyRound className="size-5" aria-hidden="true" />
            </div>
            <div>
              <p className="font-display text-xl font-semibold">KnowWhy</p>
              <p className="text-sm text-muted-foreground">Identity gateway</p>
            </div>
          </div>

          <h1 className="mt-12 font-display text-4xl font-semibold sm:text-5xl">
            Sign in with the identity your work already trusts.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-muted-foreground">
            KnowWhy starts with OAuth so future organizational memory can inherit provider-backed
            trust without password storage.
          </p>

          <div className="mt-10 rounded-lg border border-border bg-card p-5 shadow-line">
            <label htmlFor="provider-token" className="text-sm font-medium">
              Provider access token
            </label>
            <textarea
              id="provider-token"
              className="mt-2 min-h-24 w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition focus:ring-2 focus:ring-ring"
              value={providerToken}
              onChange={(event) => setProviderToken(event.target.value)}
              placeholder="Paste a Google or GitHub OAuth access token for local testing."
            />
            {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <Button
                type="button"
                onClick={() => handleLogin("google")}
                disabled={!providerToken.trim() || isSubmitting !== null}
              >
                <span className="font-semibold">G</span>
                {isSubmitting === "google" ? "Checking Google" : "Continue with Google"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleLogin("github")}
                disabled={!providerToken.trim() || isSubmitting !== null}
              >
                <Github className="size-4" aria-hidden="true" />
                {isSubmitting === "github" ? "Checking GitHub" : "Continue with GitHub"}
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="hidden border-l border-border bg-[#173b3f] p-10 text-white lg:flex lg:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#f7c948]">
            Access principle
          </p>
          <p className="mt-5 font-display text-3xl font-semibold">
            Identity is verified before memory is visible.
          </p>
          <p className="mt-4 max-w-md text-sm leading-6 text-white/75">
            This page is intentionally only an authentication surface. The organizational model
            arrives in the next milestone.
          </p>
        </div>
      </section>
    </main>
  );
}
