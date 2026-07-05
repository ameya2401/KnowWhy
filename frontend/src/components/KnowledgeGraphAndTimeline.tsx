import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import {
  Search,
  Filter,
  Calendar,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  RefreshCw,
  GitCommit,
  GitPullRequest,
  Info,
  Clock,
  Compass,
  FileText,
  User,
  Settings,
  HelpCircle,
  Database,
  ArrowRight,
  Maximize2,
  BookOpen
} from "lucide-react";
import { graphApi } from "../services/graphApi";
import { GraphNode, GraphEdge, TimelineEvent } from "../types/graph";

// Colors for node types
const NODE_COLORS: Record<string, { bg: string; border: string; glow: string; text: string }> = {
  project: { bg: "#f97316", border: "#fdba74", glow: "rgba(249, 115, 22, 0.4)", text: "#ffedd5" },
  user: { bg: "#06b6d4", border: "#67e8f9", glow: "rgba(6, 182, 212, 0.4)", text: "#ecfeff" },
  integration: { bg: "#8b5cf6", border: "#c084fc", glow: "rgba(139, 92, 246, 0.4)", text: "#f5f3ff" },
  repository: { bg: "#3b82f6", border: "#93c5fd", glow: "rgba(59, 130, 246, 0.4)", text: "#eff6ff" },
  commit: { bg: "#0ea5e9", border: "#7dd3fc", glow: "rgba(14, 165, 233, 0.3)", text: "#f0f9ff" },
  pull_request: { bg: "#a855f7", border: "#d8b4fe", glow: "rgba(168, 85, 247, 0.3)", text: "#faf5ff" },
  issue: { bg: "#ef4444", border: "#fca5a5", glow: "rgba(239, 68, 68, 0.3)", text: "#fef2f2" },
  notion_page: { bg: "#eab308", border: "#fde047", glow: "rgba(234, 179, 8, 0.3)", text: "#fefce8" },
  document: { bg: "#10b981", border: "#6ee7b7", glow: "rgba(16, 185, 129, 0.3)", text: "#ecfdf5" },
  folder: { bg: "#0f766e", border: "#2dd4bf", glow: "rgba(15, 118, 110, 0.3)", text: "#f0fdfa" },
  decision: { bg: "#f43f5e", border: "#fda4af", glow: "rgba(244, 63, 94, 0.4)", text: "#fff1f2" },
  meeting: { bg: "#e11d48", border: "#fda4af", glow: "rgba(225, 29, 72, 0.4)", text: "#fff1f2" },
  default: { bg: "#6b7280", border: "#d1d5db", glow: "rgba(107, 114, 128, 0.3)", text: "#f9fafb" }
};

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  fx?: number | null;
  fy?: number | null;
  radius: number;
}

interface SimEdge extends GraphEdge {
  sourceNode?: SimNode;
  targetNode?: SimNode;
}

interface KnowledgeGraphAndTimelineProps {
  projectId: string;
}

export const KnowledgeGraphAndTimeline: React.FC<KnowledgeGraphAndTimelineProps> = ({ projectId }) => {
  const [activeTab, setActiveTab] = useState<"graph" | "timeline">("graph");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Raw API Data
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({ nodes: [], edges: [] });
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);

  // Graph State & Interaction
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<SimNode[]>([]);
  const [edges, setEdges] = useState<SimEdge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTypeFilters, setSelectedTypeFilters] = useState<string[]>([
    "project", "user", "integration", "repository", "commit", "pull_request", "issue", "notion_page", "document", "decision", "meeting"
  ]);

  // Timeline Filters
  const [timelineTypeFilter, setTimelineTypeFilter] = useState<string>("all");
  const [timelineSourceFilter, setTimelineSourceFilter] = useState<string>("all");
  const [timelineSearch, setTimelineSearch] = useState("");

  // Detailed Node Inspector
  const [inspectorData, setInspectorData] = useState<{
    node: GraphNode;
    relationships: any[];
  } | null>(null);
  const [inspectorLoading, setInspectorLoading] = useState(false);

  // Zoom & Pan offset
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const [zoomScale, setZoomScale] = useState(1);

  // Physics settings
  const repulsion = 400;
  const attraction = 0.05;
  const gravity = 0.02;
  const friction = 0.85;

  // Load Initial Graph & Timeline
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [gData, tData] = await Promise.all([
        graphApi.getGraph(projectId, 1000),
        graphApi.getProjectTimeline(projectId, { limit: 100 }),
      ]);
      setGraphData(gData);
      setTimelineEvents(tData.events);

      // Initialize Simulation Node Coordinates
      const simNodes: SimNode[] = gData.nodes.map((node, i) => {
        // Place in a spiral from center
        const angle = i * 0.45;
        const dist = 50 + i * 18;
        const radius = node.type === "project" ? 22 : node.type === "user" ? 16 : 12;
        return {
          ...node,
          x: 400 + Math.cos(angle) * dist,
          y: 300 + Math.sin(angle) * dist,
          vx: 0,
          vy: 0,
          radius
        };
      });

      const simEdges: SimEdge[] = gData.edges.map((edge) => ({ ...edge }));

      setNodes(simNodes);
      setEdges(simEdges);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load Knowledge Graph data. Please verify your integrations or try syncing.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load detailed Inspector Node Data on Node Selection
  useEffect(() => {
    if (!selectedNodeId) {
      setInspectorData(null);
      return;
    }
    const fetchDetail = async () => {
      setInspectorLoading(true);
      try {
        const detail = await graphApi.getEntityDetail(selectedNodeId, projectId);
        setInspectorData({
          node: detail.entity,
          relationships: detail.relationships,
        });
      } catch (err) {
        console.error(err);
        // Fallback to local node info if details endpoint fails (e.g. for synthetic nodes)
        const localNode = nodes.find((n) => n.id === selectedNodeId);
        if (localNode) {
          setInspectorData({
            node: localNode,
            relationships: []
          });
        }
      } finally {
        setInspectorLoading(false);
      }
    };
    fetchDetail();
  }, [selectedNodeId, projectId, nodes]);

  // Physics Simulation loop
  useEffect(() => {
    if (activeTab !== "graph" || nodes.length === 0) return;

    let animId: number;

    const tick = () => {
      const n = nodes.length;

      // 1. Repulsion between node pairs
      for (let i = 0; i < n; i++) {
        const u = nodes[i];
        for (let j = i + 1; j < n; j++) {
          const v = nodes[j];
          let dx = v.x - u.x;
          let dy = v.y - u.y;
          if (dx === 0) dx = 0.1; // avoid divide by zero
          const distSq = dx * dx + dy * dy;
          const dist = Math.sqrt(distSq);

          if (dist < 400) {
            // Force strength
            const force = repulsion / (distSq + 10);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            if (!u.fx) { u.vx -= fx; u.vy -= fy; }
            if (!v.fx) { v.vx += fx; v.vy += fy; }
          }
        }
      }

      // 2. Attraction along edges
      // Build lookup maps
      const nodeMap = new Map<string, SimNode>();
      nodes.forEach((node) => nodeMap.set(node.id, node));

      edges.forEach((edge) => {
        const sourceNode = nodeMap.get(edge.source);
        const targetNode = nodeMap.get(edge.target);

        if (sourceNode && targetNode) {
          edge.sourceNode = sourceNode;
          edge.targetNode = targetNode;

          const dx = targetNode.x - sourceNode.x;
          const dy = targetNode.y - sourceNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
          const desiredDist = 120;
          const force = (dist - desiredDist) * attraction;

          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          if (!sourceNode.fx) { sourceNode.vx += fx; sourceNode.vy += fy; }
          if (!targetNode.fx) { targetNode.vx -= fx; targetNode.vy -= fy; }
        }
      });

      // 3. Gravity/Centering & Apply velocities
      const centerX = 400;
      const centerY = 300;

      nodes.forEach((node) => {
        if (node.fx != null && node.fy != null) {
          node.x = node.fx;
          node.y = node.fy;
          node.vx = 0;
          node.vy = 0;
        } else {
          // Centering force
          node.vx += (centerX - node.x) * gravity;
          node.vy += (centerY - node.y) * gravity;

          // Damping/friction
          node.vx *= friction;
          node.vy *= friction;

          // Update position
          node.x += node.vx;
          node.y += node.vy;
        }
      });

      // Draw canvas
      draw();

      animId = requestAnimationFrame(tick);
    };

    const draw = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const width = canvas.width;
      const height = canvas.height;

      // Clear with dark blue theme background
      ctx.fillStyle = "#090d16";
      ctx.fillRect(0, 0, width, height);

      ctx.save();
      // Apply panning and zoom translation
      ctx.translate(transformRef.current.x, transformRef.current.y);
      ctx.scale(transformRef.current.k, transformRef.current.k);

      // Draw grid
      ctx.strokeStyle = "rgba(30, 41, 59, 0.3)";
      ctx.lineWidth = 1;
      const gridSize = 80;
      const startX = -transformRef.current.x / transformRef.current.k - 2000;
      const endX = startX + width / transformRef.current.k + 4000;
      const startY = -transformRef.current.y / transformRef.current.k - 2000;
      const endY = startY + height / transformRef.current.k + 4000;

      for (let x = Math.floor(startX / gridSize) * gridSize; x < endX; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, startY);
        ctx.lineTo(x, endY);
        ctx.stroke();
      }
      for (let y = Math.floor(startY / gridSize) * gridSize; y < endY; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(startX, y);
        ctx.lineTo(endX, y);
        ctx.stroke();
      }

      // Filter nodes and edges by active filters
      const filteredNodes = nodes.filter((n) => selectedTypeFilters.includes(n.type));
      const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));

      // Draw edges
      edges.forEach((edge) => {
        if (!edge.sourceNode || !edge.targetNode) return;
        if (!filteredNodeIds.has(edge.source) || !filteredNodeIds.has(edge.target)) return;

        const isHighlighted =
          selectedNodeId === edge.source ||
          selectedNodeId === edge.target ||
          hoveredNodeId === edge.source ||
          hoveredNodeId === edge.target;

        const isUnrelatedSelectedState = selectedNodeId && !isHighlighted;

        ctx.beginPath();
        ctx.moveTo(edge.sourceNode.x, edge.sourceNode.y);
        ctx.lineTo(edge.targetNode.x, edge.targetNode.y);

        if (isHighlighted) {
          ctx.strokeStyle = "rgba(99, 102, 241, 0.85)"; // active indigo link
          ctx.lineWidth = 2.5;
        } else {
          ctx.strokeStyle = isUnrelatedSelectedState
            ? "rgba(30, 41, 59, 0.15)"
            : "rgba(51, 65, 85, 0.4)";
          ctx.lineWidth = 1.2;
        }
        ctx.stroke();

        // Draw relationship type label on edge if highlighted or hovered
        if (isHighlighted && transformRef.current.k > 0.6) {
          const midX = (edge.sourceNode.x + edge.targetNode.x) / 2;
          const midY = (edge.sourceNode.y + edge.targetNode.y) / 2;
          ctx.font = "italic 9px sans-serif";
          ctx.fillStyle = "#cbd5e1";
          ctx.textAlign = "center";
          ctx.fillText(edge.type, midX, midY - 4);
        }
      });

      // Draw nodes
      filteredNodes.forEach((node) => {
        const colors = NODE_COLORS[node.type] || NODE_COLORS.default;
        const isSelected = selectedNodeId === node.id;
        const isHovered = hoveredNodeId === node.id;
        const isRelatedNeighbor =
          selectedNodeId &&
          edges.some(
            (e) =>
              (e.source === selectedNodeId && e.target === node.id) ||
              (e.target === selectedNodeId && e.source === node.id)
          );

        const isUnrelatedSelectedState = selectedNodeId && !isSelected && !isRelatedNeighbor;

        // Apply glow effect on active node
        if (isSelected || isHovered) {
          ctx.shadowBlur = 15;
          ctx.shadowColor = colors.glow;
        } else {
          ctx.shadowBlur = 0;
        }

        // Draw node bubble
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);

        // Fill color with glassmorphic transparency if unrelated
        if (isUnrelatedSelectedState) {
          ctx.fillStyle = "rgba(30, 41, 59, 0.2)";
          ctx.strokeStyle = "rgba(51, 65, 85, 0.2)";
        } else {
          ctx.fillStyle = colors.bg;
          ctx.strokeStyle = colors.border;
        }

        ctx.lineWidth = isSelected ? 3 : 1.5;
        ctx.fill();
        ctx.stroke();

        // Draw icons or initials in node center
        ctx.shadowBlur = 0; // reset shadow
        ctx.fillStyle = isUnrelatedSelectedState ? "rgba(255,255,255,0.1)" : colors.text;
        ctx.font = `bold ${node.radius * 0.9}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const initial = node.title ? node.title.charAt(0).toUpperCase() : "?";
        ctx.fillText(initial, node.x, node.y);

        // Draw Node Title Label
        if (transformRef.current.k > 0.4 || isHovered || isSelected) {
          ctx.fillStyle = isUnrelatedSelectedState ? "rgba(100, 116, 139, 0.4)" : "#f1f5f9";
          ctx.font = isSelected ? "bold 11px sans-serif" : "10px sans-serif";
          ctx.fillText(
            node.title.length > 20 ? node.title.slice(0, 18) + "..." : node.title,
            node.x,
            node.y + node.radius + 12
          );

          // Subtitle / Type label
          if (isSelected && !isUnrelatedSelectedState) {
            ctx.fillStyle = "#94a3b8";
            ctx.font = "italic 8.5px sans-serif";
            ctx.fillText(node.type.toUpperCase(), node.x, node.y + node.radius + 22);
          }
        }
      });

      ctx.restore();
    };

    animId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [nodes, edges, selectedNodeId, hoveredNodeId, selectedTypeFilters, activeTab]);

  // Handle Resize and high-DPI scaling
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = (rect?.width || 800) * dpr;
      canvas.height = (rect?.height || 600) * dpr;
      canvas.style.width = `${rect?.width || 800}px`;
      canvas.style.height = `${rect?.height || 600}px`;

      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.scale(dpr, dpr);
      }
    };

    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [activeTab]);

  // Dragging and Panning Event Listeners
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const panStartRef = useRef({ x: 0, y: 0 });
  const draggedNodeRef = useRef<SimNode | null>(null);

  const getCanvasMouseCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Convert screen coordinates to simulation coordinates accounting for pan & zoom
    return {
      x: (mouseX - transformRef.current.x) / transformRef.current.k,
      y: (mouseY - transformRef.current.y) / transformRef.current.k
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasMouseCoords(e);
    isDraggingRef.current = true;
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    panStartRef.current = { x: transformRef.current.x, y: transformRef.current.y };

    // Find if clicked node
    const clickedNode = nodes.find((node) => {
      const dx = node.x - coords.x;
      const dy = node.y - coords.y;
      return dx * dx + dy * dy < (node.radius + 5) * (node.radius + 5);
    });

    if (clickedNode && selectedTypeFilters.includes(clickedNode.type)) {
      draggedNodeRef.current = clickedNode;
      clickedNode.fx = clickedNode.x;
      clickedNode.fy = clickedNode.y;
      setSelectedNodeId(clickedNode.id);
    } else {
      draggedNodeRef.current = null;
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasMouseCoords(e);

    // Set hovered node indicator
    const hoveredNode = nodes.find((node) => {
      const dx = node.x - coords.x;
      const dy = node.y - coords.y;
      return dx * dx + dy * dy < (node.radius + 5) * (node.radius + 5);
    });

    if (hoveredNode && selectedTypeFilters.includes(hoveredNode.type)) {
      setHoveredNodeId(hoveredNode.id);
    } else {
      setHoveredNodeId(null);
    }

    if (!isDraggingRef.current) return;

    if (draggedNodeRef.current) {
      // Update dragged node position
      draggedNodeRef.current.fx = coords.x;
      draggedNodeRef.current.fy = coords.y;
    } else {
      // Panning grid
      const dx = e.clientX - dragStartRef.current.x;
      const dy = e.clientY - dragStartRef.current.y;
      transformRef.current.x = panStartRef.current.x + dx;
      transformRef.current.y = panStartRef.current.y + dy;
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
    if (draggedNodeRef.current) {
      draggedNodeRef.current.fx = null;
      draggedNodeRef.current.fy = null;
      draggedNodeRef.current = null;
    }
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = 1.1;
    const nextScale = e.deltaY < 0 ? transformRef.current.k * zoomFactor : transformRef.current.k / zoomFactor;

    // Constrain zoom
    const k = Math.max(0.15, Math.min(nextScale, 4));

    // Pan adjustment so zoom centers on cursor
    const dx = mouseX - transformRef.current.x;
    const dy = mouseY - transformRef.current.y;
    transformRef.current.x = mouseX - dx * (k / transformRef.current.k);
    transformRef.current.y = mouseY - dy * (k / transformRef.current.k);
    transformRef.current.k = k;
    setZoomScale(k);
  };

  // Zoom control buttons
  const zoomIn = () => {
    transformRef.current.k = Math.min(4, transformRef.current.k * 1.3);
    setZoomScale(transformRef.current.k);
  };

  const zoomOut = () => {
    transformRef.current.k = Math.max(0.15, transformRef.current.k / 1.3);
    setZoomScale(transformRef.current.k);
  };

  const resetView = () => {
    transformRef.current = { x: 0, y: 0, k: 1 };
    setZoomScale(1);
  };

  // Node Search Handler
  const handleNodeSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    const matchNode = nodes.find(
      (n) => n.title.toLowerCase().includes(searchQuery.toLowerCase()) && selectedTypeFilters.includes(n.type)
    );

    if (matchNode) {
      setSelectedNodeId(matchNode.id);
      // Center view on this node
      const canvas = canvasRef.current;
      if (canvas) {
        const width = canvas.width / (window.devicePixelRatio || 1);
        const height = canvas.height / (window.devicePixelRatio || 1);
        transformRef.current.k = 1.2;
        transformRef.current.x = width / 2 - matchNode.x * 1.2;
        transformRef.current.y = height / 2 - matchNode.y * 1.2;
        setZoomScale(1.2);
      }
    }
  };

  // Toggle Filters
  const handleTypeFilterToggle = (type: string) => {
    if (selectedTypeFilters.includes(type)) {
      setSelectedTypeFilters(selectedTypeFilters.filter((t) => t !== type));
    } else {
      setSelectedTypeFilters([...selectedTypeFilters, type]);
    }
  };

  // Timeline Filtering computation
  const filteredTimelineEvents = useMemo(() => {
    return timelineEvents.filter((event) => {
      // Type filter
      if (timelineTypeFilter !== "all" && event.type !== timelineTypeFilter) return false;
      // Source filter
      const source = event.metadata?.source || "";
      if (timelineSourceFilter !== "all" && source !== timelineSourceFilter) return false;
      // Search filter
      if (
        timelineSearch.trim() &&
        !event.title.toLowerCase().includes(timelineSearch.toLowerCase()) &&
        !(event.description || "").toLowerCase().includes(timelineSearch.toLowerCase())
      ) {
        return false;
      }
      return true;
    });
  }, [timelineEvents, timelineTypeFilter, timelineSourceFilter, timelineSearch]);

  return (
    <div className="flex flex-col h-[750px] w-full bg-[#070b13] border border-slate-800 rounded-xl overflow-hidden shadow-2xl font-sans text-slate-100">
      {/* Header controls tab bar */}
      <div className="flex items-center justify-between px-6 py-4 bg-[#0a0f1d] border-b border-slate-800/80">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-semibold tracking-wide text-slate-200">Knowledge Intelligence</h2>
          </div>
          <div className="flex bg-[#0f172a] p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setActiveTab("graph")}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === "graph"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Knowledge Graph</span>
            </button>
            <button
              onClick={() => setActiveTab("timeline")}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === "timeline"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Project Timeline</span>
            </button>
          </div>
        </div>

        <button
          onClick={loadData}
          className="p-2 bg-slate-800/60 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors border border-slate-700/50"
          title="Refresh Data"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-indigo-400" : ""}`} />
        </button>
      </div>

      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center space-y-3 bg-[#090d16]">
          <div className="w-10 h-10 border-4 border-indigo-500/25 border-t-indigo-500 rounded-full animate-spin"></div>
          <p className="text-sm text-slate-400">Assembling connection models...</p>
        </div>
      ) : error ? (
        <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[#090d16] text-center">
          <Info className="w-12 h-12 text-rose-500 mb-3" />
          <p className="text-sm text-slate-300 max-w-md">{error}</p>
          <button
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-colors"
          >
            Retry Loading
          </button>
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden bg-[#090d16] relative">
          {activeTab === "graph" ? (
            /* ==================== GRAPH VIEW ==================== */
            <div className="flex-1 flex relative">
              {/* Left filter side drawer */}
              <div className="w-64 bg-[#0a0f1d]/90 border-r border-slate-800/80 p-4 flex flex-col overflow-y-auto z-10 select-none glassmorphism">
                <form onSubmit={handleNodeSearch} className="relative mb-5">
                  <input
                    type="text"
                    placeholder="Search graph nodes..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-[#0f172a] border border-slate-800 rounded-lg py-2 pl-3 pr-8 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/30"
                  />
                  <button type="submit" className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-200">
                    <Search className="w-3.5 h-3.5" />
                  </button>
                </form>

                <div className="flex items-center space-x-1 text-[11px] font-semibold text-slate-400 tracking-wider uppercase mb-3">
                  <Filter className="w-3 h-3 text-indigo-400" />
                  <span>Node Visibility Types</span>
                </div>

                <div className="space-y-1.5 flex-1">
                  {Object.keys(NODE_COLORS).map((type) => {
                    if (type === "default") return null;
                    const colors = NODE_COLORS[type];
                    const count = graphData.nodes.filter((n) => n.type === type).length;
                    if (count === 0 && type !== "project" && type !== "user") return null;

                    return (
                      <label
                        key={type}
                        className="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-slate-800/40 cursor-pointer transition-colors"
                      >
                        <div className="flex items-center space-x-2 text-xs">
                          <input
                            type="checkbox"
                            checked={selectedTypeFilters.includes(type)}
                            onChange={() => handleTypeFilterToggle(type)}
                            className="rounded border-slate-800 text-indigo-600 bg-slate-950 focus:ring-0 focus:ring-offset-0"
                          />
                          <span
                            className="w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: colors.bg, border: `1px solid ${colors.border}` }}
                          />
                          <span className="capitalize text-slate-300">{type.replace("_", " ")}</span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono bg-slate-900/60 px-1.5 py-0.5 rounded-md border border-slate-800/50">
                          {count}
                        </span>
                      </label>
                    );
                  })}
                </div>

                <div className="pt-4 border-t border-slate-800/60 text-[10px] text-slate-500 space-y-1">
                  <div className="flex items-center space-x-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-indigo-500/70" />
                    <span className="font-medium text-slate-400">Interaction Guide</span>
                  </div>
                  <p>• Drag nodes to manually organize physics.</p>
                  <p>• Scroll to zoom in / out.</p>
                  <p>• Click empty canvas space to pan.</p>
                  <p>• Click node to open details inspector.</p>
                </div>
              </div>

              {/* Central Graph Canvas */}
              <div className="flex-1 h-full relative overflow-hidden bg-[#090d16]">
                <canvas
                  ref={canvasRef}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                  onWheel={handleWheel}
                  className="w-full h-full block cursor-grab active:cursor-grabbing"
                />

                {/* Canvas Floating controls */}
                <div className="absolute right-4 bottom-4 flex flex-col space-y-2">
                  <button
                    onClick={zoomIn}
                    className="p-2 bg-[#0a0f1d]/90 hover:bg-slate-800 rounded-lg border border-slate-800/80 text-slate-400 hover:text-white transition-colors glassmorphism"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                  <button
                    onClick={zoomOut}
                    className="p-2 bg-[#0a0f1d]/90 hover:bg-slate-800 rounded-lg border border-slate-800/80 text-slate-400 hover:text-white transition-colors glassmorphism"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <button
                    onClick={resetView}
                    className="p-2 bg-[#0a0f1d]/90 hover:bg-slate-800 rounded-lg border border-slate-800/80 text-slate-400 hover:text-white transition-colors glassmorphism"
                    title="Reset Coordinates"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="absolute left-4 top-4 bg-[#0a0f1d]/85 px-3 py-1.5 rounded-lg border border-slate-800/60 text-[10px] text-slate-400 font-mono pointer-events-none select-none glassmorphism">
                  Zoom: {Math.round(zoomScale * 100)}% | Active Nodes: {nodes.filter((n) => selectedTypeFilters.includes(n.type)).length}
                </div>
              </div>
            </div>
          ) : (
            /* ==================== TIMELINE VIEW ==================== */
            <div className="flex-1 flex overflow-hidden">
              {/* Left filter side panel */}
              <div className="w-64 bg-[#0a0f1d]/90 border-r border-slate-800/80 p-4 flex flex-col space-y-5 select-none glassmorphism">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Search Timeline</label>
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Search description..."
                      value={timelineSearch}
                      onChange={(e) => setTimelineSearch(e.target.value)}
                      className="w-full bg-[#0f172a] border border-slate-800 rounded-lg py-1.5 pl-3 pr-8 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/80"
                    />
                    <Search className="w-3.5 h-3.5 absolute right-2.5 top-2.5 text-slate-500" />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Entity Type</label>
                  <select
                    value={timelineTypeFilter}
                    onChange={(e) => setTimelineTypeFilter(e.target.value)}
                    className="w-full bg-[#0f172a] border border-slate-800 rounded-lg py-1.5 px-2.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="all">All Event Types</option>
                    <option value="commit">GitHub Commits</option>
                    <option value="pull_request">Pull Requests</option>
                    <option value="issue">GitHub Issues</option>
                    <option value="notion_page">Notion Pages</option>
                    <option value="document">Drive Documents</option>
                    <option value="ai_conversation">AI Conversations</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Source Provider</label>
                  <select
                    value={timelineSourceFilter}
                    onChange={(e) => setTimelineSourceFilter(e.target.value)}
                    className="w-full bg-[#0f172a] border border-slate-800 rounded-lg py-1.5 px-2.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="all">All Integration Sources</option>
                    <option value="github">GitHub</option>
                    <option value="notion">Notion</option>
                    <option value="google_drive">Google Drive</option>
                  </select>
                </div>

                <div className="pt-2 border-t border-slate-800/50 flex-1 flex flex-col justify-end text-[10px] text-slate-500 space-y-1">
                  <div className="flex items-center space-x-1.5">
                    <Clock className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="font-semibold text-slate-400">Timeline Metrics</span>
                  </div>
                  <p>Displaying {filteredTimelineEvents.length} total events matching active criteria.</p>
                </div>
              </div>

              {/* Main timeline listing flow */}
              <div className="flex-1 h-full overflow-y-auto p-6 bg-[#090d16] relative scrollbar-thin scrollbar-thumb-slate-800">
                {filteredTimelineEvents.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <Calendar className="w-10 h-10 text-slate-600 mb-2" />
                    <p className="text-sm text-slate-400">No events matched active filters.</p>
                  </div>
                ) : (
                  <div className="relative border-l border-slate-850 pl-6 space-y-6">
                    {filteredTimelineEvents.map((event) => {
                      const colors = NODE_COLORS[event.type] || NODE_COLORS.default;
                      const date = new Date(event.time);
                      const isSelected = selectedNodeId === event.id;

                      return (
                        <div
                          key={event.id}
                          onClick={() => setSelectedNodeId(event.id)}
                          className={`relative group cursor-pointer p-4 rounded-xl border transition-all ${
                            isSelected
                              ? "bg-slate-900/60 border-indigo-500/50 ring-1 ring-indigo-500/20"
                              : "bg-slate-900/20 border-slate-800/40 hover:border-slate-700/60 hover:bg-slate-900/40"
                          }`}
                        >
                          {/* Dot connector */}
                          <div
                            className="absolute -left-[31px] top-6 w-2.5 h-2.5 rounded-full border-2 transition-transform group-hover:scale-125"
                            style={{
                              backgroundColor: colors.bg,
                              borderColor: isSelected ? "#fff" : colors.border,
                              boxShadow: `0 0 8px ${colors.glow}`
                            }}
                          />

                          {/* Top row */}
                          <div className="flex items-center justify-between mb-1.5">
                            <div className="flex items-center space-x-2">
                              <span
                                className="px-2 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wider font-mono"
                                style={{
                                  backgroundColor: `${colors.bg}22`,
                                  color: colors.border,
                                  border: `1px solid ${colors.bg}44`
                                }}
                              >
                                {event.type.replace("_", " ")}
                              </span>
                              <h3 className="text-xs font-semibold text-slate-200 group-hover:text-indigo-400 transition-colors">
                                {event.title}
                              </h3>
                            </div>
                            <span className="text-[10px] text-slate-500 font-mono">
                              {date.toLocaleDateString(undefined, {
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit"
                              })}
                            </span>
                          </div>

                          {/* Body description */}
                          <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed pl-1">
                            {event.description || "No description provided."}
                          </p>

                          {/* Meta row */}
                          <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-900/60 text-[10px] text-slate-500 pl-1">
                            <div className="flex items-center space-x-1">
                              <User className="w-3 h-3 text-slate-400" />
                              <span>{event.author || "system"}</span>
                            </div>
                            {event.url && (
                              <a
                                href={event.url}
                                target="_blank"
                                rel="noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="flex items-center space-x-1 text-indigo-400 hover:text-indigo-300"
                              >
                                <span>Source</span>
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ==================== RIGHT ENTITY INSPECTOR PANEL ==================== */}
          <div
            className={`w-80 bg-[#0a0f1d]/95 border-l border-slate-800/80 flex flex-col shadow-2xl transition-all duration-350 z-20 glassmorphism ${
              selectedNodeId ? "translate-x-0" : "translate-x-full absolute right-0 top-0 bottom-0 pointer-events-none"
            }`}
          >
            {selectedNodeId && (
              <div className="flex-1 flex flex-col overflow-hidden pointer-events-auto">
                {/* Inspector Header */}
                <div className="flex items-center justify-between px-4 py-3 bg-slate-900/60 border-b border-slate-800/50">
                  <div className="flex items-center space-x-2">
                    <Info className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-semibold tracking-wider text-slate-300 uppercase">Entity Properties</span>
                  </div>
                  <button
                    onClick={() => setSelectedNodeId(null)}
                    className="text-slate-400 hover:text-slate-200 text-xs font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800"
                  >
                    CLOSE
                  </button>
                </div>

                {inspectorLoading ? (
                  <div className="flex-1 flex flex-col items-center justify-center space-y-2">
                    <div className="w-5 h-5 border-2 border-indigo-500/25 border-t-indigo-500 rounded-full animate-spin"></div>
                    <span className="text-[10px] text-slate-500">Querying details...</span>
                  </div>
                ) : inspectorData ? (
                  <div className="flex-1 overflow-y-auto p-4 space-y-5 scrollbar-thin scrollbar-thumb-slate-800">
                    {/* Node Type and Title Banner */}
                    <div className="space-y-1">
                      <div className="flex items-center space-x-1.5">
                        <span
                          className="px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider font-mono"
                          style={{
                            backgroundColor: `${(NODE_COLORS[inspectorData.node.type] || NODE_COLORS.default).bg}22`,
                            color: (NODE_COLORS[inspectorData.node.type] || NODE_COLORS.default).border,
                            border: `1px solid ${(NODE_COLORS[inspectorData.node.type] || NODE_COLORS.default).bg}44`
                          }}
                        >
                          {inspectorData.node.type.replace("_", " ")}
                        </span>
                        {inspectorData.node.subtitle && (
                          <span className="text-[9px] text-slate-500 font-mono">
                            {inspectorData.node.subtitle}
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-bold text-slate-100">{inspectorData.node.title}</h3>
                    </div>

                    {/* Metadata attributes list */}
                    <div className="bg-slate-900/40 p-3 rounded-lg border border-slate-850 space-y-2.5 text-xs text-slate-400">
                      {inspectorData.node.author && (
                        <div className="flex justify-between">
                          <span className="text-slate-550">Author:</span>
                          <span className="text-slate-300 font-medium">{inspectorData.node.author}</span>
                        </div>
                      )}
                      {inspectorData.node.metadata?.created_time && (
                        <div className="flex justify-between">
                          <span className="text-slate-550">Created:</span>
                          <span className="text-slate-300 font-mono text-[10px]">
                            {new Date(inspectorData.node.metadata.created_time).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                      {inspectorData.node.metadata?.updated_time && (
                        <div className="flex justify-between">
                          <span className="text-slate-550">Updated:</span>
                          <span className="text-slate-300 font-mono text-[10px]">
                            {new Date(inspectorData.node.metadata.updated_time).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                      {inspectorData.node.url && (
                        <div className="flex justify-between items-center pt-1 border-t border-slate-950/40">
                          <span className="text-slate-550">Original Link:</span>
                          <a
                            href={inspectorData.node.url}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center space-x-1 text-indigo-400 hover:text-indigo-300"
                          >
                            <span>Open Source</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      )}
                    </div>

                    {/* Description Text */}
                    {inspectorData.node.metadata?.description && (
                      <div className="space-y-1">
                        <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Description</h4>
                        <div className="text-xs text-slate-300 leading-relaxed bg-slate-900/10 p-2.5 rounded-lg border border-slate-850/60 max-h-24 overflow-y-auto scrollbar-thin">
                          {inspectorData.node.metadata.description}
                        </div>
                      </div>
                    )}

                    {/* Content Detail (e.g. Commit content / notions body) */}
                    {inspectorData.node.metadata?.content && (
                      <div className="space-y-1">
                        <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Indexed Content</h4>
                        <pre className="text-[10px] font-mono text-slate-400 p-2.5 bg-slate-950/60 rounded-lg border border-slate-900 overflow-x-auto max-h-36 overflow-y-auto scrollbar-thin leading-normal">
                          {inspectorData.node.metadata.content}
                        </pre>
                      </div>
                    )}

                    {/* Relationships List */}
                    <div className="space-y-2">
                      <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Graph Neighbors</h4>
                      {inspectorData.relationships.length === 0 ? (
                        <p className="text-[10px] text-slate-550 italic">No directional relationships mapped.</p>
                      ) : (
                        <div className="space-y-1.5">
                          {inspectorData.relationships.map((rel, idx) => {
                            const colors = NODE_COLORS[rel.neighbor.type] || NODE_COLORS.default;
                            return (
                              <div
                                key={idx}
                                onClick={() => setSelectedNodeId(rel.neighbor.id)}
                                className="flex items-center justify-between p-2 bg-[#0f172a]/70 hover:bg-slate-800/40 rounded-lg border border-slate-850 hover:border-slate-800 transition-colors cursor-pointer group text-xs"
                              >
                                <div className="flex items-center space-x-2 truncate">
                                  <span
                                    className="w-2 h-2 rounded-full flex-shrink-0"
                                    style={{ backgroundColor: colors.bg }}
                                  />
                                  <span className="text-slate-300 group-hover:text-indigo-400 transition-colors truncate">
                                    {rel.neighbor.title}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-1 text-[9px] text-slate-500 font-mono flex-shrink-0">
                                  <span className="capitalize">{rel.edge_type}</span>
                                  {rel.direction === "outgoing" ? (
                                    <ArrowRight className="w-2.5 h-2.5 text-indigo-400" />
                                  ) : (
                                    <ArrowRight className="w-2.5 h-2.5 text-indigo-400 rotate-180" />
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center p-4">
                    <p className="text-xs text-slate-550">Failed to load entity properties.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
