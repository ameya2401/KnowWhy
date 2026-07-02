import { Activity, Database, Server, Workflow } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useOrganizations } from "@/organizations/OrganizationContext";

const statusCards = [
  {
    title: "Frontend",
    value: "Protected shell",
    description: "Unauthenticated users are routed to login before entering the app.",
    icon: Workflow,
  },
  {
    title: "Backend",
    value: "FastAPI",
    description: "Auth endpoints, health checks, and session contracts are in place.",
    icon: Server,
  },
  {
    title: "Database",
    value: "Users",
    description: "Identity tables exist without organization or product domain logic.",
    icon: Database,
  },
  {
    title: "Session",
    value: "JWT",
    description: "Access and refresh token flows are handled by the backend.",
    icon: Activity,
  },
];

export function DashboardPage() {
  const { activeOrganization } = useOrganizations();

  return (
    <DashboardLayout>
      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="rounded-lg border border-border bg-card p-6 shadow-line">
          <div className="max-w-3xl">
            <p className="text-sm font-medium text-primary">Milestone M04</p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-normal sm:text-4xl">
              {activeOrganization
                ? `${activeOrganization.organization.name} workspace`
                : "Choose an organization to begin."}
            </h2>
            <p className="mt-4 text-base leading-7 text-muted-foreground">
              KnowWhy now has OAuth-first authentication, signed tokens, refresh sessions, and a
              protected app shell. Organization, team, project, and intelligence features remain
              outside this milestone.
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-[#f7c948] p-6 text-[#172126] shadow-line">
          <p className="text-sm font-semibold uppercase tracking-[0.18em]">Security rule</p>
          <p className="mt-5 font-display text-2xl font-semibold">
            No passwords. Provider identity first, app access second.
          </p>
          <p className="mt-4 text-sm leading-6 text-[#35434a]">
            The dashboard remains a placeholder until later milestones define real organizational
            data.
          </p>
        </div>
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {statusCards.map((card) => (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle>{card.title}</CardTitle>
              <card.icon className="size-4 text-muted-foreground" aria-hidden="true" />
            </CardHeader>
            <CardContent>
              <p className="font-display text-2xl font-semibold">{card.value}</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{card.description}</p>
            </CardContent>
          </Card>
        ))}
      </section>
    </DashboardLayout>
  );
}
