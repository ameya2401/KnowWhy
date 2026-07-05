import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Brain,
  Folder,
  Link2,
  Activity,
  Settings,
  Search,
  Database,
  Clock,
  Menu,
  X,
  Sun,
  Moon,
  Building2,
  LogOut,
  Sparkles,
} from "lucide-react";
import type { ReactNode } from "react";

import { useAuth } from "@/auth/AuthContext";
import { useOrganizations } from "@/organizations/OrganizationContext";
import { useProjects } from "@/projects/ProjectContext";

export function DashboardLayout({ children }: { children: ReactNode }) {
  const { logout, user } = useAuth();
  const { organizations, activeOrganization, switchWorkspace } = useOrganizations();
  const { projects, activeProject, switchProject } = useProjects();
  const location = useLocation();
  const navigate = useNavigate();

  // Mobile menu state
  const [mobileOpen, setMobileOpen] = useState(false);

  // Theme state
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("knowwhy:theme") as "light" | "dark") || "light",
  );

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("knowwhy:theme", theme);
  }, [theme]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === "/" &&
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "TEXTAREA"
      ) {
        e.preventDefault();
        const headerSearch = document.getElementById("header-search-bar");
        headerSearch?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  const navItems = [
    { label: "Dashboard", icon: LayoutDashboardLink, href: "/dashboard" },
    { label: "Projects", icon: Folder, href: "/projects" },
    { label: "Search", icon: Search, href: "/search" },
    {
      label: "Integrations",
      icon: Link2,
      href: activeProject ? `/projects/${activeProject.id}?tab=integrations` : "/projects",
    },
    { label: "Activity", icon: Activity, href: "/activity" },
    { label: "Settings", icon: Settings, href: "/settings" },
  ];

  const futureItems = [
    { label: "AI Chat", icon: Sparkles },
    { label: "Memory", icon: Database },
    { label: "Timeline", icon: Clock },
  ];

  function LayoutDashboardLink(props: React.SVGProps<SVGSVGElement>) {
    // Custom icon mapper for layout dashboard
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        {...props}
      >
        <rect width="7" height="9" x="3" y="3" rx="1" />
        <rect width="7" height="5" x="14" y="3" rx="1" />
        <rect width="7" height="9" x="14" y="12" rx="1" />
        <rect width="7" height="5" x="3" y="16" rx="1" />
      </svg>
    );
  }

  const handleOrgChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const orgId = e.target.value;
    if (orgId) {
      await switchWorkspace(orgId);
      navigate("/dashboard");
    }
  };

  const handleProjectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const projectId = e.target.value;
    if (projectId) {
      switchProject(projectId);
      navigate("/dashboard");
    }
  };

  const renderSidebarContent = () => (
    <div className="flex h-full flex-col justify-between">
      <div>
        {/* Logo and Brand */}
        <div className="flex items-center gap-3 px-2 pt-1">
          <div className="grid size-10 place-items-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <Brain className="size-5 animate-pulse" aria-hidden="true" />
          </div>
          <div>
            <p className="font-display text-lg font-bold tracking-tight text-foreground">KnowWhy</p>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
              Org Intelligence
            </p>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="mt-8">
          <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-2">
            Navigation
          </p>
          <nav className="space-y-1" aria-label="Sidebar navigation">
            {navItems.map((item) => {
              const isActive =
                location.pathname === item.href ||
                (item.href !== "/dashboard" &&
                  location.pathname.startsWith(item.href.split("?")[0]));
              return (
                <Link
                  key={item.label}
                  to={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  }`}
                >
                  <item.icon className="size-4 shrink-0" aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Future/AI Features Section */}
        <div className="mt-8">
          <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-2">
            Intelligence (Coming Soon)
          </p>
          <div className="space-y-1">
            {futureItems.map((item) => (
              <div
                key={item.label}
                className="flex h-10 items-center justify-between rounded-md px-3 text-sm text-muted-foreground/40 cursor-not-allowed select-none"
              >
                <div className="flex items-center gap-3">
                  <item.icon className="size-4 shrink-0" aria-hidden="true" />
                  <span>{item.label}</span>
                </div>
                <span className="text-[9px] font-mono border border-muted-foreground/10 px-1 rounded bg-muted/20">
                  Soon
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Profile summary */}
      <div className="border-t border-border pt-4 mt-auto">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="grid size-8 shrink-0 place-items-center rounded-full bg-secondary font-display text-xs font-semibold text-secondary-foreground">
              {user?.full_name?.charAt(0) || "U"}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-medium text-foreground truncate">{user?.full_name}</p>
              <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="p-1.5 text-muted-foreground hover:text-red-500 rounded-md hover:bg-accent transition-colors"
            title="Log out"
          >
            <LogOut className="size-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      {/* Desktop Sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-card/60 backdrop-blur-md px-4 py-5 lg:block z-30">
        {renderSidebarContent()}
      </aside>

      {/* Mobile Drawer Sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          {/* Backdrop overlay */}
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          {/* Menu Drawer */}
          <div className="relative flex w-64 max-w-xs flex-col bg-card px-4 py-5 border-r border-border shadow-xl">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute top-4 right-4 p-1.5 text-muted-foreground hover:text-foreground rounded-md"
            >
              <X className="size-5" />
            </button>
            <div className="flex-1 mt-2">{renderSidebarContent()}</div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        {/* Top Header Navbar */}
        <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur-md">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8 gap-4">
            {/* Hamburger button for mobile */}
            <button
              onClick={() => setMobileOpen(true)}
              className="p-2 text-muted-foreground hover:text-foreground rounded-md lg:hidden shrink-0 border"
              aria-label="Toggle sidebar"
            >
              <Menu className="size-5" />
            </button>

            {/* Selectors for Organization & Project */}
            <div className="flex flex-1 items-center gap-3 overflow-x-auto no-scrollbar py-1">
              {/* Org Switcher */}
              <div className="flex items-center gap-1.5 shrink-0 bg-secondary/30 rounded-md border px-2 py-1 max-w-[160px] sm:max-w-none">
                <Building2 className="size-3.5 text-muted-foreground shrink-0" />
                <select
                  value={activeOrganization?.organization?.id || ""}
                  onChange={handleOrgChange}
                  className="bg-transparent text-xs font-semibold focus:outline-none cursor-pointer border-none p-0 pr-1 text-foreground"
                >
                  {organizations.map((org) => (
                    <option key={org.organization?.id} value={org.organization?.id}>
                      {org.organization?.name}
                    </option>
                  ))}
                  {organizations.length === 0 && <option value="">No org selected</option>}
                </select>
              </div>

              {/* Project Switcher */}
              {activeOrganization && (
                <div className="flex items-center gap-1.5 shrink-0 bg-secondary/30 rounded-md border px-2 py-1 max-w-[160px] sm:max-w-none">
                  <Folder className="size-3.5 text-muted-foreground shrink-0" />
                  <select
                    value={activeProject?.id || ""}
                    onChange={handleProjectChange}
                    className="bg-transparent text-xs font-semibold focus:outline-none cursor-pointer border-none p-0 pr-1 text-foreground"
                  >
                    {projects.map((proj) => (
                      <option key={proj.id} value={proj.id}>
                        {proj.name}
                      </option>
                    ))}
                    {projects.length === 0 && <option value="">No project</option>}
                  </select>
                </div>
              )}
            </div>

            {/* Global Search Bar */}
            {activeProject && (
              <div className="hidden md:flex flex-1 max-w-xs relative mx-4">
                <Search className="absolute left-2.5 top-2.5 size-3.5 text-muted-foreground" />
                <input
                  id="header-search-bar"
                  type="text"
                  placeholder="Search knowledge... (/)"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      const value = (e.target as HTMLInputElement).value;
                      navigate(`/search?q=${encodeURIComponent(value)}`);
                      (e.target as HTMLInputElement).value = "";
                      (e.target as HTMLInputElement).blur();
                    }
                  }}
                  className="h-9 w-full rounded-md border border-input bg-card pl-8 pr-3 text-xs outline-none focus:ring-1 focus:ring-primary shadow-sm"
                />
              </div>
            )}

            {/* Header Right Actions */}
            <div className="flex items-center gap-2 shrink-0">
              {/* Theme Toggle Button */}
              <button
                onClick={toggleTheme}
                className="p-2 hover:bg-accent rounded-md border text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Toggle theme"
              >
                {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
              </button>

              {/* Profile Shortcut */}
              <div className="hidden sm:flex items-center gap-2 border px-3 py-1.5 rounded-md bg-card">
                <div className="grid size-6 place-items-center rounded-full bg-primary/10 text-primary text-[10px] font-semibold">
                  {user?.full_name?.charAt(0) || "U"}
                </div>
                <span className="text-xs font-medium text-foreground max-w-[100px] truncate">
                  {user?.full_name}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Workspace Content Router Viewport */}
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
