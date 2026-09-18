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

  document.getElementById('analyticsCheckins').textContent = '2,480';
  document.getElementById('analyticsWait').textContent = '7m';
  document.getElementById('analyticsThroughput').textContent = '82%';
  document.getElementById('analyticsStaff').textContent = '76%';
}

renderChart();
