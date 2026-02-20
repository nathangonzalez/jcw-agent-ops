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

const loadMetrics = async () => {
  const res = await fetch("/api/metrics");
  const data = await res.json();
  if (data.error) {
    setText("metrics-updated", data.error);
    return;
  }
  const codex24 = (data.codex_prompt_tokens_24h || 0) + (data.codex_output_tokens_24h || 0);
  const codex1 = (data.codex_prompt_tokens_1h || 0) + (data.codex_output_tokens_1h || 0);
  const anth24 = (data.anthropic_prompt_tokens_24h || 0) + (data.anthropic_output_tokens_24h || 0);
  const anth1 = (data.anthropic_prompt_tokens_1h || 0) + (data.anthropic_output_tokens_1h || 0);
  setText("metrics-codex-24h", codex24);
  setText("metrics-codex-1h", codex1);
  setText("metrics-anth-24h", anth24);
  setText("metrics-anth-1h", anth1);
  setText("metrics-claw-24h", data.openclaw_calls_24h || 0);
  setText("metrics-replies-1h", data.slack_replies_1h || 0);
  setText("metrics-agents", data.supervisor_backlog_summary || "n/a");
  if (data.gcp_cost_24h_usd !== null && data.gcp_cost_24h_usd !== undefined) {
    setText("metrics-gcp-24h", `$${data.gcp_cost_24h_usd}`);
  } else {
    setText("metrics-gcp-24h", data.gcp_cost_status || "n/a");
  }
  const vm = [
    data.vm_load_1m ? `load=${data.vm_load_1m}` : null,
    data.vm_mem_free_gb ? `mem_free_gb=${data.vm_mem_free_gb}` : null,
    data.vm_disk_free_gb ? `disk_free_gb=${data.vm_disk_free_gb}` : null,
  ]
    .filter(Boolean)
    .join(" | ");
  setText("metrics-vm", vm || "n/a");
  setText("metrics-updated", data.updated_at || "live");
};

const renderApps = (apps) => {
  const grid = document.getElementById("app-grid");
  if (!grid) return;
  grid.innerHTML = "";
  if (!apps || !apps.length) {
    grid.innerHTML = "<div class='empty'>No apps configured.</div>";
    return;
  }
  apps.forEach((app) => {
    const card = document.createElement("div");
    card.className = "app-card";
    const status = app.status || "dev";
    const primary = app.primary_url || "";
    const patch = app.patch_url || "";
    card.innerHTML = `
      <div class="app-header">
        <div class="app-title">${app.name || "Unnamed"}</div>
        <span class="app-status ${status}">${status}</span>
      </div>
      <div class="app-desc">${app.description || ""}</div>
      <div class="app-links">
        ${primary ? `<a class="btn small" href="${primary}" target="_blank">Open</a>` : ""}
        ${patch ? `<a class="btn ghost small" href="${patch}" target="_blank">Patch</a>` : ""}
      </div>
      <div class="app-meta mono small">${app.repo || ""}</div>
    `;
    grid.appendChild(card);
  });
};

const loadApps = async () => {
  const res = await fetch("/api/apps");
  const data = await res.json();
  renderApps(data.items || []);
};

const refreshAll = async () => {
  await Promise.all([loadApps(), loadSprint(), loadBacklog(), loadOps(), loadMetrics()]);
};

document.getElementById("refresh").addEventListener("click", refreshAll);

refreshAll();
