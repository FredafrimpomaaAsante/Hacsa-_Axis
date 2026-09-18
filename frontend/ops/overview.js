async function refreshOverview() {
  try {
    var id = await eventId();
    var overview = await api("/api/v1/analytics/overview?event_id=" + id);
    var zones = await api("/api/v1/occupancy/zones?event_id=" + id);
    var alerts = await api("/api/v1/alerts/?event_id=" + id);
    var people = await api("/participants");
    var incidents = await api("/api/v1/incidents/?event_id=" + id);
    var venues = zones.map(function (zone) {
      return { name: zone.zone_name, count: zone.current_count, capacity: zone.capacity };
    });
    var openIncidents = incidents.filter(function (item) {
      return !["resolved", "closed"].includes((item.status || "").toLowerCase());
    }).length;

    document.getElementById("overviewAttendance").textContent = people.filter(function (person) {
      return ["participant", "speaker"].includes(person.role);
    }).length;
    document.getElementById("overviewCheckins").textContent = overview.total_checked_in;
    document.getElementById("overviewOccupancy").textContent = occupancyFromVenues(venues) + "%";
    document.getElementById("overviewIncidents").textContent = openIncidents;
    renderVenueCards(document.getElementById("overviewVenues"), venues);

    var mappedAlerts = alerts.filter(function (alert) { return !alert.resolved; }).slice(0, 6);
    var alertHost = document.getElementById("overviewAlerts");
    alertHost.innerHTML = "";
    if (!mappedAlerts.length) {
      alertHost.innerHTML = '<li class="alert-item info">All systems operational. No active alerts.</li>';
    } else {
      mappedAlerts.forEach(function (alert) {
        var item = document.createElement("li");
        item.className = "alert-item " + alertLevel(alert.level);
        item.textContent = (alert.zone_name ? alert.zone_name + " · " : "") + alert.message;
        alertHost.appendChild(item);
      });
    }
    showOpsNotice("Live · last updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
  } catch (error) {
    showOpsNotice(error.message || "Could not load overview.", true);
  }
}

watchOperations(refreshOverview);
