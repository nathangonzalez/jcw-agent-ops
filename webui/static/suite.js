const fmtTime = (ts) => {
  if (!ts) return "unknown";
  const date = new Date(ts * 1000);
  return date.toLocaleString();
};

const setText = (id, value) => {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? "";
};

const loadSprint = async () => {
  const res = await fetch("/api/sprint");
  const data = await res.json();
  setText("sprint-content", data.content || "No sprint data.");
  setText("sprint-updated", `updated ${fmtTime(data.updated_at)}`);
};

const loadBacklog = async () => {
  const res = await fetch("/api/backlog");
  const data = await res.json();
  setText("backlog-content", data.content || "No backlog data.");
  setText("backlog-updated", `updated ${fmtTime(data.updated_at)}`);
};

const loadOps = async () => {
  const res = await fetch("/api/ops");
  const data = await res.json();
  setText("ops-dms", data.dms);
  setText("ops-replies", data.replies);
  setText("ops-errors", data.errors);
  setText("ops-mentions", data.mentions);
  setText("ops-runtime", data.runtime_errors);
  setText("ops-path", data.log_path);
  setText("ops-event", data.last_event);
  setText("ops-last", "live");
};

const refreshAll = async () => {
  await Promise.all([loadSprint(), loadBacklog(), loadOps()]);
};

document.getElementById("refresh").addEventListener("click", refreshAll);

refreshAll();