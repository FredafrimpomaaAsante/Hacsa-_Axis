var teamMap = {
  Medical: 'Medical Response',
  Security: 'Security',
  Facility: 'Facilities',
  Safety: 'Crowd Control'
};

var incidentData = [
  { id: 'INC-2051', title: 'Crowd congestion at Gate 3', location: 'Main Entrance', severity: 'Medium', status: 'Monitoring', assignedTeam: 'Security', time: '09:10', sla: '45m', slaMinutes: 45, type: 'Safety' },
  { id: 'INC-2052', title: 'Guest reported dizziness', location: 'Workshop A', severity: 'High', status: 'In Progress', assignedTeam: 'Medical Response', time: '08:42', sla: '30m', slaMinutes: 30, type: 'Medical' },
  { id: 'INC-2053', title: 'Power fluctuation in stage lighting', location: 'Main Hall', severity: 'Critical', status: 'Open', assignedTeam: 'Facilities', time: '07:56', sla: '20m', slaMinutes: 20, type: 'Facility' },
  { id: 'INC-2054', title: 'Lost item reported', location: 'Lobby', severity: 'Low', status: 'Resolved', assignedTeam: 'Guest Services', time: '06:25', sla: '90m', slaMinutes: 90, type: 'Safety' }
];

var severityFilter = document.getElementById('severityFilter');
var statusFilter = document.getElementById('statusFilter');
var incidentTableBody = document.getElementById('incidentTableBody');
var incidentForm = document.getElementById('incidentForm');

function getSeverityClass(level) {
  if (level === 'Critical') return 'danger';
  if (level === 'High') return 'danger';
  if (level === 'Medium') return 'warning';
  return 'success';
}

function getTeamForType(type) {
  return teamMap[type] || null;
}

function parseIncidentSlaMinutes(incident) {
  if (typeof incident.slaMinutes === 'number') {
    return incident.slaMinutes;
  }

  if (incident.sla) {
    var match = String(incident.sla).match(/(\d+)/);
    if (match) {
      return parseInt(match[1], 10);
    }
  }

  return 0;
}

function getIncidentTimeMinutes(incident) {
  if (!incident || !incident.time) {
    return 0;
  }

  var timeParts = String(incident.time).split(':');
  if (timeParts.length < 2) {
    return 0;
  }

  var hours = parseInt(timeParts[0], 10);
  var minutes = parseInt(timeParts[1], 10);

  if (Number.isNaN(hours) || Number.isNaN(minutes)) {
    return 0;
  }

  return (hours * 60) + minutes;
}

function getSlaBreachMinutes(incident) {
  if (!incident || incident.status === 'Resolved') {
    return 0;
  }

  var now = new Date();
  var currentMinutes = (now.getHours() * 60) + now.getMinutes();
  var incidentMinutes = getIncidentTimeMinutes(incident);
  var slaMinutes = parseIncidentSlaMinutes(incident);

  if (incidentMinutes === 0 || slaMinutes === 0) {
    return 0;
  }

  var elapsedMinutes = currentMinutes - incidentMinutes;
  if (elapsedMinutes < 0) {
    elapsedMinutes = 0;
  }

  return Math.max(0, elapsedMinutes - slaMinutes);
}

function getEscalationLevel(incident) {
  if (!incident || incident.status === 'Resolved') {
    return null;
  }

  var overdueMinutes = getSlaBreachMinutes(incident);

  if (overdueMinutes <= 2) {
    return 'team';
  }

  if (overdueMinutes > 2 && overdueMinutes <= 5) {
    return 'operations lead';
  }

  return 'event manager';
}

function getSlaBadge(incident) {
  if (!incident || incident.status === 'Resolved') {
    return '';
  }

  var overdueMinutes = getSlaBreachMinutes(incident);
  if (overdueMinutes <= 0) {
    return '';
  }

  var escalationLevel = getEscalationLevel(incident);
  return '<span class="badge danger">SLA BREACHED</span> <span class="badge warning">' + escalationLevel + '</span>';
}

function renderIncidents() {
  var severityValue = severityFilter.value;
  var statusValue = statusFilter.value;

  var filtered = incidentData.filter(function (incident) {
    var severityMatch = severityValue === 'All' || incident.severity === severityValue;
    var statusMatch = statusValue === 'All' || incident.status === statusValue;
    return severityMatch && statusMatch;
  });

  incidentTableBody.innerHTML = '';

  filtered.forEach(function (incident) {
    var row = document.createElement('tr');
    var slaBadge = getSlaBadge(incident);

    row.innerHTML = [
      '<td>' + incident.id + '</td>',
      '<td>' + incident.title + '</td>',
      '<td>' + incident.location + '</td>',
      '<td><span class="badge ' + getSeverityClass(incident.severity) + '">' + incident.severity + '</span></td>',
      '<td><span class="badge success">' + incident.status + '</span></td>',
      '<td>' + (incident.assignedTeam || 'Unassigned') + '</td>',
      '<td>' + incident.time + ' / ' + (incident.sla || 'N/A') + '</td>',
      '<td>' + (slaBadge || '<span class="badge success">On Track</span>') + '</td>'
    ].join('');
    incidentTableBody.appendChild(row);
  });

  var openCases = incidentData.filter(function (item) { return item.status !== 'Resolved'; }).length;
  var resolvedCases = incidentData.filter(function (item) { return item.status === 'Resolved'; }).length;
  var criticalCases = incidentData.filter(function (item) { return item.severity === 'Critical'; }).length;
  var avgResponse = Math.max(4, Math.round((openCases + resolvedCases) / 3));

  document.getElementById('openCases').textContent = openCases;
  document.getElementById('resolvedCases').textContent = resolvedCases;
  document.getElementById('criticalCases').textContent = criticalCases;
  document.getElementById('avgResponse').textContent = avgResponse + 'm';
}

severityFilter.addEventListener('change', renderIncidents);
statusFilter.addEventListener('change', renderIncidents);

incidentForm.addEventListener('submit', function (event) {
  event.preventDefault();

  var title = document.getElementById('title').value.trim();
  var location = document.getElementById('location').value.trim();
  var severity = document.getElementById('severity').value;
  var type = document.getElementById('type').value;
  var description = document.getElementById('description').value.trim();

  if (!title || !location || !description) {
    return;
  }

  var assignedTeam = getTeamForType(type);
  var newIncident = {
    id: 'INC-' + Math.floor(Math.random() * 9000 + 1000),
    title: title,
    location: location,
    severity: severity,
    status: assignedTeam ? 'assigned' : 'reported',
    assignedTeam: assignedTeam || null,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    sla: '30m',
    slaMinutes: 30,
    type: type,
    description: description
  };

  incidentData.unshift(newIncident);
  incidentForm.reset();
  renderIncidents();
});

renderIncidents();
