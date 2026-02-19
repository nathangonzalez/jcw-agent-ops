const statusEl = document.getElementById("statusline");
const cardsEl = document.getElementById("cards");
const qEl = document.getElementById("q");
const tagEl = document.getElementById("tag");
const statusFilterEl = document.getElementById("status");
const limitEl = document.getElementById("limit");
const refreshBtn = document.getElementById("refresh");
const toggleAddBtn = document.getElementById("toggle-add");
const syncExcelBtn = document.getElementById("sync-excel");
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

const draftModal = document.getElementById("draft-modal");
const draftClose = document.getElementById("draft-close");
const tabEmail = document.getElementById("tab-email");
const tabEvent = document.getElementById("tab-event");
const emailPanel = document.getElementById("draft-email");
const eventPanel = document.getElementById("draft-event");
const draftOutput = document.getElementById("draft-output");

const emailTo = document.getElementById("email-to");
const emailSubject = document.getElementById("email-subject");
const emailBody = document.getElementById("email-body");
const emailApprove = document.getElementById("email-approve");
const emailPreview = document.getElementById("email-preview");
const emailCommit = document.getElementById("email-commit");
const emailStatus = document.getElementById("email-status");

const eventTitle = document.getElementById("event-title");
const eventStart = document.getElementById("event-start");
const eventEnd = document.getElementById("event-end");
const eventTimezone = document.getElementById("event-timezone");
const eventCalendar = document.getElementById("event-calendar");
const eventLocation = document.getElementById("event-location");
const eventDescription = document.getElementById("event-description");
const eventAttendees = document.getElementById("event-attendees");
const eventApprove = document.getElementById("event-approve");
const eventPreview = document.getElementById("event-preview");
const eventCommit = document.getElementById("event-commit");
const eventStatus = document.getElementById("event-status");

let activeTask = null;

function setStatus(text) {
  statusEl.textContent = text;
}

function setDraftOutput(text) {
  draftOutput.textContent = text;
}

function setDraftMode(mode) {
  if (mode === "email") {
    tabEmail.classList.add("active");
    tabEvent.classList.remove("active");
    emailPanel.classList.remove("hidden");
    eventPanel.classList.add("hidden");
    emailStatus.textContent = "Drafts only. No emails sent.";
  } else {
    tabEvent.classList.add("active");
    tabEmail.classList.remove("active");
    eventPanel.classList.remove("hidden");
    emailPanel.classList.add("hidden");
    eventStatus.textContent = "Drafts only. No invites sent.";
  }
}

function openDraftModal(mode, task) {
  activeTask = task;
  draftModal.classList.remove("hidden");
  setDraftMode(mode);

  const lines = [];
  if (task.title) lines.push(task.title);
  if (task.next_action) {
    lines.push("", "Next Action:", task.next_action);
  }
  if (task.notes) {
    lines.push("", "Notes:", task.notes);
  }
  if (task.due_date) {
    lines.push("", `Due: ${task.due_date}`);
  }
  const baseBody = lines.join("\n").trim();

  emailSubject.value = task.title || "";
  emailBody.value = baseBody;

  eventTitle.value = task.title || "";
  eventDescription.value = baseBody;
  if (task.due_date) {
    eventStart.value = `${task.due_date}T09:00`;
    eventEnd.value = `${task.due_date}T09:30`;
  }
  setDraftOutput("Awaiting action.");
}

function closeDraftModal() {
  draftModal.classList.add("hidden");
  activeTask = null;
}

function normalizeDateTime(value) {
  if (!value) return "";
  return value.length === 16 ? `${value}:00` : value;
}

async function postJson(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function requireApproval(inputEl) {
  if (inputEl.value.trim() !== "APPROVE") {
    setDraftOutput("Type APPROVE to commit.");
    return false;
  }
  return true;
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
    toggleBtn.className = "btn ghost small";
    toggleBtn.textContent = "Edit";
    toggleBtn.addEventListener("click", () => {
      editor.classList.toggle("hidden");
    });

    const actions = document.createElement("div");
    actions.className = "card-actions";

    const emailBtn = document.createElement("button");
    emailBtn.className = "btn ghost small";
    emailBtn.textContent = "Draft Email";
    emailBtn.addEventListener("click", () => openDraftModal("email", item));

    const eventBtn = document.createElement("button");
    eventBtn.className = "btn ghost small";
    eventBtn.textContent = "Draft Event";
    eventBtn.addEventListener("click", () => openDraftModal("event", item));

    actions.appendChild(toggleBtn);
    actions.appendChild(emailBtn);
    actions.appendChild(eventBtn);

    card.appendChild(actions);
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

syncExcelBtn.addEventListener("click", async () => {
  const approve = window.prompt("Type APPROVE to sync changes back to Excel:");
  if (!approve) return;
  try {
    setStatus("Syncing to Excel...");
    const data = await postJson("/api/writeback", { approve });
    setStatus(data.stdout || "Sync complete.");
  } catch (err) {
    setStatus(`Sync failed: ${err.message}`);
  }
});

tabEmail.addEventListener("click", () => setDraftMode("email"));
tabEvent.addEventListener("click", () => setDraftMode("event"));
draftClose.addEventListener("click", closeDraftModal);
draftModal.addEventListener("click", (event) => {
  if (event.target === draftModal) {
    closeDraftModal();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !draftModal.classList.contains("hidden")) {
    closeDraftModal();
  }
});

emailPreview.addEventListener("click", async () => {
  try {
    setDraftOutput("Generating preview...");
    const data = await postJson("/api/drafts/email", {
      to: emailTo.value,
      subject: emailSubject.value,
      body: emailBody.value,
      commit: false,
    });
    setDraftOutput(JSON.stringify(data, null, 2));
  } catch (err) {
    setDraftOutput(`Preview failed: ${err.message}`);
  }
});

emailCommit.addEventListener("click", async () => {
  if (!requireApproval(emailApprove)) return;
  try {
    setDraftOutput("Creating Gmail draft...");
    const data = await postJson("/api/drafts/email", {
      to: emailTo.value,
      subject: emailSubject.value,
      body: emailBody.value,
      commit: true,
      approve: emailApprove.value.trim(),
    });
    setDraftOutput(JSON.stringify(data, null, 2));
  } catch (err) {
    setDraftOutput(`Draft failed: ${err.message}`);
  }
});

eventPreview.addEventListener("click", async () => {
  try {
    setDraftOutput("Generating preview...");
    const data = await postJson("/api/drafts/event", {
      title: eventTitle.value,
      start: normalizeDateTime(eventStart.value),
      end: normalizeDateTime(eventEnd.value),
      timezone: eventTimezone.value,
      description: eventDescription.value,
      location: eventLocation.value,
      attendees: eventAttendees.value,
      calendar_name: eventCalendar.value,
      commit: false,
    });
    setDraftOutput(JSON.stringify(data, null, 2));
  } catch (err) {
    setDraftOutput(`Preview failed: ${err.message}`);
  }
});

eventCommit.addEventListener("click", async () => {
  if (!requireApproval(eventApprove)) return;
  try {
    setDraftOutput("Creating calendar draft...");
    const data = await postJson("/api/drafts/event", {
      title: eventTitle.value,
      start: normalizeDateTime(eventStart.value),
      end: normalizeDateTime(eventEnd.value),
      timezone: eventTimezone.value,
      description: eventDescription.value,
      location: eventLocation.value,
      attendees: eventAttendees.value,
      calendar_name: eventCalendar.value,
      commit: true,
      approve: eventApprove.value.trim(),
    });
    setDraftOutput(JSON.stringify(data, null, 2));
  } catch (err) {
    setDraftOutput(`Draft failed: ${err.message}`);
  }
});

fetchTasks();
fetchTags();
