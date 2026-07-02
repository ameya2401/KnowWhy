import { Building2, Plus } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useOrganizations } from "@/organizations/OrganizationContext";

export function OrganizationSelectionPage() {
  const navigate = useNavigate();
  const { organizations, createWorkspace, switchWorkspace, isLoading } = useOrganizations();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");

  async function handleCreate() {
    await createWorkspace({
      name,
      slug,
      description: description || null,
    });
    setName("");
    setSlug("");
    setDescription("");
    navigate("/dashboard");
  }

  return (
    <DashboardLayout>
      <section className="grid gap-6 xl:grid-cols-[1fr_0.85fr]">
        <div>
          <p className="text-sm font-medium text-primary">Workspace switching</p>
          <h2 className="mt-3 font-display text-3xl font-semibold">Choose an organization</h2>
          <div className="mt-6 grid gap-3">
            {organizations.map((item) => (
              <Card key={item.organization.id}>
                <CardContent className="flex items-center justify-between p-5">
                  <div className="flex items-center gap-3">
                    <div className="grid size-10 place-items-center rounded-md bg-secondary">
                      <Building2 className="size-5" aria-hidden="true" />
                    </div>
                    <div>
                      <p className="font-medium">{item.organization.name}</p>
                      <p className="text-sm text-muted-foreground">{item.role}</p>
                    </div>
                  </div>
                  <Button
                    onClick={async () => {
                      await switchWorkspace(item.organization.id);
                      navigate("/dashboard");
                    }}
                  >
                    Open
                  </Button>
                </CardContent>
              </Card>
            ))}
            {!isLoading && organizations.length === 0 ? (
              <p className="rounded-lg border border-border bg-card p-5 text-sm text-muted-foreground">
                Create your first organization to enter a workspace.
              </p>
            ) : null}
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Create organization</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <input
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Organization name"
            />
            <input
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
              value={slug}
              onChange={(event) => setSlug(event.target.value)}
              placeholder="organization-slug"
            />
            <textarea
              className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Description"
            />
            <Button onClick={handleCreate} disabled={!name || !slug}>
              <Plus className="size-4" aria-hidden="true" />
              Create workspace
            </Button>
          </CardContent>
        </Card>
      </section>
    </DashboardLayout>
  );
}
