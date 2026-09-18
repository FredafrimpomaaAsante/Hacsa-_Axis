var state = {
  totalRegistered: 500,
  checkedIn: 320,
  staffCount: 18,
  venues: [
    { name: 'Main Hall', count: 210, capacity: 300 },
    { name: 'Workshop A', count: 110, capacity: 180 },
    { name: 'Workshop B', count: 120, capacity: 200 },
    { name: 'Lobby', count: 75, capacity: 150 }
  ],
  checkins: [
    { name: 'Kwame', gate: 'Gate 1', time: '14:20', status: 'IN' },
    { name: 'Aisha', gate: 'Gate 2', time: '14:18', status: 'IN' },
    { name: 'Tariq', gate: 'Gate 3', time: '14:15', status: 'IN' },
    { name: 'Mina', gate: 'Gate 1', time: '14:12', status: 'IN' }
  ],
  alerts: [
    { text: 'Queue at Gate 3 is increasing.', level: 'warning' },
    { text: 'Medical station is fully staffed.', level: 'info' },
    { text: 'Fire exits are clear and verified.', level: 'info' }
  ]
};

function renderDashboard() {
  var totalRegistered = document.getElementById('totalRegistered');
  var checkedInCount = document.getElementById('checkedInCount');
  var occupancyValue = document.getElementById('occupancyValue');
  var staffCount = document.getElementById('staffCount');
  var venueGrid = document.getElementById('venueGrid');
  var checkinBody = document.getElementById('checkinBody');
  var alertsList = document.getElementById('alertsList');

  var occupancy = Math.round((state.checkedIn / state.totalRegistered) * 100);

  totalRegistered.textContent = state.totalRegistered;
  checkedInCount.textContent = state.checkedIn;
  occupancyValue.textContent = occupancy + '%';
  staffCount.textContent = state.staffCount;

  venueGrid.innerHTML = '';
  state.venues.forEach(function (venue) {
    var percent = Math.round((venue.count / venue.capacity) * 100);
    var tone = 'green';

    if (percent > 85) {
      tone = 'red';
    } else if (percent > 60) {
      tone = 'yellow';
    }

    var node = document.createElement('div');
    node.className = 'venue-card';
    node.innerHTML = [
      '<div class="venue-row">',
      '<span>' + venue.name + '</span>',
      '<strong>' + venue.count + '/' + venue.capacity + '</strong>',
      '</div>',
      '<div class="venue-progress"><div class="venue-progress-bar ' + tone + '" style="width: ' + percent + '%"></div></div>'
    ].join('');
    venueGrid.appendChild(node);
  });

  checkinBody.innerHTML = '';
  state.checkins.forEach(function (checkin) {
    var row = document.createElement('tr');
    row.innerHTML = [
      '<td>' + checkin.name + '</td>',
      '<td>' + checkin.gate + '</td>',
      '<td>' + checkin.time + '</td>',
      '<td><span class="badge success">' + checkin.status + '</span></td>'
    ].join('');
    checkinBody.appendChild(row);
  });

  alertsList.innerHTML = '';
  state.alerts.forEach(function (alert) {
    var item = document.createElement('li');
    item.className = 'alert-item ' + alert.level;
    item.textContent = alert.text;
    alertsList.appendChild(item);
  });
}

setInterval(function () {
  var names = ['Kwame', 'Aisha', 'Tariq', 'Mina', 'Sam', 'Lina', 'Omar'];
  var gates = ['Gate 1', 'Gate 2', 'Gate 3', 'VIP'];
  var now = new Date();

  state.checkedIn += 1;
  if (state.checkedIn > state.totalRegistered) {
    state.checkedIn = state.totalRegistered;
  }

  state.checkins.unshift({
    name: names[Math.floor(Math.random() * names.length)],
    gate: gates[Math.floor(Math.random() * gates.length)],
    time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    status: 'IN'
  });

  if (state.checkins.length > 5) {
    state.checkins.pop();
  }

  state.venues.forEach(function (venue) {
    var jump = Math.floor(Math.random() * 8) + 1;
    venue.count += jump;
    if (venue.count > venue.capacity) {
      venue.count = venue.capacity;
    }
  });

  state.alerts = [
    { text: 'Queue at Gate 3 is increasing.', level: 'warning' },
    { text: 'Medical station is fully staffed.', level: 'info' },
    { text: 'Venue occupancy remains stable.', level: 'info' }
  ];

  renderDashboard();
}, 3000);

renderDashboard();
