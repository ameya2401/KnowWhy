import {
  BrainCircuit,
  CircleHelp,
  Database,
  Folder,
  GitBranch,
  Search,
  Settings,
} from "lucide-react";
import type { ReactNode } from "react";

import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";

const navigationItems = [
  { label: "Workspace", icon: BrainCircuit, href: "/" },
  { label: "Dashboard", icon: Search, href: "/dashboard" },
  { label: "Projects", icon: Folder, href: "/projects" },
  { label: "Members", icon: Database, href: "/members" },
  { label: "Settings", icon: GitBranch, href: "/settings" },
];

export function DashboardLayout({ children }: { children: ReactNode }) {
  const { logout } = useAuth();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-card px-4 py-5 lg:block">
        <div className="flex items-center gap-3 px-2">
          <div className="grid size-10 place-items-center rounded-md bg-primary text-primary-foreground">
            <BrainCircuit className="size-5" aria-hidden="true" />
          </div>
          <div>
            <p className="font-display text-lg font-semibold">KnowWhy</p>
            <p className="text-xs text-muted-foreground">Organizational memory</p>
          </div>
        </div>

        <nav className="mt-8 space-y-1" aria-label="Primary navigation">
          {navigationItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="flex h-10 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              <item.icon className="size-4" aria-hidden="true" />
              {item.label}
            </a>
          ))}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-border bg-background/90 backdrop-blur">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Authenticated workspace</p>
              <h1 className="font-display text-xl font-semibold">System Overview</h1>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" aria-label="Help">
                <CircleHelp className="size-4" />
              </Button>
              <Button variant="outline" size="icon" aria-label="Settings">
                <Settings className="size-4" />
              </Button>
              <Button variant="secondary" onClick={logout}>
                Log out
              </Button>
            </div>
          </div>
        </header>

        <main className="px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
