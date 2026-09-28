(function () {
  var areas = [
    { id: "main-entrance", name: "Main Entrance", category: "Entry point", capacity: 300, team: "Guest Services", note: "Primary public entry, accessible arrival route and welcome point.", x: 65, y: 545, width: 230, height: 105, label: ["Main", "Entrance"] },
    { id: "registration", name: "Registration & Check-in", category: "Guest services", capacity: 200, team: "Registration Team A", note: "Badge pickup and guest check-in. Keep the queue clear of the east corridor.", x: 65, y: 365, width: 230, height: 155, label: ["Registration", "& Check-in"] },
    { id: "auditorium", name: "Main Auditorium", category: "Event space", capacity: 800, team: "Floor Team A", note: "Main stage, plenary seating and accessible seating area.", x: 65, y: 85, width: 490, height: 205, label: ["Main Auditorium"] },
    { id: "exhibition", name: "Exhibition Hall", category: "Event space", capacity: 500, team: "Operations Team B", note: "Exhibitor stands and demonstrations. Keep the eastern aisle open.", x: 575, y: 85, width: 365, height: 205, label: ["Exhibition Hall"] },
    { id: "networking", name: "Networking Lounge", category: "Community space", capacity: 180, team: "Guest Services B", note: "Informal meetings and hosted networking tables.", x: 575, y: 370, width: 255, height: 255, label: ["Networking", "Lounge"] },
    { id: "speaker-prep", name: "Speaker Preparation Room", category: "Speaker services", capacity: 50, team: "Speaker Liaison", note: "Quiet preparation room near the auditorium access corridor.", x: 315, y: 370, width: 235, height: 120, label: ["Speaker Prep"] },
    { id: "media", name: "Media & Press Room", category: "Media", capacity: 35, team: "Communications Team", note: "Media check-in, interview holding and press work area.", x: 315, y: 510, width: 235, height: 140, label: ["Media & Press"] },
    { id: "first-aid", name: "First Aid Station", category: "Safety", capacity: 20, team: "Medical Team", note: "First aid and medical support point. This map is illustrative only.", x: 850, y: 370, width: 140, height: 120, label: ["First Aid"] },
    { id: "security", name: "Security Operations Post", category: "Safety", capacity: 30, team: "Security Team", note: "Security coordination post. No emergency response is dispatched by this demo.", x: 1005, y: 370, width: 145, height: 120, label: ["Security", "Post"] },
    { id: "restrooms", name: "Restrooms", category: "Guest facilities", capacity: 60, team: "Facilities Team", note: "Guest facilities. Occupancy sensor data is not available in this demo.", x: 850, y: 510, width: 300, height: 140, label: ["Restrooms"] },
    { id: "loading-bay", name: "Loading & Vendor Bay", category: "Vendor access", capacity: 150, team: "Vendor Team", note: "Vendor and service access. Keep the loading route clear.", x: 960, y: 85, width: 190, height: 205, label: ["Loading &", "Vendor Bay"] },
    { id: "emergency-exits", name: "Emergency Exits", category: "Safety & egress", capacity: 0, team: "Safety Team", note: "Illustrative exit positions only. Confirm the verified venue plan before use.", x: 65, y: 680, width: 1085, height: 36, label: ["Emergency Exits · north, east and south egress"] },
  ];

  var events = [
    {
      id: "hackathon",
      name: "HACSA Tech4Girls Hackathon",
      venue: "HACSA Innovation & Heritage Hub",
      city: "Accra, Ghana",
      address: null,
      coordinates: null,
      occupancy: { "main-entrance": 86, registration: 164, auditorium: 418, exhibition: 301, networking: 94, "speaker-prep": 18, media: 12, "first-aid": 2, security: 9, restrooms: null, "loading-bay": 31, "emergency-exits": null },
      incidents: [
        { id: "HACK-014", title: "Registration queue congestion", locationId: "registration", priority: "medium", status: "open", reportedAt: "09:42", team: "Registration Team A", description: "A queue is forming at badge pickup. Keep the accessible lane clear and open the second desk." },
        { id: "HACK-021", title: "Medical assistance requested", locationId: "exhibition", priority: "high", status: "acknowledged", reportedAt: "10:16", team: "Medical Team", description: "A guest requested assistance near the eastern demonstration aisle. This is simulated incident data." },
      ],
    },
    {
      id: "graduation",
      name: "Tech4Girls Cohort 5 Graduation",
      venue: "HACSA Campus",
      city: "Accra, Ghana",
      address: null,
      coordinates: null,
      occupancy: { "main-entrance": 132, registration: 182, auditorium: 712, exhibition: 104, networking: 146, "speaker-prep": 23, media: 21, "first-aid": 5, security: 13, restrooms: null, "loading-bay": 58, "emergency-exits": null },
      incidents: [
        { id: "GRAD-009", title: "Restricted access alert", locationId: "security", priority: "high", status: "open", reportedAt: "11:08", team: "Security Team", description: "An access check is required at the east service door. Verify credentials with the event lead." },
      ],
    },
    {
      id: "summit",
      name: "Sankofa Summit 2026",
      venue: "HACSA Innovation & Heritage Hub",
      city: "Accra, Ghana",
      address: null,
      coordinates: null,
      occupancy: { "main-entrance": 241, registration: 187, auditorium: 704, exhibition: 432, networking: 152, "speaker-prep": 34, media: 24, "first-aid": 8, security: 17, restrooms: null, "loading-bay": 72, "emergency-exits": null },
      incidents: [
        { id: "SUM-112", title: "Medical assistance requested", locationId: "exhibition", priority: "critical", status: "open", reportedAt: "12:24", team: "Medical Team", description: "Assistance requested near the eastern entrance of the Exhibition Hall. Demonstration incident only; no team is actually notified." },
        { id: "SUM-113", title: "Registration queue building", locationId: "registration", priority: "medium", status: "open", reportedAt: "12:31", team: "Guest Services", description: "The badge collection queue is approaching the circulation corridor. Redirect arrivals to the second check-in lane." },
      ],
    },
  ];

  function createEventSnapshot(eventId) {
    var selected = events.find(function (event) { return event.id === eventId; }) || events[0];
    return {
      id: selected.id,
      name: selected.name,
      venue: selected.venue,
      city: selected.city,
      address: selected.address,
      coordinates: selected.coordinates,
      locations: areas.map(function (area) {
        return Object.assign({}, area, { currentOccupancy: selected.occupancy[area.id] });
      }),
      incidents: selected.incidents.map(function (incident) { return Object.assign({}, incident); }),
    };
  }

  window.HACSA_VENUE_MAP_DATA = {
    areas: areas,
    events: events.map(function (event) { return { id: event.id, name: event.name }; }),
    createEventSnapshot: createEventSnapshot,
  };
})();