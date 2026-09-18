function occupancyFromVenues(venues) {
  var capacity = venues.reduce(function (sum, venue) { return sum + (venue.capacity || 0); }, 0);
  var count = venues.reduce(function (sum, venue) { return sum + (venue.count || 0); }, 0);
  return capacity ? Math.round((count / capacity) * 100) : 0;
}

function occupancyTone(percent) {
  if (percent > 85) return "red";
  if (percent > 60) return "yellow";
  return "green";
}

function occupancyLabel(percent) {
  if (percent > 85) return "Near capacity";
  if (percent > 60) return "Busy";
  return "Comfortable";
}

function guestLabel(row, people) {
  var match = people.find(function (person) {
    return String(person.id) === String(row.participant_id) || person.email === row.participant_id;
  });
  if (match) return match.full_name || match.name || match.email;
  var raw = String(row.participant_id || "Guest");
  if (raw.length > 18) return "Guest " + raw.slice(-4);
  return raw;
}

function gateLabel(method) {
  if (!method) return "Main gate";
  return method.replaceAll("_", " ");
}

function renderVenues(host, venues) {
  host.innerHTML = "";
  if (!venues.length) {
    host.innerHTML = '<p class="empty-state">No venues reporting occupancy yet.</p>';
    return;
  }
  venues.forEach(function (venue) {
    var percent = venue.capacity ? Math.round((venue.count / venue.capacity) * 100) : 0;
    var node = document.createElement("article");
    node.className = "venue-card";
    node.innerHTML =
      '<div class="venue-row"><span>' + venue.name + "</span><strong>" + venue.count + " / " + venue.capacity + "</strong></div>" +
      '<div class="venue-status"><span>' + occupancyLabel(percent) + "</span><span>" + percent + "%</span></div>" +
      '<div class="venue-progress"><div class="venue-progress-bar ' + occupancyTone(percent) + '" style="width: ' + percent + '%"></div></div>';
    host.appendChild(node);
  });
}

function renderAlerts(host, alerts) {
  host.innerHTML = "";
  alerts.forEach(function (alert) {
    var item = document.createElement("li");
    item.className = "alert-item " + alert.level;
    item.textContent = alert.text;
    host.appendChild(item);
  });
}

async function loadOpsState() {
  var id = await eventId();
  var overview = await api("/api/v1/analytics/overview?event_id=" + id);
  var zones = await api("/api/v1/occupancy/zones?event_id=" + id);
  var checkins = await api("/api/v1/attendance/check-ins?event_id=" + id).catch(function () { return []; });
  var alerts = await api("/api/v1/alerts/?event_id=" + id).catch(function () { return []; });
  var people = await api("/participants").catch(function () { return []; });
  var incidents = await api("/api/v1/incidents/?event_id=" + id).catch(function () { return []; });
  return {
    totalRegistered: people.length || overview.total_checked_in,
    checkedIn: overview.total_checked_in,
    staffCount: people.filter(function (person) {
      return ["organiser", "ops_lead", "staff", "safety_officer"].includes(person.role);
    }).length || 18,
    openIncidents: incidents.filter(function (item) {
      return !["resolved", "closed"].includes((item.status || "").toLowerCase());
    }).length,
    venues: zones.map(function (zone) {
      return { name: zone.zone_name, count: zone.current_count, capacity: zone.capacity };
    }),
    checkins: checkins.slice(0, 8).map(function (row) {
      return {
        name: guestLabel(row, people),
        gate: gateLabel(row.method),
        time: new Date(row.checked_in_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        status: "In",
      };
    }),
    alerts: (alerts.length ? alerts : [{ message: "All systems operational. No active alerts.", level: "info" }]).slice(0, 6).map(function (alert) {
      return {
        text: alert.message || alert.text,
        level: alert.level === "critical" ? "critical" : alert.level === "elevated" || alert.level === "warning" ? "warning" : "info",
      };
    }),
  };
}

function renderDashboard(state) {
  var occupancy = occupancyFromVenues(state.venues);
  document.getElementById("totalRegistered").textContent = state.totalRegistered;
  document.getElementById("checkedInCount").textContent = state.checkedIn;
  document.getElementById("occupancyValue").textContent = occupancy + "%";
  document.getElementById("staffCount").textContent = state.staffCount;
  renderVenues(document.getElementById("venueGrid"), state.venues);

  var checkinBody = document.getElementById("checkinBody");
  checkinBody.innerHTML = "";
  if (!state.checkins.length) {
    var empty = document.createElement("tr");
    empty.innerHTML = '<td colspan="4"><div class="empty-state">No check-ins yet. Arrivals will appear here as guests scan in.</div></td>';
    checkinBody.appendChild(empty);
  } else {
    state.checkins.forEach(function (checkin) {
      var row = document.createElement("tr");
      row.innerHTML = "<td>" + checkin.name + "</td><td>" + checkin.gate + "</td><td>" + checkin.time + '</td><td><span class="badge success">' + checkin.status + "</span></td>";
      checkinBody.appendChild(row);
    });
  }

  renderAlerts(document.getElementById("alertsList"), state.alerts);
}

loadOpsState().then(renderDashboard).catch(function (error) {
  console.error(error);
});
