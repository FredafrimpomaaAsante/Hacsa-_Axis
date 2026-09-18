var incidentTableBody = document.getElementById("incidentTableBody");
var incidentForm = document.getElementById("incidentForm");
var severityFilter = document.getElementById("severityFilter");
var statusFilter = document.getElementById("statusFilter");
var incidentData = [];

function getSeverityClass(level) {
  var value = (level || "").toLowerCase();
  if (value === "critical" || value === "high") return "danger";
  if (value === "medium") return "warning";
  return "success";
}

function prettyStatus(status) {
  return (status || "open").replaceAll("_", " ");
}

function renderIncidents() {
  var severityValue = severityFilter.value;
  var statusValue = statusFilter.value;
  var filtered = incidentData.filter(function (incident) {
    var severity = (incident.severity || "").toLowerCase();
    var status = prettyStatus(incident.status);
    var severityMatch = severityValue === "All" || severity === severityValue.toLowerCase();
    var statusMatch = statusValue === "All" || status.toLowerCase() === statusValue.toLowerCase();
    return severityMatch && statusMatch;
  });

  incidentTableBody.innerHTML = "";
  if (!filtered.length) {
    var empty = document.createElement("tr");
    empty.innerHTML = '<td colspan="7"><div class="empty-state">No incidents match these filters.</div></td>';
    incidentTableBody.appendChild(empty);
    document.getElementById("openCases").textContent = incidentData.filter(function (item) { return !["resolved", "closed"].includes((item.status || "").toLowerCase()); }).length;
    document.getElementById("resolvedCases").textContent = incidentData.filter(function (item) { return ["resolved", "closed"].includes((item.status || "").toLowerCase()); }).length;
    document.getElementById("criticalCases").textContent = incidentData.filter(function (item) { return (item.severity || "").toLowerCase() === "critical"; }).length;
    document.getElementById("avgResponse").textContent = (incidentData[0] && incidentData[0].response_time_seconds ? Math.round(incidentData[0].response_time_seconds / 60) : 0) + "m";
    return;
  }
  filtered.forEach(function (incident) {
    var row = document.createElement("tr");
    row.innerHTML = [
      "<td>INC-" + incident.id + "</td>",
      "<td>" + (incident.title || incident.description || "") + "</td>",
      "<td>" + (incident.location || "") + "</td>",
      '<td><span class="badge ' + getSeverityClass(incident.severity) + '">' + incident.severity + "</span></td>",
      '<td><span class="badge success">' + prettyStatus(incident.status) + "</span></td>",
      "<td>" + (incident.reported_by || "") + "</td>",
      "<td>" + new Date(incident.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + "</td>",
    ].join("");
    incidentTableBody.appendChild(row);
  });

  var openCases = incidentData.filter(function (item) { return !["resolved", "closed"].includes((item.status || "").toLowerCase()); }).length;
  var resolvedCases = incidentData.filter(function (item) { return ["resolved", "closed"].includes((item.status || "").toLowerCase()); }).length;
  var criticalCases = incidentData.filter(function (item) { return (item.severity || "").toLowerCase() === "critical"; }).length;
  document.getElementById("openCases").textContent = openCases;
  document.getElementById("resolvedCases").textContent = resolvedCases;
  document.getElementById("criticalCases").textContent = criticalCases;
  document.getElementById("avgResponse").textContent = (incidentData[0] && incidentData[0].response_time_seconds ? Math.round(incidentData[0].response_time_seconds / 60) : 0) + "m";
}

async function refreshIncidents() {
  var id = await eventId();
  incidentData = await api("/api/v1/incidents/?event_id=" + id);
  renderIncidents();
}

severityFilter.addEventListener("change", renderIncidents);
statusFilter.addEventListener("change", renderIncidents);

incidentForm.addEventListener("submit", async function (event) {
  event.preventDefault();
  var id = await eventId();
  await api("/api/v1/incidents/", {
    method: "POST",
    body: JSON.stringify({
      event_id: id,
      title: document.getElementById("title").value.trim(),
      location: document.getElementById("location").value.trim(),
      severity: document.getElementById("severity").value.toLowerCase(),
      description: document.getElementById("description").value.trim(),
    }),
  });
  incidentForm.reset();
  refreshIncidents();
});

refreshIncidents().catch(function () {});
