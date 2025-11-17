import React, { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  FiCalendar,
  FiFilter,
  FiRefreshCcw,
  FiSearch,
  FiPlusCircle,
} from "react-icons/fi";

const API_BASE = "http://localhost:8000";
const TIMELINE_URL = `${API_BASE}/timeline`;
const TIMELINE_STATS_URL = `${API_BASE}/timeline/stats`;
const ADMIN_TICKETS_URL = `${API_BASE}/admin/tickets`;
const PROJECTS_URL = `${API_BASE}/projects`;

const PRIORITY_WINDOWS = {
  Low: { totalMinutes: 72 * 60, label: "Up to 72 Hrs" },
  Medium: { totalMinutes: 24 * 60, label: "Up to 24 Hrs" },
  High: { totalMinutes: 6 * 60, label: "Up to 6 Hrs" },
  Critical: { totalMinutes: 60, label: "Up to 1 Hr" },
};

const createFallbackTask = ({
  id,
  ticketCode,
  project,
  name,
  priority,
  status,
  start,
  progress,
}) => {
  const window = PRIORITY_WINDOWS[priority] || PRIORITY_WINDOWS.Medium;
  const startDate = new Date(start);
  const startIso = Number.isNaN(startDate.getTime())
    ? new Date().toISOString()
    : startDate.toISOString();
  const endIso = Number.isNaN(startDate.getTime())
    ? null
    : new Date(startDate.getTime() + window.totalMinutes * 60000).toISOString();
  const accumulatedMinutes =
    typeof progress === "number"
      ? Math.max(0, Math.min(100, progress)) * 0.01 * window.totalMinutes
      : 0;

  return {
    id,
    ticketCode: ticketCode || null,
    project,
    name,
    priority,
    status,
    start: startIso,
    end: endIso,
    duration: window.label,
    totalMinutes: window.totalMinutes,
    accumulatedMinutes,
    lastStartedAt: startIso,
    isPaused: status !== "In Progress",
    progress,
  };
};

const INITIAL_TASKS = [
  createFallbackTask({
    id: "t-1",
    ticketCode: "FL0001V",
    project: "NOVYA",
    name: "API Refactor",
    priority: "High",
    status: "In Progress",
    start: "2025-09-22T08:00:00",
    progress: 55,
  }),
  createFallbackTask({
    id: "t-2",
    ticketCode: "FL0002V",
    project: "JIO",
    name: "UI Polish",
    priority: "Low",
    status: "Completed",
    start: "2025-09-21T09:00:00",
    progress: 100,
  }),
  createFallbackTask({
    id: "t-3",
    ticketCode: "FL0003V",
    project: "FlowTrack",
    name: "Timeline Motion",
    priority: "Medium",
    status: "In Progress",
    start: "2025-09-23T10:00:00",
    progress: 48,
  }),
  createFallbackTask({
    id: "t-4",
    ticketCode: "FL0004V",
    project: "UX Team",
    name: "Deploy Production",
    priority: "Critical",
    status: "Delayed",
    start: "2025-09-24T11:00:00",
    progress: 118,
  }),
];

const PRIORITY_THEMES = {
  Low: {
    gradient: "linear-gradient(90deg, #60a5fa 0%, #22c55e 100%)",
    badgeBg: "rgba(34,197,94,0.18)",
    badgeColor: "#047857",
  },
  Medium: {
    gradient: "linear-gradient(90deg, #fde047 0%, #f97316 100%)",
    badgeBg: "rgba(250,204,21,0.25)",
    badgeColor: "#b45309",
  },
  High: {
    gradient: "linear-gradient(90deg, #fb923c 0%, #ef4444 100%)",
    badgeBg: "rgba(249,115,22,0.25)",
    badgeColor: "#c2410c",
  },
  Critical: {
    gradient: "linear-gradient(90deg, #f87171 0%, #dc2626 100%)",
    badgeBg: "rgba(248,113,113,0.25)",
    badgeColor: "#b91c1c",
  },
};

const STATUS_THEMES = {
  "In Progress": { bg: "rgba(59,130,246,0.18)", color: "#1d4ed8" },
  Completed: { bg: "rgba(34,197,94,0.18)", color: "#166534" },
  Blocked: { bg: "rgba(248,113,113,0.25)", color: "#b91c1c" },
};

const LEGEND_ITEMS = [
  { label: "In Progress", color: "#3b82f6" },
  { label: "Completed", color: "#22c55e" },
  { label: "Overdue", color: "#ef4444" },
];

const PRIORITY_FILTER_OPTIONS = ["All priorities", "Low", "Medium", "High", "Critical"];
const STATUS_FILTER_OPTIONS = ["All statuses", "In Progress", "Completed", "Blocked"];

const containerStyle = {
  minHeight: "100vh",
  background: "linear-gradient(180deg, #e0f2ff 0%, #ffffff 45%, #ffffff 100%)",
  padding: "32px 24px 56px",
  fontFamily: "'Inter', 'Segoe UI', sans-serif",
};

const shellStyle = {
  maxWidth: "1180px",
  margin: "0 auto",
  display: "flex",
  flexDirection: "column",
  gap: "24px",
};

const headerTitleStyle = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
  fontSize: "32px",
  fontWeight: 700,
  color: "#0f172a",
};

const statCardStyle = {
  background: "rgba(255,255,255,0.9)",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 12px 28px rgba(15,23,42,0.08)",
  display: "grid",
  gap: "4px",
};

const badgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  borderRadius: "999px",
  padding: "6px 12px",
  fontSize: "13px",
  fontWeight: 600,
};

const searchWrapperStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "8px",
  borderRadius: "14px",
  border: "1px solid rgba(148,163,184,0.35)",
  background: "rgba(255,255,255,0.92)",
  padding: "10px 14px",
  boxShadow: "0 4px 12px rgba(148,163,184,0.12)",
};

const selectStyle = {
  borderRadius: "14px",
  border: "1px solid rgba(148,163,184,0.35)",
  padding: "10px 14px",
  fontSize: "14px",
  color: "#1f2937",
  background: "rgba(255,255,255,0.9)",
  boxShadow: "0 4px 12px rgba(148,163,184,0.12)",
};

const legendStyle = {
  display: "flex",
  gap: "16px",
  fontSize: "13px",
  color: "#475569",
  flexWrap: "wrap",
};

const tableWrapperStyle = {
  background: "rgba(255,255,255,0.95)",
  borderRadius: "24px",
  boxShadow: "0 18px 40px rgba(15,23,42,0.08)",
  overflow: "hidden",
};

const tableHeadCellStyle = {
  background: "rgba(224,242,254,0.65)",
  padding: "16px 18px",
  fontSize: "13px",
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#334155",
  fontWeight: 700,
  borderBottom: "1px solid rgba(148,163,184,0.2)",
};

const cellStyle = {
  padding: "18px",
  fontSize: "15px",
  color: "#1f2937",
  borderBottom: "1px solid rgba(226,232,240,0.6)",
  verticalAlign: "middle",
};

const formatDate = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
};

const parseDateTime = (value) => {
  if (!value) return null;
  if (value instanceof Date) return value;
  const normalized = typeof value === "string" ? value.replace(" ", "T") : value;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
};

const formatDurationMinutes = (minutes) => {
  if (minutes == null) return "—";
  const total = Math.max(0, Math.round(minutes));
  const hours = Math.floor(total / 60);
  const mins = total % 60;
  const parts = [];
  if (hours) parts.push(`${hours} hr${hours !== 1 ? "s" : ""}`);
  if (mins || !hours) parts.push(`${mins} min${mins !== 1 ? "s" : ""}`);
  return parts.join(" ");
};

const normalizeEmail = (value) => {
  if (!value || typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed || !trimmed.includes("@")) return null;
  return trimmed.toLowerCase();
};

const toEmailArray = (value) => {
  if (!value) return [];
  const source = Array.isArray(value)
    ? value
    : value
        .toString()
        .split(",")
        .map((entry) => entry.trim());
  return Array.from(new Set(source.map((entry) => normalizeEmail(entry)).filter(Boolean)));
};

const normalizePriority = (priority) => {
  const key = (priority || "Medium").toString().toLowerCase();
  if (key.includes("critical")) return "Critical";
  if (key.includes("high")) return "High";
  if (key.includes("low")) return "Low";
  return "Medium";
};

const normalizeStatus = (status) => {
  const raw = (status || "In Progress").toString().trim().toLowerCase();
  const compact = raw.replace(/\s+/g, "");
  if (raw === "done" || raw === "completed" || compact === "complete" || compact === "resolved" || compact === "closed") {
    return "Completed";
  }
  if (raw === "blocked" || raw === "delayed" || compact === "blocked") return "Blocked";
  if (compact === "inprogress" || compact === "analysis" || compact === "codereview" || compact === "qa" || compact === "milestone") {
    return "In Progress";
  }
  if (raw === "in progress" || compact === "inprogress") return "In Progress";
  if (raw === "todo" || raw === "planned") return "In Progress";
  return status
    ? status
        .toString()
        .trim()
        .toLowerCase()
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : "In Progress";
};

const isBlockedStatus = (status) => status === "Blocked";

const getCompletionDurationMinutes = (task) => {
  if (!task) return null;

  if (Number.isFinite(task.accumulatedMinutes) && task.accumulatedMinutes > 0) {
    return Math.max(0, Number(task.accumulatedMinutes));
  }

  const completedAt =
    parseDateTime(task.completedAt) ||
    parseDateTime(task.completed_at) ||
    parseDateTime(task.end);
  const startedAt =
    parseDateTime(task.lastStartedAt) ||
    parseDateTime(task.start) ||
    parseDateTime(task.created_at);

  if (completedAt && startedAt) {
    return Math.max(0, (completedAt.getTime() - startedAt.getTime()) / 60000);
  }

  return null;
};

const mapApiTaskToAdminRow = (task, projectLookup = {}) => {
  const priority = normalizePriority(task.priority);
  const status = normalizeStatus(task.status);
  const window = PRIORITY_WINDOWS[priority] || PRIORITY_WINDOWS.Medium;
  const stageMinutesArray = Array.isArray(task.stage_minutes) ? task.stage_minutes : [];
  const totalMinutes =
    (stageMinutesArray.length > 1 && Number(stageMinutesArray[1])) || window.totalMinutes;

  const ticketMeta =
    projectLookup?.[task.ticket_id] ??
    projectLookup?.[task.ticket_id != null ? task.ticket_id.toString() : undefined] ??
    null;

  const startDate = parseDateTime(task.start) || parseDateTime(task.created_at);
  const startIso = startDate ? startDate.toISOString() : null;
  const accumulatedMinutes = Number(task.accumulated_minutes ?? 0);
  const lastStartedAt = task.last_started_at || startIso;
  const endIso =
    startDate && totalMinutes
      ? new Date(startDate.getTime() + totalMinutes * 60000).toISOString()
      : null;
  const projectTitle =
    task.project_title ||
    ticketMeta?.projectTitle ||
    task.project ||
    "—";
  const projectId = task.project_id ?? ticketMeta?.projectId ?? null;
  const ticketCode =
    task.ticket_code ||
    ticketMeta?.ticketCode ||
    (task.ticket_id != null ? `FL${String(task.ticket_id).padStart(4, "0")}V` : null);
  const ownerEmail = normalizeEmail(
    task.owner_email || task.ownerEmail || task.email || ticketMeta?.ownerEmail || null
  );
  const userEntriesRaw = Array.isArray(task.user_entries) ? task.user_entries : [];
  const userEntryEmails = userEntriesRaw
    .map((entry) =>
      normalizeEmail(entry?.owner_email ?? entry?.ownerEmail ?? entry?.email ?? null)
    )
    .filter(Boolean);
  const teamMembers = [
    ...toEmailArray(task.team_members),
    ...toEmailArray(ticketMeta?.teamEmails),
  ];
  const leads = [
    ...toEmailArray(task.leads),
    ...toEmailArray(ticketMeta?.leadEmails),
  ];
  const assigneeEmail =
    normalizeEmail(task.assignee_email) ||
    normalizeEmail(task.assigneeEmail) ||
    normalizeEmail(task.assigneeEmailId) ||
    normalizeEmail(task.assignee) ||
    normalizeEmail(ticketMeta?.assigneeEmail) ||
    userEntryEmails[0] ||
    teamMembers[0] ||
    leads[0] ||
    ownerEmail ||
    null;

  return {
    id: `timeline-${task.id ?? task.ticket_id}`,
    ticketId: task.ticket_id ?? task.id,
    ticketCode,
    projectId,
    project: projectTitle,
    name: task.name || `Ticket ${task.ticket_id ?? task.id}`,
    priority,
    status,
    start: startIso,
    end: endIso,
    duration: window.label,
    totalMinutes,
    accumulatedMinutes: Number.isFinite(accumulatedMinutes) ? accumulatedMinutes : 0,
    lastStartedAt,
    isPaused: Boolean(task.is_paused),
    completedAt: task.completed_at || task.completedAt || null,
    blockedAt: task.blocked_at,
    completed_at: task.completed_at,
    ownerEmail,
    assigneeEmail,
  };
};

const buildSummaryFromTasks = (list) => {
  const priorityCounts = { Low: 0, Medium: 0, High: 0, Critical: 0 };
  let total = 0;
  let critical = 0;
  let completed = 0;
  let inProgress = 0;

  list.forEach((task) => {
    total += 1;
    const priority = normalizePriority(task.priority);
    if (priorityCounts[priority] != null) {
      priorityCounts[priority] += 1;
    }
    if (priority === "Critical") {
      critical += 1;
    }
    const status = normalizeStatus(task.status);
    if (status === "Completed") {
      completed += 1;
    } else if (status === "In Progress") {
      inProgress += 1;
    }
  });

  return {
    total,
    critical,
    completed,
    inProgress,
    priorityCounts,
  };
};

const convertStatsPayload = (payload) => {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const priorityCounts = { Low: 0, Medium: 0, High: 0, Critical: 0 };
  if (payload.priority_counts && typeof payload.priority_counts === "object") {
    Object.entries(payload.priority_counts).forEach(([key, value]) => {
      const priority = normalizePriority(key);
      if (priorityCounts[priority] != null && Number.isFinite(value)) {
        priorityCounts[priority] = value;
      }
    });
  }
  return {
    total: payload.total_tasks ?? 0,
    critical: payload.critical_tasks ?? (priorityCounts.Critical ?? 0),
    completed: payload.completed_tasks ?? 0,
    inProgress: payload.in_progress_tasks ?? 0,
    priorityCounts,
  };
};

const computeProgressMeta = (task, now) => {
  const window = PRIORITY_WINDOWS[task.priority] || PRIORITY_WINDOWS.Medium;
  const totalMinutes = task.totalMinutes || window.totalMinutes;
  const status = task.status;
  const isCompleted = status === "Completed";
  const isBlocked = isBlockedStatus(status);
  const completionMinutesOverride = getCompletionDurationMinutes(task);
  const completionLabelOverride =
    completionMinutesOverride != null
      ? formatDurationMinutes(completionMinutesOverride)
      : null;
  const isEffectivelyPaused = isCompleted || isBlocked || task.isPaused;

  if (totalMinutes && Number.isFinite(totalMinutes)) {
    const baseAccumulated = Math.max(0, Number(task.accumulatedMinutes ?? 0));
    const referenceStart =
      parseDateTime(task.lastStartedAt) || parseDateTime(task.start) || new Date();

    let elapsedMinutes = baseAccumulated;
    if (!isEffectivelyPaused && referenceStart) {
      elapsedMinutes += Math.max(0, (now - referenceStart.getTime()) / 60000);
    }

    const percentRaw = totalMinutes > 0 ? (elapsedMinutes / totalMinutes) * 100 : 0;
    const percent = Math.min(Math.max(percentRaw, 0), 100);
    const overtimePercent =
      isCompleted || isBlocked ? 0 : percentRaw > 100 ? percentRaw - 100 : 0;
    const remainingMinutes = Math.max(totalMinutes - elapsedMinutes, 0);
    const overdueMinutes = Math.max(elapsedMinutes - totalMinutes, 0);
    const overdue = !isCompleted && !isBlocked && overdueMinutes > 0;

    if (isCompleted) {
      const completionLabel =
        completionLabelOverride || formatDurationMinutes(elapsedMinutes);
      return {
        percent,
        overtimePercent: 0,
        overdue: false,
        remainingMinutes: 0,
        overdueMinutes: 0,
        elapsedMinutes,
        timeLabel: completionLabel ? `Completed in ${completionLabel}` : "Completed",
        elapsedLabel:
          completionLabel || `${Math.round(Math.min(percentRaw, 100))}% elapsed`,
      };
    }

    if (isBlocked) {
      return {
        percent,
        overtimePercent: 0,
        overdue: false,
        remainingMinutes,
        overdueMinutes: 0,
        elapsedMinutes,
        timeLabel: "Paused (Blocked)",
        elapsedLabel: `${Math.round(Math.min(percentRaw, 100))}% elapsed`,
      };
    }

    const timeLabel = overdue
      ? `Overdue by ${formatDurationMinutes(overdueMinutes)}`
      : `${formatDurationMinutes(remainingMinutes)} left`;
    const elapsedLabel = `${Math.round(Math.min(percentRaw, 100))}% elapsed`;

    return {
      percent,
      overtimePercent,
      overdue,
      remainingMinutes,
      overdueMinutes,
      elapsedMinutes,
      timeLabel,
      elapsedLabel,
    };
  }

  const basePercent = Math.min(Math.max(task.progress ?? 0, 0), 100);
  const percent = isCompleted ? 100 : basePercent;
  const overtimePercent =
    !isCompleted && !isBlocked && basePercent > 100 ? basePercent - 100 : 0;
  const overdue =
    !isCompleted &&
    !isBlocked &&
    (overtimePercent > 0 || (task.end && parseDateTime(task.end)?.getTime() < now));

  const completionMinutes =
    isCompleted && completionMinutesOverride != null
      ? completionMinutesOverride
      : null;
  const completionLabel =
    completionMinutes != null
      ? formatDurationMinutes(completionMinutes)
      : completionLabelOverride;

  return {
    percent: Math.min(percent, 100),
    overtimePercent,
    overdue,
    remainingMinutes: null,
    overdueMinutes: null,
    elapsedMinutes: null,
    timeLabel: isCompleted
      ? completionLabel
        ? `Completed in ${completionLabel}`
        : "Completed"
      : isBlocked
      ? "Paused (Blocked)"
      : overdue
      ? "Overdue"
      : `${Math.max(0, 100 - percent)}% remaining`,
    elapsedLabel:
      completionLabel ||
      `${Math.round(Math.min(isCompleted ? 100 : percent, 100))}% elapsed`,
  };
};

const Timeline = () => {
  const [tasks, setTasks] = useState(INITIAL_TASKS);
  const [stats, setStats] = useState(null);

  const [priorityFilter, setPriorityFilter] = useState(PRIORITY_FILTER_OPTIONS[0]);
  const [statusFilter, setStatusFilter] = useState(STATUS_FILTER_OPTIONS[0]);
  const [projectFilter, setProjectFilter] = useState("All projects");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [now, setNow] = useState(() => Date.now());
  const [clockOffset, setClockOffset] = useState(0);

  const fetchTimelineData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [timelineRes, adminRes, statsRes] = await Promise.all([
        fetch(TIMELINE_URL),
        fetch(ADMIN_TICKETS_URL),
        fetch(TIMELINE_STATS_URL).catch(() => null),
      ]);

      let projectLookup = {};
      if (adminRes.ok) {
        const adminTickets = await adminRes.json();
        projectLookup = adminTickets.reduce((acc, ticket) => {
          const entry = {
            projectTitle: ticket.project_title || "—",
            projectId: ticket.project_id,
            ticketCode: ticket.ticket_code || null,
            assigneeEmail: normalizeEmail(ticket.assignee_email || ticket.assignee || ticket.owner_email || null),
            ownerEmail: normalizeEmail(ticket.owner_email || ticket.ownerEmail || ticket.reporter_email || ticket.reporter || null),
            teamEmails: toEmailArray(ticket.team_members),
            leadEmails: toEmailArray(ticket.leads),
          };

          const rawId = ticket.ticket_id;
          if (rawId !== undefined && rawId !== null) {
            acc[rawId] = entry;
            const stringKey = rawId.toString();
            acc[stringKey] = entry;
          }
          return acc;
        }, {});
      }

      if (timelineRes.ok) {
        const timelinePayload = await timelineRes.json();
        let tasksPayload = [];
        let serverNowValue = null;

        if (timelinePayload && !Array.isArray(timelinePayload)) {
          tasksPayload = Array.isArray(timelinePayload.tasks) ? timelinePayload.tasks : [];
          if (timelinePayload.server_now) {
            const parsed = Date.parse(timelinePayload.server_now);
            if (!Number.isNaN(parsed)) {
              serverNowValue = parsed;
            }
          }
        } else if (Array.isArray(timelinePayload)) {
          tasksPayload = timelinePayload;
        }

        if (serverNowValue !== null) {
          setClockOffset(serverNowValue - Date.now());
        } else {
          setClockOffset(0);
        }

        const mappedTasks = tasksPayload.map((task) =>
          mapApiTaskToAdminRow(task, projectLookup)
        );

        if (mappedTasks.length) {
          setStats(buildSummaryFromTasks(mappedTasks));
          setTasks(mappedTasks);
        } else {
          let statsSummary = null;
          if (statsRes && statsRes.ok) {
            try {
              const statsPayload = await statsRes.json();
              statsSummary = convertStatsPayload(statsPayload);
            } catch (err) {
              console.warn("Admin timeline: failed to parse stats payload", err);
            }
          }
          setStats(statsSummary ?? buildSummaryFromTasks(INITIAL_TASKS));
          setTasks(INITIAL_TASKS);
        }
      } else {
        setTasks(INITIAL_TASKS);
        setStats(buildSummaryFromTasks(INITIAL_TASKS));
        setClockOffset(0);
        setError("Unable to load timeline data");
      }
    } catch (err) {
      console.error("Admin timeline: failed to fetch tasks", err);
      setError(err.message || "Failed to load timeline data");
      setTasks(INITIAL_TASKS);
      setStats(buildSummaryFromTasks(INITIAL_TASKS));
      setClockOffset(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTimelineData();
    const refreshInterval = setInterval(fetchTimelineData, 60000);
    return () => clearInterval(refreshInterval);
  }, [fetchTimelineData]);

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const uniqueProjects = useMemo(() => {
    const names = Array.from(new Set(tasks.map((task) => task.project)));
    return ["All projects", ...names];
  }, [tasks]);

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (priorityFilter !== "All priorities" && task.priority !== priorityFilter) {
        return false;
      }
      if (statusFilter !== "All statuses" && task.status !== statusFilter) {
        return false;
      }
      if (projectFilter !== "All projects" && task.project !== projectFilter) {
        return false;
      }
      if (searchTerm.trim()) {
        const needle = searchTerm.trim().toLowerCase();
        return (
          task.name.toLowerCase().includes(needle) ||
          (task.ticketCode && task.ticketCode.toLowerCase().includes(needle)) ||
          task.project.toLowerCase().includes(needle) ||
          task.status.toLowerCase().includes(needle)
        );
      }
      return true;
    });
  }, [tasks, priorityFilter, statusFilter, projectFilter, searchTerm]);

  const isDefaultFilterState =
    priorityFilter === "All priorities" &&
    statusFilter === "All statuses" &&
    projectFilter === "All projects" &&
    !searchTerm.trim();

  const displayTasks = useMemo(() => {
    if (statusFilter === "Completed") {
      return filteredTasks;
    }
    return filteredTasks.filter((task) => task.status !== "Completed");
  }, [filteredTasks, statusFilter]);

  const summary = useMemo(() => {
    if (isDefaultFilterState && stats) {
      return stats;
    }
    return buildSummaryFromTasks(filteredTasks);
  }, [stats, filteredTasks, isDefaultFilterState]);

  const cardMetrics = useMemo(() => {
    let activeTotal = 0;
    let completedTotal = 0;
    const priorityStatusCounts = {
      Low: { active: 0, completed: 0 },
      Medium: { active: 0, completed: 0 },
      High: { active: 0, completed: 0 },
      Critical: { active: 0, completed: 0 },
    };

    filteredTasks.forEach((task) => {
      const priority = normalizePriority(task.priority);
      const status = normalizeStatus(task.status);
      if (status === "Completed") {
        completedTotal += 1;
        if (priorityStatusCounts[priority]) {
          priorityStatusCounts[priority].completed += 1;
        }
      } else {
        activeTotal += 1;
        if (priorityStatusCounts[priority]) {
          priorityStatusCounts[priority].active += 1;
        }
      }
    });

    return { activeTotal, completedTotal, priorityStatusCounts };
  }, [filteredTasks]);

  const totalCardValue =
    statusFilter === "Completed" ? filteredTasks.length : cardMetrics.activeTotal;

  const priorityCardLabel = priorityFilter;

  const priorityCardValue = useMemo(() => {
    if (priorityFilter === "All priorities") {
      return statusFilter === "Completed"
        ? cardMetrics.completedTotal
        : cardMetrics.activeTotal;
    }

    const counts = cardMetrics.priorityStatusCounts?.[priorityFilter];
    if (!counts) {
      return 0;
    }
    return statusFilter === "Completed" ? counts.completed : counts.active;
  }, [cardMetrics, priorityFilter, statusFilter]);

  const priorityCardColor = useMemo(() => {
    if (priorityFilter === "All priorities") {
      return "#1f2937";
    }
    return PRIORITY_THEMES[priorityFilter]?.badgeColor || "#dc2626";
  }, [priorityFilter]);

  const statusCounts = useMemo(() => {
    const counts = {};
    filteredTasks.forEach((task) => {
      const status = normalizeStatus(task.status);
      counts[status] = (counts[status] || 0) + 1;
    });
    return counts;
  }, [filteredTasks]);

  const statusCardLabel = statusFilter;

  const statusCardValue = useMemo(() => {
    if (statusFilter === "All statuses") {
      return filteredTasks.length;
    }
    const normalized = normalizeStatus(statusFilter);
    return statusCounts[normalized] ?? 0;
  }, [filteredTasks.length, statusCounts, statusFilter]);

  const statusCardColor = useMemo(() => {
    if (statusFilter === "All statuses") {
      return "#1f2937";
    }
    const normalized = normalizeStatus(statusFilter);
    return STATUS_THEMES[normalized]?.color || "#16a34a";
  }, [statusFilter]);

  const resetFilters = () => {
    setPriorityFilter(PRIORITY_FILTER_OPTIONS[0]);
    setStatusFilter(STATUS_FILTER_OPTIONS[0]);
    setProjectFilter("All projects");
    setSearchTerm("");
  };

  const handleRefresh = () => {
    resetFilters();
    fetchTimelineData();
  };

  return (
    <div style={containerStyle}>
      <div style={shellStyle}>
        <header>
          <div style={headerTitleStyle}>
            <FiCalendar size={32} color="#2563eb" />
            Workspace Timeline
          </div>
          <p style={{ marginTop: "6px", color: "#475569", fontSize: "15px" }}>
            Track what the team is shipping across every project.
          </p>
          <div
            style={{
              marginTop: "20px",
              display: "grid",
              gap: "18px",
              gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            }}
          >
            <div style={statCardStyle}>
              <span style={{ fontSize: "13px", letterSpacing: "0.08em", textTransform: "uppercase", color: "#64748b" }}>
                Total Tasks
              </span>
              <span style={{ fontSize: "30px", fontWeight: 700 }}>{totalCardValue}</span>
            </div>
            <div style={statCardStyle}>
              <span style={{ fontSize: "13px", letterSpacing: "0.08em", textTransform: "uppercase", color: "#64748b" }}>
                {priorityCardLabel}
              </span>
              <span style={{ fontSize: "30px", fontWeight: 700, color: priorityCardColor }}>
                {priorityCardValue}
              </span>
            </div>
            <div style={statCardStyle}>
              <span style={{ fontSize: "13px", letterSpacing: "0.08em", textTransform: "uppercase", color: "#64748b" }}>
                {statusCardLabel}
              </span>
              <span style={{ fontSize: "30px", fontWeight: 700, color: statusCardColor }}>{statusCardValue}</span>
            </div>
            <div style={statCardStyle}>
              <span style={{ fontSize: "13px", letterSpacing: "0.08em", textTransform: "uppercase", color: "#64748b" }}>
                In Progress
              </span>
              <span style={{ fontSize: "30px", fontWeight: 700, color: "#2563eb" }}>{summary.inProgress}</span>
            </div>
          </div>

          <div
            style={{
              marginTop: "24px",
              display: "flex",
              flexWrap: "wrap",
              gap: "14px",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
              <div style={searchWrapperStyle}>
                <FiSearch color="#64748b" size={18} />
                <input
                  type="search"
                  placeholder="Search tasks, people, status…"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  style={{ border: "none", outline: "none", fontSize: "14px", minWidth: "200px", background: "transparent" }}
                />
              </div>
              <div style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                <FiFilter color="#475569" />
                <select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value)} style={selectStyle}>
                  {PRIORITY_FILTER_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} style={selectStyle}>
                  {STATUS_FILTER_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <select value={projectFilter} onChange={(event) => setProjectFilter(event.target.value)} style={selectStyle}>
                  {uniqueProjects.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button
                type="button"
                onClick={resetFilters}
                style={{
                  borderRadius: "14px",
                  border: "1px solid rgba(148,163,184,0.35)",
                  background: "rgba(248,250,252,0.8)",
                  padding: "10px 16px",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "#1f2937",
                  cursor: "pointer",
                }}
              >
                Clear filters
              </button>
              <button
                type="button"
                onClick={handleRefresh}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "10px 16px",
                  borderRadius: "14px",
                  border: "none",
                  background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
                  color: "#ffffff",
                  fontWeight: 600,
                  cursor: "pointer",
                  boxShadow: "0 12px 24px rgba(37,99,235,0.18)",
                }}
              >
                <FiRefreshCcw /> Refresh
              </button>
            </div>
          </div>
        </header>

        <div style={legendStyle}>
          {LEGEND_ITEMS.map((item) => (
            <span key={item.label} style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
              <span
                style={{
                  width: "10px",
                  height: "10px",
                  borderRadius: "999px",
                  background: item.color,
                  boxShadow: "0 0 8px rgba(148,163,184,0.25)",
                }}
              />
              {item.label}
            </span>
          ))}
        </div>

        {(loading || error) && (
          <div style={{ fontSize: "13px", color: error ? "#b91c1c" : "#64748b", marginBottom: "12px" }}>
            {loading ? "Syncing live ticket timeline…" : `⚠ ${error}`}
          </div>
        )}

        <div style={tableWrapperStyle}>
          <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0 }}>
            <thead>
              <tr>
                <th style={{ ...tableHeadCellStyle, borderTopLeftRadius: "24px" }}>Project</th>
                <th style={tableHeadCellStyle}>Ticket</th>
                <th style={tableHeadCellStyle}>Schedule</th>
                <th style={tableHeadCellStyle}>Status</th>
                <th style={{ ...tableHeadCellStyle, borderTopRightRadius: "24px" }}>Timeline</th>
              </tr>
            </thead>
            <tbody>
              {displayTasks.map((task, index) => {
                const meta = computeProgressMeta(task, now + clockOffset);
                const percent = meta.percent;
                const overdue = meta.overdue;
                const finishedPercent = Math.min(percent, 100);
                const overtimePercent = Math.max(meta.overtimePercent, 0);
                const overtimeWidth = Math.min(Math.max(overtimePercent, 0), 200);
                const priorityTheme = PRIORITY_THEMES[task.priority] || PRIORITY_THEMES.Medium;
                const statusTheme = STATUS_THEMES[task.status] || {
                  bg: "rgba(148,163,184,0.18)",
                  color: "#334155",
                };
                const timeBadgePalette = overdue
                  ? { background: "rgba(153, 27, 27, 0.9)", color: "#fee2e2" }
                  : { background: "rgba(209,250,229,0.75)", color: "#047857" };

                return (
                  <motion.tr
                    key={task.id}
                    initial={{ opacity: 0, translateY: 12 }}
                    animate={{ opacity: 1, translateY: 0 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ translateY: -2, boxShadow: "0 18px 32px rgba(15,23,42,0.10)" }}
                  >
                    <td style={cellStyle}>
                      <div style={{ fontWeight: 600 }}>{task.project}</div>
                      <div style={{ fontSize: "13px", color: "#64748b", marginTop: "4px" }}>{task.duration}</div>
                    </td>
                    <td style={cellStyle}>
                      <div style={{ fontWeight: 600 }}>
                        {task.ticketCode || `Ticket ${task.ticketId}`}
                      </div>
                      {task.name && (
                        <div style={{ fontSize: "13px", color: "#475569", marginTop: "4px" }}>
                          {task.name}
                        </div>
                      )}
                      {task.assigneeEmail && (
                        <div style={{ fontSize: "12px", color: "#64748b", marginTop: "2px" }}>
                          {task.assigneeEmail}
                        </div>
                      )}
                      <div style={{ fontSize: "13px", color: "#64748b", marginTop: "4px" }}>
                        SLA window: {task.duration}
                      </div>
                    </td>
                    <td style={cellStyle}>
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                          <FiCalendar color="#94a3b8" />
                          {formatDate(task.start)}
                        </span>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                          <FiCalendar color="#94a3b8" />
                          {formatDate(task.end)}
                        </span>
                      </div>
                    </td>
                    <td style={cellStyle}>
                      <div style={{ ...badgeStyle, background: statusTheme.bg, color: statusTheme.color }}>
                        {task.status}
                      </div>
                      <div
                        style={{
                          ...badgeStyle,
                          marginTop: "8px",
                          background: priorityTheme.badgeBg,
                          color: priorityTheme.badgeColor,
                        }}
                      >
                        {task.priority}
                      </div>
                    </td>
                    <td style={cellStyle}>
                      <div
                        style={{
                          width: "100%",
                          height: "12px",
                          borderRadius: "999px",
                          background: "rgba(226,232,240,0.7)",
                          overflow: "visible",
                          position: "relative",
                        }}
                      >
                        <motion.div
                          style={{
                            height: "100%",
                            borderRadius: "999px",
                            background: priorityTheme.gradient,
                          }}
                          initial={{ width: 0 }}
                          animate={{ width: `${finishedPercent}%` }}
                          transition={{ duration: 0.8, ease: "easeOut" }}
                        />
                        {overtimePercent > 0 && (
                          <motion.div
                            style={{
                              position: "absolute",
                              top: 0,
                              bottom: 0,
                              left: `${finishedPercent}%`,
                              width: `${overtimeWidth}%`,
                              borderRadius: "0 999px 999px 0",
                              background: "rgba(153, 27, 27, 0.9)",
                              paddingRight: "8px",
                              paddingLeft: "8px",
                              display: "flex",
                              alignItems: "center",
                              color: "#fee2e2",
                              fontSize: "10px",
                              letterSpacing: "0.02em",
                            }}
                            initial={{ width: 0 }}
                            animate={{ width: `${overtimeWidth}%` }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                          >
                            {meta.overdueMinutes > 0 && overtimePercent >= 5 && (
                              <span>{formatDurationMinutes(meta.overdueMinutes)}</span>
                            )}
                          </motion.div>
                        )}
                      </div>
                      <div style={{ marginTop: "8px", display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#64748b" }}>
                        <span>
                          {formatDate(task.start)} → {formatDate(task.end)}
                        </span>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                          {meta.elapsedLabel}
                          <span
                            style={{
                              ...badgeStyle,
                              padding: "4px 10px",
                              fontSize: "11px",
                              background: timeBadgePalette.background,
                              color: timeBadgePalette.color,
                            }}
                          >
                            {meta.timeLabel}
                          </span>
                        </span>
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
              {displayTasks.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ ...cellStyle, textAlign: "center", padding: "48px" }}>
                    No tasks match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Timeline;

