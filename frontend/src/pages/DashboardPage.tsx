import { Activity, Database, Server, Workflow } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";

const statusCards = [
  {
    title: "Frontend",
    value: "React shell",
    description: "Routing, query client, and design primitives are ready.",
    icon: Workflow,
  },
  {
    title: "Backend",
    value: "FastAPI",
    description: "Health API and layered package structure are in place.",
    icon: Server,
  },
  {
    title: "Database",
    value: "PostgreSQL",
    description: "Connection configuration is prepared without app tables.",
    icon: Database,
  },
  {
    title: "Cache",
    value: "Redis",
    description: "Cache connection verification is available for the stack.",
    icon: Activity,
  },
];

export function DashboardPage() {
  return (
    <DashboardLayout>
      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="rounded-lg border border-border bg-card p-6 shadow-line">
          <div className="max-w-3xl">
            <p className="text-sm font-medium text-primary">Milestone M01</p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-normal sm:text-4xl">
              Foundation for organizational memory, before the intelligence arrives.
            </h2>
            <p className="mt-4 text-base leading-7 text-muted-foreground">
              KnowWhy is starting with a stable engineering base: clean boundaries, typed frontend
              code, a minimal backend API, and infrastructure that can grow without pulling future
              features into the foundation.
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-[#f7c948] p-6 text-[#172126] shadow-line">
          <p className="text-sm font-semibold uppercase tracking-[0.18em]">Evidence rule</p>
          <p className="mt-5 font-display text-2xl font-semibold">
            No claims without sources. No automation without context.
          </p>
          <p className="mt-4 text-sm leading-6 text-[#35434a]">
            The interface begins as a dashboard shell only. Future milestones will add real data
            when the domain contracts exist.
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
