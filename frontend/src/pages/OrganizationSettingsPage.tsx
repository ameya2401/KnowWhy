import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { updateOrganization } from "@/organizations/organizationApi";
import { useOrganizations } from "@/organizations/OrganizationContext";
import { useAuth } from "@/auth/AuthContext";

export function OrganizationSettingsPage() {
  const { accessToken } = useAuth();
  const { activeOrganization, refreshOrganizations } = useOrganizations();
  const [name, setName] = useState(activeOrganization?.organization.name ?? "");
  const [description, setDescription] = useState(
    activeOrganization?.organization.description ?? "",
  );
  const [logoUrl, setLogoUrl] = useState(activeOrganization?.organization.logo_url ?? "");

  async function handleSave() {
    if (!accessToken || !activeOrganization) {
      return;
    }
    await updateOrganization(accessToken, activeOrganization.organization.id, {
      name,
      description,
      logo_url: logoUrl || null,
    });
    await refreshOrganizations();
  }

  return (
    <DashboardLayout>
      <Card>
        <CardHeader>
          <CardTitle>Organization settings</CardTitle>
        </CardHeader>
        <CardContent className="max-w-xl space-y-3">
          <input
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Name"
          />
          <input
            className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            value={logoUrl}
            onChange={(event) => setLogoUrl(event.target.value)}
            placeholder="Logo URL"
          />
          <textarea
            className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Description"
          />
          <Button onClick={handleSave} disabled={!activeOrganization}>
            Save changes
          </Button>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
