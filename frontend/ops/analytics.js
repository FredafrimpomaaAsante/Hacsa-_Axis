async function renderChart() {
  var id = await eventId();
  var overview = await api("/api/v1/analytics/overview?event_id=" + id);
  var timeline = await api("/api/v1/analytics/attendance-timeline?event_id=" + id);
  var barChart = document.getElementById("barChart");
  barChart.innerHTML = "";
  var max = Math.max(1, ...timeline.map(function (item) { return item.count; }));
  if (!timeline.length) {
    barChart.innerHTML = '<p class="empty-state">Check-in volume will appear here once guests start arriving.</p>';
  }
  (timeline.length ? timeline : []).forEach(function (item) {
    var col = document.createElement("div");
    col.className = "bar-col";
    var bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = Math.round((item.count / max) * 100) + "%";
    var label = document.createElement("div");
    label.className = "bar-label";
    label.textContent = (item.bucket || "").slice(11, 16) || item.bucket;
    col.appendChild(bar);
    col.appendChild(label);
    barChart.appendChild(col);
  });
  document.getElementById("analyticsCheckins").textContent = overview.total_checked_in;
  document.getElementById("analyticsWait").textContent = overview.incidents.average_response_seconds ? Math.round(overview.incidents.average_response_seconds / 60) + "m" : "0m";
  document.getElementById("analyticsThroughput").textContent = (overview.zones[0] ? Math.round(overview.zones[0].utilisation * 100) : 0) + "%";
  document.getElementById("analyticsStaff").textContent = overview.active_alerts + " alerts";
}

renderChart().catch(function () {});
