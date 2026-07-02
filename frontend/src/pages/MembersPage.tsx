import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { listMembers } from "@/organizations/organizationApi";
import { useOrganizations } from "@/organizations/OrganizationContext";
import type { OrganizationMember } from "@/organizations/types";
import { useAuth } from "@/auth/AuthContext";

export function MembersPage() {
  const { accessToken } = useAuth();
  const { activeOrganization } = useOrganizations();
  const [members, setMembers] = useState<OrganizationMember[]>([]);

  useEffect(() => {
    async function loadMembers() {
      if (!accessToken || !activeOrganization) {
        setMembers([]);
        return;
      }
      setMembers(await listMembers(accessToken, activeOrganization.organization.id));
    }

    void loadMembers();
  }, [accessToken, activeOrganization]);

  return (
    <DashboardLayout>
      <Card>
        <CardHeader>
          <CardTitle>Members</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {members.map((member) => (
            <div
              key={member.id}
              className="flex items-center justify-between rounded-md border border-border p-3"
            >
              <div>
                <p className="font-medium">{member.full_name}</p>
                <p className="text-sm text-muted-foreground">{member.email}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium">{member.role}</p>
                <p className="text-xs text-muted-foreground">
                  Joined {new Date(member.joined_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
          {members.length === 0 ? (
            <p className="text-sm text-muted-foreground">No members to display.</p>
          ) : null}
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}
