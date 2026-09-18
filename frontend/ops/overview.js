async function loadOverview() {
  var id = await eventId();
  var overview = await api("/api/v1/analytics/overview?event_id=" + id);
  var zones = await api("/api/v1/occupancy/zones?event_id=" + id);
  var alerts = await api("/api/v1/alerts/?event_id=" + id).catch(function () { return []; });
  var people = await api("/participants").catch(function () { return []; });
  var incidents = await api("/api/v1/incidents/?event_id=" + id).catch(function () { return []; });
  var venues = zones.map(function (zone) {
    return { name: zone.zone_name, count: zone.current_count, capacity: zone.capacity };
  });
  var capacity = venues.reduce(function (sum, venue) { return sum + (venue.capacity || 0); }, 0);
  var count = venues.reduce(function (sum, venue) { return sum + (venue.count || 0); }, 0);
  var occupancy = capacity ? Math.round((count / capacity) * 100) : 0;
  var openIncidents = incidents.filter(function (item) {
    return !["resolved", "closed"].includes((item.status || "").toLowerCase());
  }).length;

  document.getElementById("overviewAttendance").textContent = people.length || overview.total_checked_in;
  document.getElementById("overviewCheckins").textContent = overview.total_checked_in;
  document.getElementById("overviewOccupancy").textContent = occupancy + "%";
  document.getElementById("overviewIncidents").textContent = openIncidents;

  var venueHost = document.getElementById("overviewVenues");
  venueHost.innerHTML = "";
  if (!venues.length) {
    venueHost.innerHTML = '<p class="empty-state">No venues reporting occupancy yet.</p>';
  } else {
    venues.forEach(function (venue) {
      var percent = venue.capacity ? Math.round((venue.count / venue.capacity) * 100) : 0;
      var tone = percent > 85 ? "red" : percent > 60 ? "yellow" : "green";
      var status = percent > 85 ? "Near capacity" : percent > 60 ? "Busy" : "Comfortable";
      var node = document.createElement("article");
      node.className = "venue-card";
      node.innerHTML =
        '<div class="venue-row"><span>' + venue.name + "</span><strong>" + venue.count + " / " + venue.capacity + "</strong></div>" +
        '<div class="venue-status"><span>' + status + "</span><span>" + percent + "%</span></div>" +
        '<div class="venue-progress"><div class="venue-progress-bar ' + tone + '" style="width: ' + percent + '%"></div></div>';
      venueHost.appendChild(node);
    });
  }

  var mappedAlerts = (alerts.length ? alerts : [{ message: "All systems operational. No active alerts.", level: "info" }]).slice(0, 6);
  var alertHost = document.getElementById("overviewAlerts");
  alertHost.innerHTML = "";
  mappedAlerts.forEach(function (alert) {
    var item = document.createElement("li");
    var level = alert.level === "critical" ? "critical" : alert.level === "elevated" || alert.level === "warning" ? "warning" : "info";
    item.className = "alert-item " + level;
    item.textContent = alert.message || alert.text;
    alertHost.appendChild(item);
  });
}

loadOverview().catch(function () {});
