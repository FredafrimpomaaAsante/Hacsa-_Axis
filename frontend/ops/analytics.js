async function refreshAnalytics() {
  try {
    var id = await eventId();
    var overview = await api("/api/v1/analytics/overview?event_id=" + id);
    var timeline = await api("/api/v1/analytics/attendance-timeline?event_id=" + id);
    var people = await api("/participants");
    var barChart = document.getElementById("barChart");
    barChart.innerHTML = "";
    var hours = timeline.slice();
    if (!hours.length) {
      barChart.innerHTML = '<p class="empty-state">Check-in volume will appear here once guests start arriving.</p>';
    } else {
      var max = Math.max(1, ...hours.map(function (item) { return item.count; }));
      hours.forEach(function (item) {
        var col = document.createElement("div");
        col.className = "bar-col";
        var bar = document.createElement("div");
        bar.className = "bar";
        bar.style.height = Math.round((item.count / max) * 100) + "%";
        bar.title = item.count + " check-ins";
        var label = document.createElement("div");
        label.className = "bar-label";
        label.textContent = (item.bucket || "").slice(11, 16) || item.bucket;
        col.appendChild(bar);
        col.appendChild(label);
        barChart.appendChild(col);
      });
    }

    var busiest = (overview.zones || []).slice().sort(function (a, b) { return b.utilisation - a.utilisation; })[0];
    var staff = staffPeople(people).length || 1;
    var load = Math.min(100, Math.round(((overview.incidents.open + overview.incidents.in_progress + overview.active_alerts) / (staff * 2)) * 100));
    document.getElementById("analyticsCheckins").textContent = overview.total_checked_in;
    document.getElementById("analyticsWait").textContent = overview.incidents.average_response_seconds ? Math.round(overview.incidents.average_response_seconds / 60) + "m" : "0m";
    document.getElementById("analyticsThroughput").textContent = busiest ? Math.round(busiest.utilisation * 100) + "%" : "0%";
    document.getElementById("analyticsStaff").textContent = load + "%";
    document.getElementById("analyticsRejected").textContent = overview.rejected_scans;
    document.getElementById("analyticsOpenIncidents").textContent = overview.incidents.open + overview.incidents.in_progress;
    renderVenueCards(document.getElementById("analyticsZones"), (overview.zones || []).map(function (zone) {
      return { name: zone.zone_name, count: zone.current_count, capacity: zone.capacity };
    }));
    showOpsNotice("Live · last updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
  } catch (error) {
    showOpsNotice(error.message || "Could not load analytics.", true);
  }
}

watchOperations(refreshAnalytics);
