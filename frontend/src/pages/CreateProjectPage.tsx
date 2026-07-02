import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Plus } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { createProject } from "@/projects/projectApi";
import type { ProjectVisibility } from "@/projects/types";

const colorPresets = [
  { name: "Indigo", value: "#6366f1" },
  { name: "Blue", value: "#3b82f6" },
  { name: "Emerald", value: "#10b981" },
  { name: "Amber", value: "#f59e0b" },
  { name: "Rose", value: "#f43f5e" },
  { name: "Violet", value: "#8b5cf6" },
  { name: "Zinc", value: "#71717a" },
];

export function CreateProjectPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<ProjectVisibility>("private");
  const [selectedColor, setSelectedColor] = useState(colorPresets[0].value);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-generate slug from name
  const handleNameChange = (val: string) => {
    setName(val);
    const generatedSlug = val
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .slice(0, 80);
    setSlug(generatedSlug);
  };

  const handleCreate = async () => {
    if (!accessToken) {
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const nextProject = await createProject(accessToken, {
        name,
        slug,
        description: description || null,
        visibility,
        color: selectedColor,
      });
      navigate(`/projects/${nextProject.id}`);
    } catch (err) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      setError(errorObj.response?.data?.detail ?? "Failed to create project.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link to="/projects">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="size-4" />
            </Button>
          </Link>
          <div>
            <h2 className="font-display text-3xl font-semibold tracking-tight">Create Project</h2>
            <p className="text-sm text-muted-foreground">
              Add a new project to your active workspace.
            </p>
          </div>
        </div>

        <Card className="max-w-2xl">
          <CardHeader>
            <CardTitle>Project Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-700/10">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="project-name" className="text-sm font-medium">
                Project Name
              </label>
              <input
                id="project-name"
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                value={name}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="e.g. Atlas Platform"
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="project-slug" className="text-sm font-medium">
                Slug
              </label>
              <input
                id="project-slug"
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="e.g. atlas-platform"
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="project-description" className="text-sm font-medium">
                Description
              </label>
              <textarea
                id="project-description"
                className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What is this project about?"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="project-visibility" className="text-sm font-medium">
                Visibility
              </label>
              <select
                id="project-visibility"
                value={visibility}
                onChange={(e) => setVisibility(e.target.value as ProjectVisibility)}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="private">Private (Only project members can access)</option>
                <option value="public">Public (Everyone in organization can access)</option>
              </select>
            </div>

            <div className="space-y-2">
              <span className="text-sm font-medium block">Project Color Accent</span>
              <div className="flex gap-2">
                {colorPresets.map((preset) => (
                  <button
                    key={preset.value}
                    onClick={() => setSelectedColor(preset.value)}
                    className="size-8 rounded-full border-2 transition-transform focus:outline-none"
                    style={{
                      backgroundColor: preset.value,
                      borderColor: selectedColor === preset.value ? "#000" : "transparent",
                      transform: selectedColor === preset.value ? "scale(1.1)" : "scale(1)",
                    }}
                    title={preset.name}
                    aria-label={`Select ${preset.name} color`}
                  />
                ))}
              </div>
            </div>

            <div className="pt-4 flex gap-3">
              <Button onClick={handleCreate} disabled={!name || !slug || isSubmitting}>
                <Plus className="mr-2 size-4" />
                {isSubmitting ? "Creating..." : "Create Project"}
              </Button>
              <Link to="/projects">
                <Button variant="outline">Cancel</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
