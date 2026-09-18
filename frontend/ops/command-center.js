var opsPeople = [];

async function loadOpsState() {
  var id = await eventId();
  var overview = await api("/api/v1/analytics/overview?event_id=" + id);
  var zones = await api("/api/v1/occupancy/zones?event_id=" + id);
  var checkins = await api("/api/v1/attendance/check-ins?event_id=" + id);
  var alerts = await api("/api/v1/alerts/?event_id=" + id);
  var people = await api("/participants");
  opsPeople = people;
  return {
    eventId: id,
    totalRegistered: people.filter(function (person) {
      return ["participant", "speaker"].includes(person.role);
    }).length,
    checkedIn: overview.total_checked_in,
    staffCount: staffPeople(people).length,
    people: people,
    checkinRows: checkins,
    venues: zones.map(function (zone) {
      return { name: zone.zone_name, count: zone.current_count, capacity: zone.capacity };
    }),
    checkins: checkins.slice(0, 10).map(function (row) {
      return {
        name: guestLabel(row, people),
        gate: gateLabel(row.method),
        time: new Date(row.checked_in_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        status: "In",
      };
    }),
    alerts: alerts.filter(function (alert) { return !alert.resolved; }).slice(0, 8),
  };
}

function fillGuestSelect(state) {
  var select = document.getElementById("checkinGuest");
  if (!select) return;
  var checked = {};
  state.checkinRows.forEach(function (row) { checked[String(row.participant_id)] = true; });
  var waiting = state.people.filter(function (person) {
    return ["participant", "speaker"].includes(person.role) && !checked[String(person.person_id)] && !checked[String(person.id)];
  });
  var current = select.value;
  select.innerHTML = '<option value="">Select a guest</option>';
  waiting.forEach(function (person) {
    var option = document.createElement("option");
    option.value = person.person_id;
    option.textContent = person.full_name + " · " + person.email;
    select.appendChild(option);
  });
  if (current) select.value = current;
}

function renderDashboard(state) {
  document.getElementById("totalRegistered").textContent = state.totalRegistered;
  document.getElementById("checkedInCount").textContent = state.checkedIn;
  document.getElementById("occupancyValue").textContent = occupancyFromVenues(state.venues) + "%";
  document.getElementById("staffCount").textContent = state.staffCount;
  renderVenueCards(document.getElementById("venueGrid"), state.venues, { adjustable: true });
  fillGuestSelect(state);

  var checkinBody = document.getElementById("checkinBody");
  checkinBody.innerHTML = "";
  if (!state.checkins.length) {
    var empty = document.createElement("tr");
    empty.innerHTML = '<td colspan="4"><div class="empty-state">No check-ins yet. Use the form to scan a guest in.</div></td>';
    checkinBody.appendChild(empty);
  } else {
    state.checkins.forEach(function (checkin) {
      var row = document.createElement("tr");
      row.innerHTML = "<td>" + checkin.name + "</td><td>" + checkin.gate + "</td><td>" + checkin.time + '</td><td><span class="badge success">' + checkin.status + "</span></td>";
      checkinBody.appendChild(row);
    });
  }

  var alertsList = document.getElementById("alertsList");
  alertsList.innerHTML = "";
  if (!state.alerts.length) {
    alertsList.innerHTML = '<li class="alert-item info">All systems operational. No active alerts.</li>';
    return;
  }
  state.alerts.forEach(function (alert) {
    var item = document.createElement("li");
    item.className = "alert-item " + alertLevel(alert.level);
    item.innerHTML =
      "<div><strong>" + (alert.zone_name || "Venue") + "</strong> · " + alert.message + "</div>" +
      '<div class="inline-actions">' +
      (alert.acknowledged_at ? "" : '<button type="button" class="ghost-btn" data-alert-ack="' + alert.id + '">Acknowledge</button>') +
      '<button type="button" class="ghost-btn" data-alert-resolve="' + alert.id + '">Resolve</button>' +
      "</div>";
    alertsList.appendChild(item);
  });
}

async function refreshOps() {
  try {
    var state = await loadOpsState();
    renderDashboard(state);
    showOpsNotice("Live · last updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
  } catch (error) {
    showOpsNotice(error.message || "Could not load live operations data.", true);
  }
}

document.getElementById("checkinForm").addEventListener("submit", async function (event) {
  event.preventDefault();
  var guestId = document.getElementById("checkinGuest").value;
  if (!guestId) return;
  try {
    var id = await eventId();
    var guest = findPerson(opsPeople, guestId);
    await api("/api/v1/attendance/check-in", {
      method: "POST",
      body: JSON.stringify({
        event_id: id,
        participant_id: guestId,
        pass_code: guest ? "PASS-" + String(guest.id).padStart(4, "0") : "PASS-MANUAL",
        method: document.getElementById("checkinMethod").value,
      }),
    });
    document.getElementById("checkinForm").reset();
    showOpsNotice("Guest checked in.");
    refreshOps();
  } catch (error) {
    showOpsNotice(error.message || "Check-in failed.", true);
  }
});

document.getElementById("venueGrid").addEventListener("click", async function (event) {
  var button = event.target.closest("[data-zone]");
  if (!button) return;
  try {
    var id = await eventId();
    await api("/api/v1/occupancy/delta", {
      method: "POST",
      body: JSON.stringify({
        event_id: id,
        zone_name: button.getAttribute("data-zone"),
        delta: Number(button.getAttribute("data-delta")),
      }),
    });
    refreshOps();
  } catch (error) {
    showOpsNotice(error.message || "Could not update occupancy.", true);
  }
});

document.getElementById("alertsList").addEventListener("click", async function (event) {
  var ack = event.target.closest("[data-alert-ack]");
  var resolve = event.target.closest("[data-alert-resolve]");
  try {
    if (ack) await api("/api/v1/alerts/" + ack.getAttribute("data-alert-ack") + "/acknowledge", { method: "PATCH" });
    if (resolve) await api("/api/v1/alerts/" + resolve.getAttribute("data-alert-resolve") + "/resolve", { method: "PATCH" });
    if (ack || resolve) refreshOps();
  } catch (error) {
    showOpsNotice(error.message || "Could not update alert.", true);
  }
});

watchOperations(refreshOps);
