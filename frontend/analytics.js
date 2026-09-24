var data = [48, 62, 75, 80, 66, 88];
var labels = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00'];

function renderChart() {
  var barChart = document.getElementById('barChart');
  barChart.innerHTML = '';

  data.forEach(function (value, index) {
    var col = document.createElement('div');
    col.className = 'bar-col';

    var bar = document.createElement('div');
    bar.className = 'bar';
    bar.style.height = value + '%';

    var label = document.createElement('div');
    label.className = 'bar-label';
    label.textContent = labels[index];

    col.appendChild(bar);
    col.appendChild(label);
    barChart.appendChild(col);
  });
}

function renderMetrics() {
  document.getElementById('analyticsCheckins').textContent = '2,480';
  document.getElementById('analyticsWait').textContent = '7m';
  document.getElementById('analyticsThroughput').textContent = '82%';
  document.getElementById('analyticsStaff').textContent = '76%';
  document.getElementById('avgResponseTime').textContent = '11m';
  document.getElementById('incidentsToday').textContent = '38';
  document.getElementById('incidentsResolved').textContent = '29';
  document.getElementById('slaBreaches').textContent = '3';
}

function exportReport() {
  var rows = [
    ['Metric', 'Value'],
    ['Check-ins', document.getElementById('analyticsCheckins').textContent],
    ['Avg. Wait', document.getElementById('analyticsWait').textContent],
    ['Throughput', document.getElementById('analyticsThroughput').textContent],
    ['Staff Utilization', document.getElementById('analyticsStaff').textContent],
    ['Avg. Response Time', document.getElementById('avgResponseTime').textContent],
    ['Incidents Today', document.getElementById('incidentsToday').textContent],
    ['Resolved', document.getElementById('incidentsResolved').textContent],
    ['SLA Breaches', document.getElementById('slaBreaches').textContent]
  ];

  var csv = rows.map(function (row) {
    return row.join(',');
  }).join('\n');

  var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  var link = document.createElement('a');
  var url = URL.createObjectURL(blob);
  link.href = url;
  link.download = 'operations-report.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

var exportBtn = document.getElementById('exportBtn');
if (exportBtn) {
  exportBtn.addEventListener('click', exportReport);
}

renderChart();
renderMetrics();
