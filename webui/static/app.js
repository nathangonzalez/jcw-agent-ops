const statusEl = document.getElementById("statusline");
const cardsEl = document.getElementById("cards");
const qEl = document.getElementById("q");
const tagEl = document.getElementById("tag");
const statusFilterEl = document.getElementById("status");
const limitEl = document.getElementById("limit");
const refreshBtn = document.getElementById("refresh");
const toggleAddBtn = document.getElementById("toggle-add");
const addPanel = document.getElementById("add-panel");
const countTotal = document.getElementById("count-total");
const countOpen = document.getElementById("count-open");
const countDone = document.getElementById("count-done");
const tagOptions = document.getElementById("tag-options");

const newTitle = document.getElementById("new-title");
const newTags = document.getElementById("new-tags");
const newStatus = document.getElementById("new-status");
const newDue = document.getElementById("new-due");
const newPriority = document.getElementById("new-priority");
const newNext = document.getElementById("new-next");
const newNotes = document.getElementById("new-notes");
const saveNew = document.getElementById("save-new");

function setStatus(text) {
  statusEl.textContent = text;
}

function buildQuery() {
  const params = new URLSearchParams();
  if (qEl.value.trim()) params.set("q", qEl.value.trim());
  if (tagEl.value.trim()) params.set("tag", tagEl.value.trim());
  if (statusFilterEl.value) params.set("status", statusFilterEl.value);
  params.set("limit", limitEl.value || "200");
  return params.toString();
}

async function fetchTasks() {
  setStatus("Loading...");
  const qs = buildQuery();
  const res = await fetch(`/api/tasks?${qs}`);
  const data = await res.json();
  renderTasks(data.items || []);
  setStatus(`Loaded ${data.items.length} tasks`);
}

async function fetchTags() {
  const res = await fetch("/api/tags");
  const data = await res.json();
  if (!data.items) return;
  tagOptions.innerHTML = "";
  data.items.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = t;
    tagOptions.appendChild(opt);
  });
}

function pillClass(status) {
  if (status === "Completed") return "pill green";
  if (status === "Not Started") return "pill red";
  if (status === "In-Progress") return "pill yellow";
  return "pill";
}

function renderTasks(items) {
  cardsEl.innerHTML = "";
  let done = 0;
  let open = 0;

  items.forEach((item) => {
    if (item.status === "Completed") done += 1;
    else open += 1;

    const card = document.createElement("div");
    card.className = "card";

    const title = document.createElement("h3");
    title.textContent = item.title || "(untitled)";
    card.appendChild(title);

    const meta = document.createElement("div");
    meta.className = "meta";

    const statusPill = document.createElement("span");
    statusPill.className = pillClass(item.status || "");
    statusPill.textContent = item.status || "";
    meta.appendChild(statusPill);

    if (item.due_date) {
      const due = document.createElement("span");
      due.className = "pill";
      due.textContent = `Due ${item.due_date}`;
      meta.appendChild(due);
    }

    if (item.priority) {
      const pr = document.createElement("span");
      pr.className = "pill";
      pr.textContent = `Priority ${item.priority}`;
      meta.appendChild(pr);
    }

    if (item.tags) {
      item.tags.split(",").forEach((t) => {
        const tag = document.createElement("span");
        tag.className = "pill";
        tag.textContent = t.trim();
        meta.appendChild(tag);
      });
    }

    card.appendChild(meta);

    const detail = document.createElement("div");
    detail.className = "meta";
    detail.textContent = item.next_action || item.notes || "";
    card.appendChild(detail);

    const editor = document.createElement("div");
    editor.className = "hidden";

    const statusSelect = document.createElement("select");
    ["Not Started", "In-Progress", "Completed"].forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      if (s === item.status) opt.selected = true;
      statusSelect.appendChild(opt);
    });

    const dueInput = document.createElement("input");
    dueInput.placeholder = "YYYY-MM-DD";
    dueInput.value = item.due_date || "";

    const tagsInput = document.createElement("input");
    tagsInput.placeholder = "tags";
    tagsInput.value = item.tags || "";

    const nextInput = document.createElement("input");
    nextInput.placeholder = "next action";
    nextInput.value = item.next_action || "";

    const notesInput = document.createElement("textarea");
    notesInput.placeholder = "notes";
    notesInput.rows = 2;
    notesInput.value = item.notes || "";

    const saveBtn = document.createElement("button");
    saveBtn.className = "btn";
    saveBtn.textContent = "Save";

    saveBtn.addEventListener("click", async () => {
      await updateTask(item.id, {
        status: statusSelect.value,
        due_date: dueInput.value,
        tags: tagsInput.value,
        next_action: nextInput.value,
        notes: notesInput.value,
      });
      await fetchTasks();
    });

    editor.appendChild(statusSelect);
    editor.appendChild(dueInput);
    editor.appendChild(tagsInput);
    editor.appendChild(nextInput);
    editor.appendChild(notesInput);
    editor.appendChild(saveBtn);

    const toggleBtn = document.createElement("button");
    toggleBtn.className = "btn ghost";
    toggleBtn.textContent = "Edit";
    toggleBtn.addEventListener("click", () => {
      editor.classList.toggle("hidden");
    });

    card.appendChild(toggleBtn);
    card.appendChild(editor);

    cardsEl.appendChild(card);
  });

  countTotal.textContent = items.length;
  countOpen.textContent = open;
  countDone.textContent = done;
}

async function updateTask(id, payload) {
  await fetch(`/api/tasks/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

saveNew.addEventListener("click", async () => {
  const payload = {
    title: newTitle.value,
    tags: newTags.value,
    status: newStatus.value,
    due_date: newDue.value,
    priority: newPriority.value,
    next_action: newNext.value,
    notes: newNotes.value,
  };
  await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  newTitle.value = "";
  newTags.value = "";
  newDue.value = "";
  newPriority.value = "";
  newNext.value = "";
  newNotes.value = "";
  await fetchTasks();
});

toggleAddBtn.addEventListener("click", () => {
  addPanel.classList.toggle("hidden");
});

refreshBtn.addEventListener("click", fetchTasks);

fetchTasks();
fetchTags();
