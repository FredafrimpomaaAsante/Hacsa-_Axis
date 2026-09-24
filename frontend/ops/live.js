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

function occupancyFromVenues(venues) {
  var capacity = venues.reduce(function (sum, venue) { return sum + (venue.capacity || 0); }, 0);
  var count = venues.reduce(function (sum, venue) { return sum + (venue.count || 0); }, 0);
  return capacity ? Math.round((count / capacity) * 100) : 0;
}

function personName(person) {
  return (person && (person.full_name || person.name || person.email)) || "Staff";
}

function findPerson(people, value) {
  var needle = String(value || "");
  return people.find(function (person) {
    return (
      String(person.id) === needle ||
      String(person.person_id) === needle ||
      person.email === needle
    );
  });
}

function guestLabel(row, people) {
  var match = findPerson(people, row.participant_id);
  if (match) return personName(match);
  var raw = String(row.participant_id || "Guest");
  if (raw.length > 18) return "Guest " + raw.slice(-4);
  return raw;
}

function gateLabel(method) {
  if (!method) return "Main gate";
  return String(method).replaceAll("_", " ");
}

function alertLevel(level) {
  if (level === "critical") return "critical";
  if (level === "elevated" || level === "warning") return "warning";
  return "info";
}

function showOpsNotice(message, isError) {
  var host = document.getElementById("opsNotice");
  if (!host) return;
  host.textContent = message || "";
  host.className = "ops-notice" + (message ? (isError ? " error" : " ok") : "");
}

function staffPeople(people) {
  return people.filter(function (person) {
    return ["organiser", "ops_lead", "staff", "safety_officer"].includes(person.role);
  });
}

function renderVenueCards(host, venues, options) {
  options = options || {};
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
    if (options.adjustable) {
      var actions = document.createElement("div");
      actions.className = "venue-actions";
      actions.innerHTML =
        '<button type="button" class="ghost-btn" data-zone="' + venue.name + '" data-delta="-5">-5</button>' +
        '<button type="button" class="ghost-btn" data-zone="' + venue.name + '" data-delta="5">+5</button>';
      node.appendChild(actions);
    }
    host.appendChild(node);
  });
}

function watchOperations(refresh) {
  refresh();
  setInterval(refresh, 15000);
  try {
    var socket = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws/operations");
    socket.onmessage = function () { refresh(); };
  } catch (error) {
    console.warn(error);
  }
}
