var opsPeople = [];
var eventCenterMap = null;
var eventCenterMarker = null;
var eventCenterMapKey = "";
var eventCenterSatelliteLayer = null;
var eventCenterStreetLayer = null;
var eventCenterLabelsLayer = null;
var eventCenterBaseLayer = "satellite";
var announcedUrgentIncidents = new Set();
var urgentAudioContext = null;
var urgentAlarmEnabled = false;

async function loadOpsState() {
  var id = await eventId();
  var appConfig = await api("/api/config");
  var overview = await api("/api/v1/analytics/overview?event_id=" + id);
  var zones = await api("/api/v1/occupancy/zones?event_id=" + id);
  var checkins = await api("/api/v1/attendance/check-ins?event_id=" + id);
  var alerts = await api("/api/v1/alerts/?event_id=" + id);
  var incidents = await api("/api/v1/incidents/?event_id=" + id);
  var people = await api("/participants");
  opsPeople = people;
  return {
    eventId: id,
    eventCenter: appConfig.event_center,
    totalRegistered: people.filter(function (person) {
      return ["participant", "speaker"].includes(person.role);
    }).length,
    checkedIn: overview.total_checked_in,
    staffCount: staffPeople(people).length,
    people: people,
    checkinRows: checkins,
    incidents: incidents,
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
  renderEventMap(state.eventCenter, state.venues, state.incidents, state.people);
  renderUrgentIncidentDialog(state.incidents, state.people);
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

function renderEventMap(center, venues, incidents, people) {
  center = center || {};
  incidents = incidents || [];
  people = people || [];
  var latitude = Number(center.latitude);
  var longitude = Number(center.longitude);
  var name = center.name || "HACSA Event Center";
  var location = center.location || "Accra, Ghana";
  var approximate = center.coordinates_approximate !== false;
  var nameLabel = document.getElementById("eventCenterName");
  var locationLabel = document.getElementById("eventCenterLocation");
  var precisionLabel = document.getElementById("eventCenterPrecision");
  var status = document.getElementById("eventMapStatus");
  var zoneCount = document.getElementById("mapZoneCount");
  var issueSummary = document.getElementById("mapIssueSummary");
  var zoneList = document.getElementById("mapZoneList");

  nameLabel.textContent = name;
  locationLabel.textContent = location;
  precisionLabel.textContent = approximate ? "Approximate location" : "Verified coordinates";
  precisionLabel.classList.toggle("verified", !approximate);
  var openIncidents = incidents.filter(function (incident) {
    return !["resolved", "closed"].includes(String(incident.status).toLowerCase());
  });
  var areas = [
    "Main Entrance",
    "Exhibition Hall",
    "VIP Lounge",
    "Loading Bay",
    "Main Auditorium",
    "Innovation Lab",
    "Heritage Hall",
  ];
  venues.forEach(function (venue) { if (!areas.includes(venue.name)) areas.push(venue.name); });
  openIncidents.forEach(function (incident) {
    if (incident.location && !areas.includes(incident.location)) areas.push(incident.location);
  });
  zoneCount.textContent = venues.length + " reporting";
  issueSummary.innerHTML = '<span aria-hidden="true">●</span> ' + (openIncidents.length
    ? openIncidents.length + (openIncidents.length === 1 ? " open help signal" : " open help signals")
    : "No open help signals");
  issueSummary.classList.toggle("has-signals", openIncidents.length > 0);
  zoneList.replaceChildren();

  if (!areas.length) {
    var empty = document.createElement("li");
    empty.className = "map-zone-empty";
    empty.textContent = "No venue areas available.";
    zoneList.appendChild(empty);
  }

  areas.forEach(function (area) {
    var venue = venues.find(function (item) { return item.name.toLowerCase() === area.toLowerCase(); });
    var areaIncidents = openIncidents.filter(function (incident) {
      return incident.location && incident.location.toLowerCase() === area.toLowerCase();
    });
    var percent = venue && venue.capacity ? Math.round((venue.count / venue.capacity) * 100) : 0;
    var item = document.createElement("li");
    item.className = "map-zone-item" + (areaIncidents.length ? " has-help-signal" : "");
    var heading = document.createElement("div");
    heading.className = "map-zone-heading";
    var zoneName = document.createElement("strong");
    zoneName.textContent = area;
    var occupancy = document.createElement("span");
    occupancy.textContent = venue ? venue.count + " / " + venue.capacity : "No sensor";
    if (areaIncidents.length) {
      var signal = document.createElement("span");
      signal.className = "map-help-signal";
      signal.textContent = "! " + areaIncidents.length + (areaIncidents.length === 1 ? " request" : " requests");
      heading.append(zoneName, signal, occupancy);
    } else {
      heading.append(zoneName, occupancy);
    }
    item.appendChild(heading);
    if (venue) {
      var meter = document.createElement("div");
      meter.className = "map-zone-meter";
      var fill = document.createElement("span");
      fill.className = occupancyTone(percent);
      fill.style.width = Math.max(0, Math.min(100, percent)) + "%";
      meter.appendChild(fill);
      item.appendChild(meter);
    }
    if (areaIncidents.length) {
      areaIncidents.forEach(function (incident) {
        var signalDetail = document.createElement("small");
        signalDetail.className = "map-help-detail";
        var reporter = people.find(function (person) {
          return String(person.id) === String(incident.reported_by)
            || String(person.person_id) === String(incident.reported_by);
        });
        signalDetail.textContent = (reporter ? reporter.full_name + " · " : "") + incident.description;
        item.appendChild(signalDetail);
        var resolveButton = document.createElement("button");
        resolveButton.type = "button";
        resolveButton.className = "map-resolve-button";
        resolveButton.dataset.resolveIncident = incident.id;
        resolveButton.textContent = "Mark resolved";
        item.appendChild(resolveButton);
      });
    }
    if (venue) {
      var stateLabel = document.createElement("small");
      stateLabel.textContent = occupancyLabel(percent) + " · " + percent + "% occupied";
      item.appendChild(stateLabel);
    }
    zoneList.appendChild(item);
  });

  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    status.textContent = "Configure event-center coordinates to show the map pin.";
    return;
  }
  if (!window.L) {
    status.textContent = "Interactive map tiles are unavailable. Live zone status is still shown.";
    return;
  }

  var coordinates = [latitude, longitude];
  var mapKey = latitude + "," + longitude;
  if (!eventCenterMap) {
    eventCenterMap = L.map("eventMap", { scrollWheelZoom: false }).setView(coordinates, approximate ? 16 : 18);
    eventCenterSatelliteLayer = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19,
      attribution: "Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    });
    eventCenterStreetLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    });
    eventCenterLabelsLayer = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19,
      attribution: "Labels &copy; Esri",
      pane: "overlayPane",
    });
    eventCenterMarker = L.marker(coordinates).addTo(eventCenterMap);
    setEventCenterBaseLayer(eventCenterBaseLayer);
    eventCenterMapKey = mapKey;
  } else if (eventCenterMapKey !== mapKey) {
    eventCenterMap.setView(coordinates, approximate ? 16 : 18);
    eventCenterMapKey = mapKey;
  }
  eventCenterMarker.setLatLng(coordinates);

  var popup = document.createElement("div");
  var popupName = document.createElement("strong");
  popupName.textContent = name;
  var popupLocation = document.createElement("div");
  popupLocation.textContent = location + (approximate ? " · approximate pin" : "");
  popup.append(popupName, popupLocation);
  eventCenterMarker.bindPopup(popup);
  status.textContent = approximate
    ? "Approximate Kanda pin · set verified coordinates in backend environment for exact directions."
    : "Verified event-center coordinates";
  window.requestAnimationFrame(function () { eventCenterMap.invalidateSize(); });
}

function setEventCenterBaseLayer(layerName) {
  if (!eventCenterMap || !eventCenterSatelliteLayer || !eventCenterStreetLayer) return;
  eventCenterBaseLayer = layerName === "streets" ? "streets" : "satellite";
  if (eventCenterBaseLayer === "satellite") {
    if (eventCenterMap.hasLayer(eventCenterStreetLayer)) eventCenterMap.removeLayer(eventCenterStreetLayer);
    eventCenterSatelliteLayer.addTo(eventCenterMap);
    if (eventCenterLabelsLayer) eventCenterLabelsLayer.addTo(eventCenterMap);
  } else {
    if (eventCenterMap.hasLayer(eventCenterSatelliteLayer)) eventCenterMap.removeLayer(eventCenterSatelliteLayer);
    if (eventCenterLabelsLayer && eventCenterMap.hasLayer(eventCenterLabelsLayer)) eventCenterMap.removeLayer(eventCenterLabelsLayer);
    eventCenterStreetLayer.addTo(eventCenterMap);
  }
  var satelliteButton = document.getElementById("mapSatellite");
  var streetsButton = document.getElementById("mapStreets");
  satelliteButton.classList.toggle("active", eventCenterBaseLayer === "satellite");
  satelliteButton.setAttribute("aria-pressed", String(eventCenterBaseLayer === "satellite"));
  streetsButton.classList.toggle("active", eventCenterBaseLayer === "streets");
  streetsButton.setAttribute("aria-pressed", String(eventCenterBaseLayer === "streets"));
}

function renderUrgentIncidentDialog(incidents, people) {
  var urgent = incidents.filter(function (incident) {
    var active = !["resolved", "closed"].includes(String(incident.status).toLowerCase());
    var priority = ["high", "critical"].includes(String(incident.severity).toLowerCase());
    return active && priority;
  });
  var newUrgent = urgent.filter(function (incident) {
    return !announcedUrgentIncidents.has(String(incident.id));
  });
  var dialog = document.getElementById("urgentIncidentDialog");
  if (!urgent.length) {
    dialog.hidden = true;
    return;
  }
  if (!newUrgent.length && dialog.hidden) return;
  newUrgent.forEach(function (incident) { announcedUrgentIncidents.add(String(incident.id)); });

  var title = document.getElementById("urgentIncidentTitle");
  var summary = document.getElementById("urgentIncidentSummary");
  var list = document.getElementById("urgentIncidentList");
  var hasMedicalEmergency = urgent.some(function (incident) {
    return String(incident.description || "").toLowerCase().includes("medical");
  });
  title.textContent = hasMedicalEmergency ? "Medical emergency reported" : "High-priority issue reported";
  summary.textContent = urgent.length + (urgent.length === 1
    ? " open urgent issue needs attention now."
    : " open urgent issues need attention now.");
  list.replaceChildren();

  urgent.forEach(function (incident) {
    var item = document.createElement("li");
    item.className = "urgent-incident-item";
    var heading = document.createElement("strong");
    heading.textContent = String(incident.severity).toUpperCase() + " · " + incident.location;
    var reporter = people.find(function (person) {
      return String(person.id) === String(incident.reported_by)
        || String(person.person_id) === String(incident.reported_by);
    });
    var detail = document.createElement("small");
    detail.textContent = (reporter ? reporter.full_name + " · " : "") + incident.description;
    var resolve = document.createElement("button");
    resolve.type = "button";
    resolve.className = "ghost-btn";
    resolve.dataset.resolveIncident = incident.id;
    resolve.textContent = "Mark resolved";
    item.append(heading, detail, resolve);
    list.appendChild(item);
  });

  dialog.hidden = false;
  if (newUrgent.length) playUrgentAlarm();
}

function updateAlarmToggle() {
  var button = document.getElementById("alarmToggle");
  if (!button) return;
  button.textContent = urgentAlarmEnabled ? "Mute alarm sound" : "Enable alarm sound";
  button.setAttribute("aria-pressed", String(urgentAlarmEnabled));
}

async function enableUrgentAlarm(quiet) {
  if (urgentAlarmEnabled) return;
  var AudioContextType = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextType) {
    if (!quiet) showOpsNotice("Audio alarms are unavailable in this browser; visual alerts remain active.", true);
    return;
  }
  try {
    if (!urgentAudioContext) urgentAudioContext = new AudioContextType();
    await urgentAudioContext.resume();
    urgentAlarmEnabled = urgentAudioContext.state === "running";
    updateAlarmToggle();
    if (urgentAlarmEnabled) {
      document.removeEventListener("pointerdown", unlockUrgentAlarmOnInteraction, true);
      document.removeEventListener("keydown", unlockUrgentAlarmOnInteraction, true);
      if (!document.getElementById("urgentIncidentDialog").hidden) playUrgentAlarm();
    }
    if (!quiet) showOpsNotice(urgentAlarmEnabled ? "Alarm sound enabled." : "Audio could not be enabled; visual alerts remain active.", !urgentAlarmEnabled);
  } catch (error) {
    if (!quiet) showOpsNotice("Audio could not be enabled; visual alerts remain active.", true);
  }
}

async function toggleUrgentAlarm() {
  if (urgentAlarmEnabled) {
    urgentAlarmEnabled = false;
    if (urgentAudioContext && urgentAudioContext.state === "running") {
      await urgentAudioContext.suspend();
    }
    updateAlarmToggle();
    return;
  }
  await enableUrgentAlarm(false);
}

function unlockUrgentAlarmOnInteraction(event) {
  if (event.target.closest && event.target.closest("#alarmToggle")) return;
  enableUrgentAlarm(true);
}

function playUrgentAlarm() {
  if (navigator.vibrate) navigator.vibrate([220, 100, 220]);
  if (!urgentAlarmEnabled || !urgentAudioContext) return;
  try {
    var context = urgentAudioContext;
    if (context.state !== "running") return;
    [0, 0.38, 0.76].forEach(function (offset) {
      var oscillator = context.createOscillator();
      var gain = context.createGain();
      var startAt = context.currentTime + offset;
      oscillator.type = "sine";
      oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(0.0001, startAt);
      gain.gain.exponentialRampToValueAtTime(0.08, startAt + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, startAt + 0.2);
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.start(startAt);
      oscillator.stop(startAt + 0.21);
    });
  } catch (error) {
    console.warn("Urgent alert sound unavailable.", error);
  }
}

async function resolveIncidentSignal(incidentId, button) {
  if (button) button.disabled = true;
  try {
    await api("/api/v1/incidents/" + incidentId + "/status", {
      method: "PATCH",
      body: JSON.stringify({ status: "resolved" }),
    });
    showOpsNotice("Issue marked resolved.");
    await refreshOps();
  } catch (error) {
    if (button) button.disabled = false;
    showOpsNotice(error.message || "Could not resolve the issue.", true);
  }
}

async function refreshActivity() {
  var list = document.getElementById("activityList");
  if (!list) return;
  try {
    var activities = await api("/api/v1/audit/activity?limit=20");
    list.innerHTML = "";
    if (!activities.length) {
      list.innerHTML = '<li class="activity-empty">No recent activity yet.</li>';
    } else {
      activities.forEach(function (activity) {
        var item = document.createElement("li");
        item.className = "activity-item";
        var detail = document.createElement("strong");
        detail.textContent = activity.detail || activity.action + " · " + activity.entity_type;
        var meta = document.createElement("small");
        meta.textContent = activity.actor_role + " · " + new Date(activity.created_at).toLocaleString();
        item.append(detail, meta);
        list.appendChild(item);
      });
    }
    document.getElementById("activityUpdated").textContent = "Updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    list.innerHTML = '<li class="activity-empty">Activity is temporarily unavailable.</li>';
  }
}

async function refreshOps() {
  try {
    var state = await loadOpsState();
    renderDashboard(state);
    refreshActivity();
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

document.addEventListener("pointerdown", unlockUrgentAlarmOnInteraction, true);
document.addEventListener("keydown", unlockUrgentAlarmOnInteraction, true);
watchOperations(refreshOps);
window.setInterval(refreshActivity, 30000);
updateAlarmToggle();
document.getElementById("alarmToggle").addEventListener("click", toggleUrgentAlarm);
document.getElementById("urgentIncidentDismiss").addEventListener("click", function () {
  document.getElementById("urgentIncidentDialog").hidden = true;
});
document.getElementById("mapSatellite").addEventListener("click", function () {
  setEventCenterBaseLayer("satellite");
});
document.getElementById("mapStreets").addEventListener("click", function () {
  setEventCenterBaseLayer("streets");
});
document.addEventListener("click", function (event) {
  var resolve = event.target.closest("[data-resolve-incident]");
  if (resolve) resolveIncidentSignal(resolve.dataset.resolveIncident, resolve);
});
