var incidentTableBody = document.getElementById("incidentTableBody");
var incidentForm = document.getElementById("incidentForm");
var severityFilter = document.getElementById("severityFilter");
var statusFilter = document.getElementById("statusFilter");
var incidentData = [];
var opsPeople = [];

function getSeverityClass(level) {
  var value = (level || "").toLowerCase();
  if (value === "critical" || value === "high") return "danger";
  if (value === "medium") return "warning";
  return "success";
}

function prettyStatus(status) {
  return (status || "open").replaceAll("_", " ");
}

function incidentTitle(incident) {
  var text = incident.description || "";
  var parts = text.split(": ");
  return parts.length > 1 ? parts[0] : text;
}

function assignedName(incident) {
  var assignment = (incident.assignments || [])[0];
  if (!assignment) return "Unassigned";
  var person = findPerson(opsPeople, assignment.responder_id);
  return person ? personName(person) : assignment.responder_id;
}

function statusActions(incident) {
  var status = (incident.status || "").toLowerCase();
  if (status === "open") {
    return '<button type="button" class="ghost-btn" data-status="assigned" data-id="' + incident.id + '">Assign</button>' +
      '<button type="button" class="ghost-btn" data-status="in_progress" data-id="' + incident.id + '">Start</button>';
  }
  if (status === "assigned") {
    return '<button type="button" class="ghost-btn" data-status="in_progress" data-id="' + incident.id + '">Start</button>';
  }
  if (status === "in_progress") {
    return '<button type="button" class="ghost-btn" data-status="resolved" data-id="' + incident.id + '">Resolve</button>';
  }
  return "—";
}

function fillAssignees() {
  var select = document.getElementById("assignedTo");
  var current = select.value;
  var staff = staffPeople(opsPeople);
  select.innerHTML = '<option value="">Unassigned</option>';
  staff.forEach(function (person) {
    var option = document.createElement("option");
    option.value = String(person.id);
    option.textContent = person.full_name + " · " + person.role.replaceAll("_", " ");
    select.appendChild(option);
  });
  if (current) select.value = current;
}

function renderIncidents() {
  var severityValue = severityFilter.value;
  var statusValue = statusFilter.value;
  var filtered = incidentData.filter(function (incident) {
    var severity = (incident.severity || "").toLowerCase();
    var status = (incident.status || "").toLowerCase();
    var severityMatch = severityValue === "All" || severity === severityValue.toLowerCase();
    var statusMatch = statusValue === "All" || status === statusValue.toLowerCase();
    return severityMatch && statusMatch;
  });

  incidentTableBody.innerHTML = "";
  if (!filtered.length) {
    var empty = document.createElement("tr");
    empty.innerHTML = '<td colspan="8"><div class="empty-state">No incidents match these filters.</div></td>';
    incidentTableBody.appendChild(empty);
  } else {
    filtered.forEach(function (incident) {
      var row = document.createElement("tr");
      row.innerHTML = [
        "<td>INC-" + incident.id + "</td>",
        "<td>" + incidentTitle(incident) + "</td>",
        "<td>" + (incident.location || "") + "</td>",
        '<td><span class="badge ' + getSeverityClass(incident.severity) + '">' + incident.severity + "</span></td>",
        '<td><span class="badge ' + (incident.status === "resolved" || incident.status === "closed" ? "success" : "warning") + '">' + prettyStatus(incident.status) + "</span></td>",
        "<td>" + assignedName(incident) + "</td>",
        "<td>" + new Date(incident.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + "</td>",
        '<td class="table-actions">' + statusActions(incident) + "</td>",
      ].join("");
      incidentTableBody.appendChild(row);
    });
  }

  var openCases = incidentData.filter(function (item) { return !["resolved", "closed"].includes((item.status || "").toLowerCase()); }).length;
  var resolvedCases = incidentData.filter(function (item) { return ["resolved", "closed"].includes((item.status || "").toLowerCase()); }).length;
  var criticalCases = incidentData.filter(function (item) { return (item.severity || "").toLowerCase() === "critical"; }).length;
  var timed = incidentData.filter(function (item) { return item.response_time_seconds; });
  var avg = timed.length ? Math.round(timed.reduce(function (sum, item) { return sum + item.response_time_seconds; }, 0) / timed.length / 60) : 0;
  document.getElementById("openCases").textContent = openCases;
  document.getElementById("resolvedCases").textContent = resolvedCases;
  document.getElementById("criticalCases").textContent = criticalCases;
  document.getElementById("avgResponse").textContent = avg + "m";
}

async function renderSafetyIndicators() {
  var id = await eventId();
  var zones = await api("/api/v1/occupancy/zones?event_id=" + id);
  var alerts = await api("/api/v1/alerts/?event_id=" + id);
  var host = document.getElementById("safetyIndicators");
  host.innerHTML = "";
  zones.forEach(function (zone) {
    var percent = zone.capacity ? Math.round((zone.current_count / zone.capacity) * 100) : 0;
    var item = document.createElement("li");
    item.className = "alert-item " + (percent > 85 ? "critical" : percent > 60 ? "warning" : "info");
    item.textContent = zone.zone_name + " is " + occupancyLabel(percent).toLowerCase() + " at " + percent + "% (" + zone.current_count + "/" + zone.capacity + ")";
    host.appendChild(item);
  });
  alerts.filter(function (alert) { return !alert.resolved; }).slice(0, 4).forEach(function (alert) {
    var item = document.createElement("li");
    item.className = "alert-item " + alertLevel(alert.level);
    item.textContent = alert.message;
    host.appendChild(item);
  });
}

async function refreshIncidents() {
  var id = await eventId();
  opsPeople = await api("/participants");
  incidentData = await api("/api/v1/incidents/?event_id=" + id);
  fillAssignees();
  renderIncidents();
  await renderSafetyIndicators();
  showOpsNotice("Live · last updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
}

severityFilter.addEventListener("change", renderIncidents);
statusFilter.addEventListener("change", renderIncidents);

incidentForm.addEventListener("submit", async function (event) {
  event.preventDefault();
  try {
    var id = await eventId();
    var created = await api("/api/v1/incidents/", {
      method: "POST",
      body: JSON.stringify({
        event_id: id,
        title: document.getElementById("title").value.trim(),
        location: document.getElementById("location").value.trim(),
        severity: document.getElementById("severity").value.toLowerCase(),
        description: document.getElementById("description").value.trim(),
      }),
    });
    var assignee = document.getElementById("assignedTo").value;
    if (assignee) {
      await api("/api/v1/incidents/" + created.id + "/assign", {
        method: "POST",
        body: JSON.stringify({ responder_id: assignee, notes: document.getElementById("type").value + " desk assignment" }),
      });
    }
    incidentForm.reset();
    showOpsNotice("Incident logged.");
    refreshIncidents();
  } catch (error) {
    showOpsNotice(error.message || "Could not submit incident.", true);
  }
});

incidentTableBody.addEventListener("click", async function (event) {
  var button = event.target.closest("[data-status]");
  if (!button) return;
  var incidentId = button.getAttribute("data-id");
  var status = button.getAttribute("data-status");
  try {
    if (status === "assigned") {
      var assignee = document.getElementById("assignedTo").value || (staffPeople(opsPeople)[0] && String(staffPeople(opsPeople)[0].id));
      if (!assignee) throw new Error("Choose a responder first.");
      await api("/api/v1/incidents/" + incidentId + "/assign", {
        method: "POST",
        body: JSON.stringify({ responder_id: assignee }),
      });
    } else {
      await api("/api/v1/incidents/" + incidentId + "/status", {
        method: "PATCH",
        body: JSON.stringify({ status: status }),
      });
    }
    refreshIncidents();
  } catch (error) {
    showOpsNotice(error.message || "Could not update incident.", true);
  }
});

watchOperations(function () {
  refreshIncidents().catch(function (error) {
    showOpsNotice(error.message || "Could not load incidents.", true);
  });
});
