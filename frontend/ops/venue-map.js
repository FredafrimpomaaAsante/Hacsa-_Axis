(function () {
  var data = window.HACSA_VENUE_MAP_DATA;
  var svgNamespace = "http://www.w3.org/2000/svg";
  var numberFormat = new Intl.NumberFormat();
  var eventSelector = document.getElementById("eventSelector");
  var locationLayer = document.getElementById("venueLocationLayer");
  var locationDetails = document.getElementById("locationDetails");
  var incidentList = document.getElementById("incidentList");
  var incidentDialog = document.getElementById("incidentDialog");
  var incidentDialogContent = document.getElementById("incidentDialogContent");
  var notificationPanel = document.getElementById("notificationPanel");
  var floorPlan = document.getElementById("venueFloorPlan");
  var selectedEvent = data.createEventSnapshot(data.events[0].id);
  var selectedAreaId = "main-entrance";
  var statusFilter = "all";
  var searchQuery = "";
  var zoomLevel = 1;
  var refreshCount = 0;
  var activeIncidentId = null;
  var baseViewBox = { x: 0, y: 0, width: 1220, height: 760 };

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
    });
  }

  function findArea(areaId) {
    return selectedEvent.locations.find(function (area) { return area.id === areaId; }) || null;
  }

  function findIncident(incidentId) {
    return selectedEvent.incidents.find(function (incident) { return incident.id === incidentId; }) || null;
  }

  function incidentsForArea(areaId) {
    return selectedEvent.incidents.filter(function (incident) {
      return incident.locationId === areaId && !["resolved", "closed"].includes(incident.status);
    });
  }

  function occupancyPercent(area) {
    if (area.currentOccupancy == null || !area.capacity) return null;
    return Math.max(0, Math.min(100, Math.round((area.currentOccupancy / area.capacity) * 100)));
  }

  function areaStatus(area) {
    if (area.currentOccupancy == null || !area.capacity) return "no-data";
    var openIncidents = incidentsForArea(area.id);
    if (openIncidents.some(function (incident) { return ["high", "critical"].includes(incident.priority); })) return "critical";
    var percent = occupancyPercent(area);
    if (percent >= 95) return "critical";
    if (percent >= 80) return "warning";
    return "normal";
  }

  function statusLabel(status) {
    return {
      normal: "Normal operations",
      warning: "Warning",
      critical: "Critical",
      "no-data": "No operational data",
    }[status] || "No operational data";
  }

  function formatOccupancy(area) {
    var percent = occupancyPercent(area);
    return percent == null ? "No data" : numberFormat.format(area.currentOccupancy) + " people · " + percent + "%";
  }

  function setSvgText(parent, className, x, y, value, anchor) {
    var text = document.createElementNS(svgNamespace, "text");
    text.setAttribute("class", className);
    text.setAttribute("x", x);
    text.setAttribute("y", y);
    text.setAttribute("text-anchor", anchor || "middle");
    text.textContent = value;
    parent.appendChild(text);
    return text;
  }

  function createRoomGroup(area) {
    var status = areaStatus(area);
    var percent = occupancyPercent(area);
    var group = document.createElementNS(svgNamespace, "g");
    group.setAttribute("class", "floor-room status-" + status + (area.id === selectedAreaId ? " selected" : ""));
    group.setAttribute("data-area-id", area.id);
    group.setAttribute("role", "button");
    group.setAttribute("tabindex", "0");
    group.setAttribute("aria-pressed", String(area.id === selectedAreaId));
    group.setAttribute("aria-label", area.name + ". " + statusLabel(status) + ". " + formatOccupancy(area));

    var title = document.createElementNS(svgNamespace, "title");
    var linkedIncidents = incidentsForArea(area.id);
    title.textContent = area.name + " · " + statusLabel(status) + " · " + formatOccupancy(area) + (linkedIncidents.length ? " · " + linkedIncidents.length + " active incident" + (linkedIncidents.length === 1 ? "" : "s") : "");
    group.appendChild(title);

    var room = document.createElementNS(svgNamespace, "rect");
    room.setAttribute("class", "room-shape");
    room.setAttribute("x", area.x);
    room.setAttribute("y", area.y);
    room.setAttribute("width", area.width);
    room.setAttribute("height", area.height);
    room.setAttribute("rx", area.id === "emergency-exits" ? 4 : 8);
    group.appendChild(room);

    if (area.id === "emergency-exits") {
      [145, 1035].forEach(function (x) {
        var exit = document.createElementNS(svgNamespace, "rect");
        exit.setAttribute("x", x);
        exit.setAttribute("y", area.y + 8);
        exit.setAttribute("width", 38);
        exit.setAttribute("height", 20);
        exit.setAttribute("rx", 3);
        exit.setAttribute("class", "exit-sign-box");
        group.appendChild(exit);
        setSvgText(group, "exit-sign-text", x + 19, area.y + 22, "EXIT");
      });
      var exitStatus = document.createElementNS(svgNamespace, "circle");
      exitStatus.setAttribute("class", "room-status-dot");
      exitStatus.setAttribute("cx", area.x + area.width - 18);
      exitStatus.setAttribute("cy", area.y + 18);
      exitStatus.setAttribute("r", 7);
      group.appendChild(exitStatus);
      setSvgText(group, "emergency-exit-icon", area.x + area.width / 2, area.y + 23, area.name + " · north, east and south egress");
      return group;
    }

    var dot = document.createElementNS(svgNamespace, "circle");
    dot.setAttribute("class", "room-status-dot");
    dot.setAttribute("cx", area.x + area.width - 18);
    dot.setAttribute("cy", area.y + 18);
    dot.setAttribute("r", 8);
    group.appendChild(dot);

    var lineHeight = 17;
    var labelStartY = area.y + area.height / 2 - ((area.label.length - 1) * lineHeight) / 2 - 4;
    var label = document.createElementNS(svgNamespace, "text");
    label.setAttribute("class", "room-label");
    label.setAttribute("x", area.x + area.width / 2);
    label.setAttribute("y", labelStartY);
    label.setAttribute("text-anchor", "middle");
    area.label.forEach(function (line, index) {
      var tspan = document.createElementNS(svgNamespace, "tspan");
      tspan.setAttribute("x", area.x + area.width / 2);
      tspan.setAttribute("dy", index === 0 ? 0 : lineHeight);
      tspan.textContent = line;
      label.appendChild(tspan);
    });
    group.appendChild(label);

    var detailY = area.y + area.height - 20;
    setSvgText(group, "room-status-text", area.x + area.width / 2, detailY - 13, statusLabel(status));
    setSvgText(group, "room-occupancy-text", area.x + area.width / 2, detailY + 1, percent == null ? "Occupancy unavailable" : percent + "% occupied");
    return group;
  }

  function roomMatches(area) {
    var text = (area.name + " " + area.category + " " + area.team).toLowerCase();
    var searchMatches = !searchQuery || text.includes(searchQuery);
    var status = areaStatus(area);
    var filterMatches = statusFilter === "all" || status === statusFilter;
    return searchMatches && filterMatches;
  }

  function renderMap() {
    locationLayer.replaceChildren();
    selectedEvent.locations.forEach(function (area) {
      var group = createRoomGroup(area);
      if (!roomMatches(area)) group.classList.add("filtered-out");
      locationLayer.appendChild(group);
    });
    var matches = selectedEvent.locations.filter(roomMatches).length;
    var summary = document.getElementById("filterSummary");
    summary.textContent = (searchQuery || statusFilter !== "all")
      ? matches + " of " + selectedEvent.locations.length + " areas match. Other areas remain visible."
      : "Select a room, or use the filters to locate an area.";
    updateZoom();
  }

  function activeIncidents() {
    return selectedEvent.incidents.filter(function (incident) { return !["resolved", "closed"].includes(incident.status); });
  }

  function renderStats() {
    var people = selectedEvent.locations.reduce(function (sum, area) {
      return sum + (area.currentOccupancy == null ? 0 : area.currentOccupancy);
    }, 0);
    var attention = selectedEvent.locations.filter(function (area) { return ["warning", "critical"].includes(areaStatus(area)); }).length;
    document.getElementById("statAreas").textContent = numberFormat.format(selectedEvent.locations.length);
    document.getElementById("statPeople").textContent = numberFormat.format(people);
    document.getElementById("statIncidents").textContent = numberFormat.format(activeIncidents().length);
    document.getElementById("statAttention").textContent = numberFormat.format(attention);
  }

  function renderLocationDetails() {
    var area = findArea(selectedAreaId);
    if (!area) {
      locationDetails.innerHTML = "";
      document.getElementById("detailsEmpty").hidden = false;
      return;
    }
    document.getElementById("detailsEmpty").hidden = true;
    var status = areaStatus(area);
    var percent = occupancyPercent(area);
    var linked = incidentsForArea(area.id);
    var incidentHtml = linked.length
      ? linked.map(function (incident) {
        return '<div class="detail-incident ' + (["high", "critical"].includes(incident.priority) ? "critical" : "") + '"><strong>' + escapeHtml(incident.title) + ' · ' + escapeHtml(incident.priority) + '</strong><p>' + escapeHtml(incident.description) + '</p><button type="button" class="text-button" data-view-incident="' + escapeHtml(incident.id) + '">View Incident</button></div>';
      }).join("")
      : '<p class="detail-note">No active simulated incidents for this area.</p>';
    var progressWidth = percent == null ? 0 : percent;
    var fillStatus = status === "critical" ? "critical" : status === "warning" ? "warning" : "";
    locationDetails.innerHTML =
      '<div class="location-details-head"><div><span class="eyebrow">SELECTED LOCATION</span><h2 id="detailsTitle">' + escapeHtml(area.name) + '</h2><span class="location-category">' + escapeHtml(area.category) + '</span><br><span class="status-badge status-' + status + '">' + statusLabel(status) + '</span></div><button type="button" class="close-details" data-close-details aria-label="Clear selected location">×</button></div>' +
      '<div class="detail-occupancy"><div class="detail-occupancy-top"><strong>' + (area.currentOccupancy == null ? "—" : numberFormat.format(area.currentOccupancy)) + '</strong><span>' + (area.capacity ? 'of ' + numberFormat.format(area.capacity) + ' people' : 'Occupancy not available') + '</span></div><div class="occupancy-track" role="img" aria-label="Occupancy ' + (percent == null ? "unavailable" : percent + "%") + '"><div class="occupancy-fill ' + fillStatus + '" style="width:' + progressWidth + '%"></div></div><span class="location-category">' + (percent == null ? 'No occupancy percentage reported' : percent + '% of maximum capacity') + '</span></div>' +
      '<div class="detail-facts"><div class="detail-fact"><span>Maximum capacity</span><strong>' + (area.capacity ? numberFormat.format(area.capacity) + ' people' : 'Not configured') + '</strong></div><div class="detail-fact"><span>Assigned team</span><strong>' + escapeHtml(area.team) + '</strong></div></div>' +
      '<p class="detail-note">' + escapeHtml(area.note) + '</p><div class="detail-incidents"><span class="eyebrow">ACTIVE INCIDENTS · SIMULATED</span>' + incidentHtml + '</div>';
  }

  function renderIncidents() {
    var incidents = selectedEvent.incidents.slice().sort(function (first, second) {
      return first.reportedAt.localeCompare(second.reportedAt);
    });
    if (!incidents.length) {
      incidentList.innerHTML = '<p class="incident-empty">No demonstration incidents are listed for this event.</p>';
      return;
    }
    incidentList.innerHTML = incidents.map(function (incident) {
      var area = findArea(incident.locationId);
      var isClosed = ["resolved", "closed"].includes(incident.status);
      var actions = isClosed ? "" : '<div class="incident-row-actions">' + (incident.status === "open" ? '<button type="button" data-incident-action="acknowledged" data-incident-id="' + escapeHtml(incident.id) + '">Acknowledge</button>' : '') + '<button type="button" data-incident-action="resolved" data-incident-id="' + escapeHtml(incident.id) + '">Resolve</button></div>';
      return '<div class="incident-row"><button type="button" class="incident-title-button" data-open-incident="' + escapeHtml(incident.id) + '">' + escapeHtml(incident.id + ' · ' + incident.title) + '</button><span class="incident-meta">' + escapeHtml(area ? area.name : "Unknown area") + ' · ' + escapeHtml(incident.reportedAt) + '</span><span class="incident-priority ' + escapeHtml(incident.priority) + '">' + escapeHtml(incident.priority) + '</span><span class="incident-status">' + escapeHtml(incident.status) + '</span>' + actions + '</div>';
    }).join("");
  }

  function renderNotifications() {
    var incidents = activeIncidents();
    document.getElementById("notificationCount").textContent = incidents.length;
    document.getElementById("notificationToggle").setAttribute("aria-label", "Show " + incidents.length + " demonstration notifications");
    document.getElementById("notificationList").innerHTML = incidents.length
      ? incidents.slice(0, 4).map(function (incident) {
        var area = findArea(incident.locationId);
        return '<div class="notification-item"><strong>' + escapeHtml(incident.title) + '</strong><span>' + escapeHtml(area ? area.name : "Unknown area") + ' · ' + escapeHtml(incident.priority) + ' priority · Simulated report</span></div>';
      }).join("")
      : '<div class="notification-item"><strong>No active notifications</strong><span>Mock notifications update when demonstration incidents change.</span></div>';
  }

  function renderVenueHeader() {
    document.getElementById("venueName").textContent = selectedEvent.venue;
    document.getElementById("venueCity").textContent = selectedEvent.city;
    var directions = document.getElementById("directionsButton");
    var hasVerifiedLocation = Boolean(selectedEvent.address || selectedEvent.coordinates);
    directions.disabled = !hasVerifiedLocation;
    directions.title = hasVerifiedLocation ? "Open verified venue directions" : "Directions are unavailable until a verified address is configured";
    document.getElementById("venueAddressState").textContent = hasVerifiedLocation ? "Verified venue location" : "Venue address not verified";
  }

  function renderAll() {
    renderVenueHeader();
    renderStats();
    renderMap();
    renderLocationDetails();
    renderIncidents();
    renderNotifications();
  }

  function updateZoom() {
    var width = baseViewBox.width / zoomLevel;
    var height = baseViewBox.height / zoomLevel;
    var x = (baseViewBox.width - width) / 2;
    var y = (baseViewBox.height - height) / 2;
    floorPlan.setAttribute("viewBox", [x, y, width, height].join(" "));
    document.getElementById("zoomIn").disabled = zoomLevel >= 1.8;
    document.getElementById("zoomOut").disabled = zoomLevel <= 1;
  }

  function setSelectedArea(areaId) {
    if (!findArea(areaId)) return;
    selectedAreaId = areaId;
    renderMap();
    renderLocationDetails();
  }

  function openIncidentDialog(incidentId) {
    var incident = findIncident(incidentId);
    if (!incident) return;
    activeIncidentId = incident.id;
    var area = findArea(incident.locationId);
    var closed = ["resolved", "closed"].includes(incident.status);
    incidentDialogContent.innerHTML =
      '<h2 id="incidentDialogTitle">' + escapeHtml(incident.title) + '</h2>' +
      '<p>' + escapeHtml(incident.description) + '</p>' +
      '<div class="incident-dialog-grid"><div><span>Incident ID</span><strong>' + escapeHtml(incident.id) + '</strong></div><div><span>Location</span><strong>' + escapeHtml(area ? area.name : "Unknown area") + '</strong></div><div><span>Priority</span><strong>' + escapeHtml(incident.priority.toUpperCase()) + '</strong></div><div><span>Status</span><strong>' + escapeHtml(incident.status) + '</strong></div><div><span>Assigned team</span><strong>' + escapeHtml(incident.team) + '</strong></div><div><span>Time reported</span><strong>' + escapeHtml(incident.reportedAt) + '</strong></div></div>' +
      '<p class="incident-data-note">This is simulated demonstration data. No emergency team is being notified.</p>' +
      '<div class="incident-dialog-actions">' + (closed ? '' : (incident.status === "open" ? '<button type="button" data-dialog-action="acknowledged">Mark acknowledged</button>' : '') + '<button type="button" class="secondary" data-dialog-action="resolved">Mark resolved</button>') + '</div>';
    if (!incidentDialog.open) incidentDialog.showModal();
  }

  function updateIncidentStatus(incidentId, status) {
    var incident = findIncident(incidentId);
    if (!incident) return;
    incident.status = status;
    renderAll();
    if (incidentDialog.open && activeIncidentId === incident.id) openIncidentDialog(incident.id);
    document.getElementById("updateStatus").textContent = "Simulated incident " + incident.id + " marked " + status + ".";
  }

  function resetView() {
    selectedAreaId = "main-entrance";
    zoomLevel = 1;
    statusFilter = "all";
    searchQuery = "";
    document.getElementById("statusFilter").value = "all";
    document.getElementById("locationSearch").value = "";
    renderAll();
  }

  function refreshDemoData() {
    refreshCount += 1;
    var changes = [3, -2, 4, -1, 2, 0, -3, 1, 0, 0, -2, 0];
    selectedEvent.locations.forEach(function (area, index) {
      if (area.currentOccupancy == null || !area.capacity) return;
      var delta = changes[(index + refreshCount - 1) % changes.length];
      area.currentOccupancy = Math.max(0, Math.min(area.capacity, area.currentOccupancy + delta));
    });
    renderAll();
    document.getElementById("updateStatus").textContent = "Demo data refreshed locally at " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + ".";
  }

  data.events.forEach(function (event) {
    var option = document.createElement("option");
    option.value = event.id;
    option.textContent = event.name;
    eventSelector.appendChild(option);
  });

  eventSelector.addEventListener("change", function () {
    selectedEvent = data.createEventSnapshot(eventSelector.value);
    resetView();
    document.getElementById("updateStatus").textContent = "Showing local demonstration data for " + selectedEvent.name + ".";
  });

  locationLayer.addEventListener("click", function (event) {
    var target = event.target.closest("[data-area-id]");
    if (target) setSelectedArea(target.getAttribute("data-area-id"));
  });

  locationLayer.addEventListener("keydown", function (event) {
    var target = event.target.closest("[data-area-id]");
    if (!target || !["Enter", " "].includes(event.key)) return;
    event.preventDefault();
    setSelectedArea(target.getAttribute("data-area-id"));
  });

  document.getElementById("locationSearch").addEventListener("input", function (event) {
    searchQuery = event.target.value.trim().toLowerCase();
    renderMap();
  });

  document.getElementById("statusFilter").addEventListener("change", function (event) {
    statusFilter = event.target.value;
    renderMap();
  });

  document.getElementById("zoomIn").addEventListener("click", function () {
    zoomLevel = Math.min(1.8, Math.round((zoomLevel + 0.2) * 10) / 10);
    updateZoom();
  });

  document.getElementById("zoomOut").addEventListener("click", function () {
    zoomLevel = Math.max(1, Math.round((zoomLevel - 0.2) * 10) / 10);
    updateZoom();
  });

  document.getElementById("resetMap").addEventListener("click", resetView);
  document.getElementById("refreshDemo").addEventListener("click", refreshDemoData);

  document.getElementById("fullscreenMap").addEventListener("click", async function () {
    var panel = document.getElementById("floorPlanPanel");
    if (!document.fullscreenElement && panel.requestFullscreen) await panel.requestFullscreen();
    else if (document.fullscreenElement && document.exitFullscreen) await document.exitFullscreen();
  });

  document.addEventListener("fullscreenchange", function () {
    document.getElementById("fullscreenMap").textContent = document.fullscreenElement ? "Exit fullscreen" : "Fullscreen";
  });

  locationDetails.addEventListener("click", function (event) {
    var incidentButton = event.target.closest("[data-view-incident]");
    if (incidentButton) openIncidentDialog(incidentButton.dataset.viewIncident);
  });

  incidentList.addEventListener("click", function (event) {
    var incidentButton = event.target.closest("[data-open-incident]");
    if (incidentButton) {
      var incident = findIncident(incidentButton.dataset.openIncident);
      if (incident) setSelectedArea(incident.locationId);
      openIncidentDialog(incidentButton.dataset.openIncident);
      return;
    }
    var actionButton = event.target.closest("[data-incident-action]");
    if (actionButton) updateIncidentStatus(actionButton.dataset.incidentId, actionButton.dataset.incidentAction);
  });

  incidentDialog.addEventListener("click", function (event) {
    if (event.target === incidentDialog) incidentDialog.close();
    var actionButton = event.target.closest("[data-dialog-action]");
    if (actionButton && activeIncidentId) updateIncidentStatus(activeIncidentId, actionButton.dataset.dialogAction);
  });

  document.getElementById("closeIncidentDialog").addEventListener("click", function () { incidentDialog.close(); });

  document.getElementById("notificationToggle").addEventListener("click", function (event) {
    var isOpen = event.currentTarget.getAttribute("aria-expanded") === "true";
    event.currentTarget.setAttribute("aria-expanded", String(!isOpen));
    notificationPanel.hidden = isOpen;
  });
  document.getElementById("closeNotifications").addEventListener("click", function () {
    notificationPanel.hidden = true;
    document.getElementById("notificationToggle").setAttribute("aria-expanded", "false");
  });

  document.getElementById("directionsButton").addEventListener("click", function () {
    if (selectedEvent.address) window.open("https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(selectedEvent.address), "_blank", "noopener");
    else if (selectedEvent.coordinates) window.open("https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(selectedEvent.coordinates.join(",")), "_blank", "noopener");
  });

  renderAll();
  document.getElementById("updateStatus").textContent = "Local demonstration data · not connected to venue sensors.";
})();