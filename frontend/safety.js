var incidentData = [
  { id: 'INC-2051', title: 'Crowd congestion at Gate 3', location: 'Main Entrance', severity: 'Medium', status: 'Monitoring', assignedTo: 'A. Chen', time: '09:10' },
  { id: 'INC-2052', title: 'Guest reported dizziness', location: 'Workshop A', severity: 'High', status: 'In Progress', assignedTo: 'D. Brooks', time: '08:42' },
  { id: 'INC-2053', title: 'Power fluctuation in stage lighting', location: 'Main Hall', severity: 'Critical', status: 'Open', assignedTo: 'M. Patel', time: '07:56' },
  { id: 'INC-2054', title: 'Lost item reported', location: 'Lobby', severity: 'Low', status: 'Resolved', assignedTo: 'N. Singh', time: '06:25' }
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
    row.innerHTML = [
      '<td>' + incident.id + '</td>',
      '<td>' + incident.title + '</td>',
      '<td>' + incident.location + '</td>',
      '<td><span class="badge ' + getSeverityClass(incident.severity) + '">' + incident.severity + '</span></td>',
      '<td><span class="badge success">' + incident.status + '</span></td>',
      '<td>' + incident.assignedTo + '</td>',
      '<td>' + incident.time + '</td>'
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
  var assignedTo = document.getElementById('assignedTo').value;

  if (!title || !location || !description) {
    return;
  }

  incidentData.unshift({
    id: 'INC-' + Math.floor(Math.random() * 9000 + 1000),
    title: title,
    location: location,
    severity: severity,
    status: 'Open',
    assignedTo: assignedTo,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    type: type,
    description: description
  });

  incidentForm.reset();
  renderIncidents();
});

renderIncidents();
