const state={view:'dashboard',role:'participant',name:'Lawrencia A.',email:'lawrencia@example.com',personId:null,category:'Participant',activeEventId:null,saved:[],poll:null,scanner:null,authenticated:false,notifications:[]};
const roleLabels={participant:'Participant',speaker:'Speaker'};
const authStoreKey='hacsaAxisMockAuth';
const readAuthStore=()=>JSON.parse(localStorage.getItem(authStoreKey)||'{"registrations":[],"audit":[]}');
const writeAuthStore=store=>localStorage.setItem(authStoreKey,JSON.stringify(store));
const mockDigest=async value=>{const bytes=new TextEncoder().encode(value);const hash=await crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(hash)].map(byte=>byte.toString(16).padStart(2,'0')).join('')};
const roleNavigation={participant:[['dashboard','⌂','Overview'],['schedule','▦','My Schedule'],['badge','▣','Digital Badge'],['networking','◎','Networking'],['engage','◈','Polls & Feedback'],['support','⚑','Support'],['donate','✦','Support HACSA']],speaker:[['speaker','✦','Speaker Studio'],['schedule','▦','My Schedule'],['engage','◈','Polls & Feedback'],['support','⚑','Support'],['donate','✦','Support HACSA']]};
const networkingFallback=[{id:'n-1',name:'Ama Mensah',role:'Tech4Girls mentor',organisation:'HACSA Foundation',location:'Accra, Ghana',interests:['Youth innovation','Education'],initials:'AM'},{id:'n-2',name:'Kwame Boateng',role:'Heritage entrepreneur',organisation:'Sankofa Collective',location:'Kumasi, Ghana',interests:['Culture','Creative economy'],initials:'KB'},{id:'n-3',name:'Nia Williams',role:'Diaspora partnerships lead',organisation:'Africa Connect',location:'London, UK',interests:['Diaspora','Community building'],initials:'NW'},{id:'n-4',name:'Kofi Asante',role:'Technology strategist',organisation:'Open Futures Lab',location:'Accra, Ghana',interests:['Technology','Social impact'],initials:'KA'}];
const networkingFallbackStatuses={'n-1':'pending','n-2':'accepted','n-3':'denied','n-4':'none'};
const networkingStatuses={};
const sessions=[{id:1,date:'Thu, 10 Dec',time:'09:00',title:'Opening Ceremony & Welcome',venue:'HACSA Innovation & Heritage Hub',type:'Opening'},{id:2,date:'Thu, 10 Dec',time:'11:00',title:'Africa’s Future: Heritage, Innovation & Opportunity',venue:'Main Auditorium',type:'Panel'},{id:3,date:'Fri, 11 Dec',time:'10:00',title:'Women and Girls in Technology',venue:'Innovation Lab',type:'Workshop'},{id:4,date:'Sat, 12 Dec',time:'14:00',title:'Sankofa Dialogue: Reclaiming Our Narratives',venue:'Heritage Hall',type:'Dialogue'},{id:5,date:'Sun, 13 Dec',time:'12:30',title:'Heritage Brunch & Afrobeat Send-off',venue:'HACSA Innovation & Heritage Hub',type:'Experience'},{id:6,date:'Tue, 15 Dec',time:'16:00',title:'Closing Reflections & Commitments',venue:'Main Auditorium',type:'Closing'}];

const upcomingEvents=[
{id:'hackathon',title:'HACSA Tech4Girls Hackathon',date:'18 September 2026',venue:'HACSA Campus',kind:'Innovation & youth technology',image:'images/istockphoto-1216719230-170667a.jpg',officialUrl:'https://www.thehacsa.org/tech4girls/'},
{id:'graduation',title:'Tech4Girls Cohort 5 Graduation',date:'29 September 2026',venue:'HACSA Campus',kind:'Celebration & learning',image:'images/tech4girls.webp',officialUrl:'https://www.thehacsa.org/tech4girls/'},
{id:'summit',title:'Sankofa Summit 2026',date:'10–15 December 2026',venue:'Accra, Ghana',kind:'Culture, heritage & global connection',image:'images/OIP.webp'}
];

function parseEventDate(dateText){
  if (!dateText) return null;
  const normalized = String(dateText).trim().replace(/–|—/g, '-');

  const rangeMatch = normalized.match(/^(\d{1,2})\s*[-]\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$/i);
  if (rangeMatch) {
    const [, startDay, endDay, monthName, year] = rangeMatch;
    const start = new Date(`${monthName} ${startDay}, ${year}`);
    const end = new Date(`${monthName} ${endDay}, ${year}`);
    if (!Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime())) {
      return { start, end };
    }
  }

  const singleMatch = normalized.match(/^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$/i);
  if (singleMatch) {
    const [, day, monthName, year] = singleMatch;
    const parsed = new Date(`${monthName} ${day}, ${year}`);
    if (!Number.isNaN(parsed.getTime())) {
      return { start: parsed, end: parsed };
    }
  }

  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : { start: parsed, end: parsed };
}

function eventStatusLabel(event){
  const dateRange = parseEventDate(event.date);
  if (!dateRange) return 'Upcoming Event';

  const today = new Date();
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const startDate = new Date(dateRange.start.getFullYear(), dateRange.start.getMonth(), dateRange.start.getDate());
  const endDate = new Date(dateRange.end.getFullYear(), dateRange.end.getMonth(), dateRange.end.getDate());

  if (startDate > todayStart) return 'Upcoming Event';
  if (endDate < todayStart) return 'Past Event';
  return 'Ongoing Event';
}
const speakerPhotos=['images/adjoa-b-asamoah.webp','images/peterAKWABOAH.webp','images/tonyeCOLE.jpeg','images/nanaABA.jpg'];
const speakerPhotoByName={'dr. adjoa asamoah':speakerPhotos[0],'peter akwaboah':speakerPhotos[1],'tonye cole':speakerPhotos[2],'nana aba anamoah':speakerPhotos[3]};
let featuredSpeakers=[{name:'Dr. Adjoa Asamoah',title:'Policy strategist & social impact advisor',organization:'HACSA Foundation',photo_url:speakerPhotos[0]},{name:'Peter Akwaboah',title:'Featured speaker',organization:'HACSA Axis',photo_url:speakerPhotos[1]},{name:'Tonye Cole',title:'Co-founder, Sahara Group',organization:'Sahara Group',photo_url:speakerPhotos[2]},{name:'Nana Aba Anamoah',title:'Media personality & broadcaster',organization:'HACSA Axis',photo_url:speakerPhotos[3]}];
function speakerPhoto(index,url,name){return speakerPhotoByName[(name||'').trim().toLowerCase()]||url||speakerPhotos[index%speakerPhotos.length]}
function speakerCardsHtml(){return featuredSpeakers.map((speaker,index)=>`<article class="speaker-photo-card"><img src="${speakerPhoto(index,speaker.photo_url,speaker.name)}" alt="${speaker.name}"><div><h4>${speaker.name}</h4><p class="muted">${speaker.title||speaker.expertise||'Speaker'} · ${speaker.organization||'HACSA Axis'}</p></div></article>`).join('')}
const speakerAssignments=[{id:'sp-1',event:'Sankofa Summit 2026',date:'Thu, 10 Dec 2026',time:'11:00–12:00',title:'Africa’s Future: Heritage, Innovation & Opportunity',venue:'Main Auditorium',type:'Panel',status:'Confirmed',prep:'Review panel prompts, arrival time and technical check-in.'},{id:'sp-2',event:'Sankofa Summit 2026',date:'Fri, 11 Dec 2026',time:'10:00–11:30',title:'Women and Girls in Technology',venue:'Innovation Lab',type:'Workshop',status:'Confirmed',prep:'Bring your workshop outline and confirm presentation format.'},{id:'sp-3',event:'Sankofa Summit 2026',date:'Sat, 12 Dec 2026',time:'14:00–15:00',title:'Sankofa Dialogue: Reclaiming Our Narratives',venue:'Heritage Hall',type:'Dialogue',status:'Planning',prep:'Prepare key reflections and discussion prompts.'},{id:'sp-4',event:'Sankofa Summit 2026',date:'Sun, 13 Dec 2026',time:'12:30–15:30',title:'Heritage Brunch & Afrobeat Send-off',venue:'HACSA Innovation & Heritage Hub',type:'Experience',status:'Planning',prep:'Confirm participation format with the programme team.'}];
const $=s=>document.querySelector(s);const content=$('#content');
function toast(msg){$('#toast').textContent=msg;$('#toast').classList.add('show');setTimeout(()=>$('#toast').classList.remove('show'),2800)}
function openModal(html){$('#modalBody').innerHTML=html;$('#modal').classList.remove('hidden')};function closeModal(){$('#modal').classList.add('hidden')}
function header(title){$('#pageTitle').textContent=title}
function button(label,fn,cls='btn'){return `<button class="${cls}" data-action="${fn}">${label}</button>`}
function nameInitials(name){const parts=(name||'').trim().split(/\s+/).filter(Boolean);return parts.length>1?`${parts[0][0]}${parts[parts.length-1][0]}`.toUpperCase():(parts[0]||'HA').slice(0,2).toUpperCase()}
function updateProfileInitials(){const avatar=$('#profileBtn');if(avatar)avatar.textContent=nameInitials(state.name)}
function render(){const links=roleNavigation[state.role]||roleNavigation.participant;$('#nav').innerHTML=links.map(([view,icon,label])=>`<button class="nav-link ${view===state.view?'active':''}" data-view="${view}">${icon} <span>${label}</span></button>`).join('');$('#roleStatus').innerHTML=`<strong>${roleLabels[state.role]} access</strong><button data-action="signOut()">Sign out</button>`;const titles={dashboard:'Welcome to your axis',events:'Upcoming HACSA events',schedule:state.role==='speaker'?'My speaker schedule':'Your summit schedule',badge:'Digital access',networking:'Networking',scanner:'Verify a badge',engage:'Polls & Feedback',support:'We are here to help',donate:'Support the work behind the summit',assistant:'Axis AI Assistant',accessibility:'Accessibility tools',speaker:'Speaker workspace'};header(titles[state.view]);const views={dashboard,events,schedule,badge,networking,scanner,engage,support,donate,speaker};if(views[state.view])views[state.view]();}
function dashboard(){content.innerHTML=`
<div class="home-hero"><div class="hero-overlay"><span class="tag">HACSA AXIS · CULTURE • HERITAGE • POSSIBILITY</span><h2>Welcome to HACSA Axis.</h2><p>A welcoming digital event space for participants and speakers to discover HACSA programmes, celebrate Ghanaian and African heritage, connect with the diaspora, and participate in meaningful experiences.</p><div class="hero-meta"><span>Ghana · Diaspora · Shared heritage</span><span>Events · Community · Connection</span></div></div></div>
<div class="page-intro"><h2>Explore HACSA's Events</h2><p>Select an event to view its details, programme information, participation guidance and official updates.</p></div><div class="event-grid">${upcomingEvents.map(eventCard).join('')}</div>
<div class="card compact-intro"><img src="images/heritage.png" alt="African heritage at HACSA Axis"><div><span class="tag">ABOUT HACSA AXIS</span><h3>One place to discover, attend and connect.</h3><p class="muted">Your event-specific tools—agenda, saved sessions, access category, badge status, engagement and support—are available after you open an event.</p></div></div>
<div class="section-head"><h3>Featured speakers</h3></div><div class="speaker-photo-grid">${speakerCardsHtml()}</div>`}
function eventCard(e){const status=eventStatusLabel(e);const eventStateClass=status==='Past Event' ? 'event-state past' : status==='Ongoing Event' ? 'event-state ongoing' : 'event-state upcoming';return `<button class="event-card" data-action="eventDetails('${e.id}')"><div class="event-image ${e.id}"><span>${e.id==='summit'?'SANKOFA SUMMIT':'HACSA'}</span></div><div class="event-card-body"><span class="tag ${eventStateClass}">${status}</span><h4>${e.title}</h4><p>${e.date}</p><p>${e.venue}</p><span class="event-link">Explore event →</span></div></button>`}
function events(){content.innerHTML=`<div class="page-intro"><h2>Explore HACSA's Events</h2><p>Discover programmes connecting culture, heritage, education, technology and the diaspora.</p></div><div class="event-grid">${upcomingEvents.map(eventCard).join('')}</div>`}
function eventDetails(id){
const e=upcomingEvents.find(x=>x.id===id);
state.activeEventId=id;
const details=e.id==='summit'?`The Sankofa Summit 2026 is HACSA's flagship gathering in Accra, Ghana, bringing together culture, heritage, innovation and global connection. The official summit experience includes conference programming, a Charity Gala, Sankofa Fest, Heritage Tours and a Heritage Brunch. Use the official summit website for confirmed registration, programme, speakers, travel information and updates.`:e.id==='hackathon'?`The HACSA Tech4Girls Hackathon takes place on 18 September 2026 at the HACSA Campus. It is an innovation-focused experience where young women can build, collaborate, solve problems and demonstrate technology skills. Confirm the final programme and participation instructions through HACSA's official channels.`:`Tech4Girls Cohort 5 Graduation takes place on 29 September 2026 at the HACSA Campus. The event celebrates the cohort's learning, projects, growth and achievements. Confirm the final ceremony schedule and participant information through HACSA's official channels.`;
state.view='event-'+id;
header(e.title);
content.innerHTML=`<div class="event-detail-page"><button class="btn ghost" data-action="go('dashboard')">← Back to homepage</button><div class="event-image ${e.id}"></div><div class="page-intro"><span class="tag">${e.kind}</span><h2>${e.title}</h2><p><b>${e.date}</b> · ${e.venue}</p><p>${details}</p></div><div class="grid"><div class="card"><h3>Event information</h3><p class="muted">Explore the official event information, programme announcements and visitor guidance.</p><a class="btn" href="${e.officialUrl||'https://summit.thehacsa.org/'}" target="_blank" rel="noopener">Official event website ↗</a></div><div class="card"><h3>Event registration</h3><p class="muted">Your registration is saved to your HACSA Axis account.</p>${button('Register for event','register()')}<div id="registrationStatus"></div></div></div>${e.id==='summit'?'<div class="card"><h3>Summit experiences</h3><div class="list"><div class="notice">Conference</div><div class="notice">Charity Gala</div><div class="notice">Sankofa Fest</div><div class="notice">Heritage Tours</div><div class="notice">Heritage Brunch</div></div></div>':''}</div>`;
loadEventRegistration(id);
}
function registrationEventId(id){return id==='summit'?'summit-2026':id}
async function loadEventRegistration(id){try{const registration=await api(`/registrations/mine/${registrationEventId(id)}`);const button=content.querySelector('[data-action="register()"]');const status=$('#registrationStatus');if(registration.registered&&button){button.textContent='Registered';button.disabled=true;if(status)status.innerHTML=`<p class="muted">Registration confirmed for ${registration.event_name}.</p>`}}catch(error){}}
async function register(){const event=upcomingEvents.find(item=>item.id===state.activeEventId);if(!event)return toast('Open an event before registering.');try{const registration=await api('/registrations',{method:'POST',body:JSON.stringify({event_id:registrationEventId(event.id)})});toast(`Registration confirmed for ${registration.event_name}.`);eventDetails(event.id)}catch(error){toast(error.message||'Event registration failed.')}}
function sessionHtml(s){return `<div class="session"><div class="time">${s.date}<br>${s.time}</div><div style="flex:1"><h4>${s.title}</h4><p>${s.venue} · ${s.type}</p></div><div>${button(state.saved.includes(s.id)?'Saved':'Save',`save(${s.id})`,'btn ghost')}</div></div>`}
function schedule(){content.innerHTML=`<div class="page-intro"><h2>Complete schedule</h2><p>Browse the summit programme, explore venues and save sessions to your personal agenda. Dates and sessions are demo content and can be connected to official programme data later.</p></div><div class="filters"><select id="dayFilter"><option value="all">All dates</option>${[...new Set(sessions.map(s=>s.date))].map(d=>`<option>${d}</option>`).join('')}</select><select id="typeFilter"><option value="all">All session types</option>${[...new Set(sessions.map(s=>s.type))].map(d=>`<option>${d}</option>`).join('')}</select></div><div class="schedule-list" id="scheduleList">${sessions.map(scheduleCard).join('')}</div>`;$('#dayFilter').onchange=filterSchedule;$('#typeFilter').onchange=filterSchedule}
async function networking(){
  const currentAvailability = typeof state.isOpenToConnect === 'boolean' ? state.isOpenToConnect : true;
  content.innerHTML = `<div class="networking-hero"><div><span class="tag">HACSA AXIS NETWORK</span><h2>Find the people who move ideas forward.</h2><p>Discover participants, mentors, founders and culture-makers who share your interests. Start with a thoughtful connection and build beyond the summit.</p></div><div class="networking-orbit" aria-hidden="true"><span>◎</span></div></div><div class="card" style="margin:18px 0 16px;padding:18px 20px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;"><div><strong style="display:block;color:var(--green)">Your networking status</strong><span class="muted">${currentAvailability ? 'Open to connect' : 'Not open to connect'}</span></div><button class="btn ${currentAvailability ? 'ghost' : ''}" data-action="toggleNetworkAvailability()">${currentAvailability ? 'Set unavailable' : 'Set available'}</button></div><div class="networking-toolbar"><div><span class="eyebrow">DISCOVER PEOPLE</span><h3>Make your next meaningful connection</h3></div><input id="networkSearch" type="search" placeholder="Search by name, role or interest" aria-label="Search networking profiles"></div><div id="networkProfiles" class="networking-grid"><div class="networking-loading">Loading your network...</div></div>`;
  const profiles = await loadNetworkingProfiles();
  renderNetworkingProfiles(profiles);
  $('#networkSearch').oninput = event => renderNetworkingProfiles(profiles, event.target.value);
}
function localNetworkingProfiles(){const store=readAuthStore();const users=(store.registrations||[]).map((entry,index)=>{const name=entry.name||entry.full_name||entry.email||`User ${index+1}`;const role=entry.role||'Participant';return {id:String(entry.id||`local-${index}`),name,role,organisation:entry.organization||'HACSA Axis',location:entry.location||'Accra, Ghana',interests:Array.isArray(entry.interests)&&entry.interests.length?entry.interests:[role,'Community building'],initials:(name.split(' ').map(part=>part[0]).join('').slice(0,2)||'HA').toUpperCase(),connectionStatus:'none',is_open_to_connect:entry.is_open_to_connect !== false};});if(state.name && !users.some(user=>user.name===state.name)){users.push({id:String(state.personId||state.email||`current-${Date.now()}`),name:state.name,role:state.category||roleLabels[state.role]||'Participant',organisation:'HACSA Axis',location:'Accra, Ghana',interests:['Community','Networking'],initials:nameInitials(state.name),connectionStatus:'none',is_open_to_connect:state.isOpenToConnect !== false});}return users.length?users:networkingFallback}
async function loadNetworkingProfiles(){const fallbackProfiles=localNetworkingProfiles();try{const response=await fetch('/network/directory',{headers:{Accept:'application/json',...(typeof getToken==='function'&&getToken()?{Authorization:'Bearer '+getToken()}:{})}});if(!response.ok)throw new Error('Networking API unavailable');const profiles=await response.json();const normalized=Array.isArray(profiles)&&profiles.length?profiles.map(profile=>({id:String(profile.id),name:profile.full_name||profile.name,role:profile.role,organisation:profile.email||'',location:'HACSA Axis',interests:[profile.role],initials:(profile.full_name||'?').split(' ').map(part=>part[0]).join('').slice(0,2),connectionStatus:profile.connectionStatus||'none',is_open_to_connect:profile.is_open_to_connect !== false})):fallbackProfiles;const merged=[...fallbackProfiles,...normalized].filter((profile,index,array)=>array.findIndex(item=>item.id===profile.id||item.name===profile.name)===index);merged.forEach(profile=>{networkingStatuses[profile.id]=profile.connectionStatus||'none'});return merged.length?merged:networkingFallback}catch(error){fallbackProfiles.forEach(profile=>{networkingStatuses[profile.id]=profile.connectionStatus||'none'});return fallbackProfiles.length?fallbackProfiles:networkingFallback}}
function renderNetworkingProfiles(profiles,query=''){const normalizedQuery=query.trim().toLowerCase();const matches=profiles.filter(profile=>!normalizedQuery||[profile.name,profile.role,profile.organisation,profile.location,...(profile.interests||[])].join(' ').toLowerCase().includes(normalizedQuery));$('#networkProfiles').innerHTML=matches.length?matches.map(networkProfileCard).join(''):'<div class="networking-empty">No people match that search yet.</div>'}
function networkProfileCard(profile){const status=networkingStatuses[profile.id]||profile.connectionStatus||'none';const availability = profile.is_open_to_connect !== false ? 'Open to connect' : 'Not open to connect';const connectDisabled = profile.is_open_to_connect === false || status === 'pending';const action = status==='accepted'?`<button class="btn network-connect" data-action="openMessageComposer('${profile.id}','${profile.name.replace(/'/g,"\\'")}')">Message ${profile.name.split(' ')[0]}</button>`:status==='pending'?'<span class="network-action network-action-pending">Request pending</span>':status==='denied'?`<button class="btn ghost network-connect" data-action="connectWithProfile('${profile.id}','${profile.name.replace(/'/g,"\\'")}')">Request again</button>`:connectDisabled?'<span class="network-action network-action-pending">Not open to connect</span>':`<button class="btn network-connect" data-action="connectWithProfile('${profile.id}','${profile.name.replace(/'/g,"\\'")}')">Connect</button>`;return `<article class="network-profile"><div class="network-profile-top"><div class="network-avatar">${profile.initials||profile.name.split(' ').map(part=>part[0]).join('').slice(0,2)}</div><span class="network-status network-status-${status}">${availability}</span></div><h3>${profile.name}</h3><p class="network-role">${profile.role}</p><p class="muted">${profile.organisation} · ${profile.location}</p><div class="network-interests">${(profile.interests||[]).map(interest=>`<span>${interest}</span>`).join('')}</div>${action}</article>`}
async function toggleNetworkAvailability(){
  const nextState = !(state.isOpenToConnect !== false);
  try {
    const response = await api('/me/network-availability', {
      method: 'PATCH',
      body: JSON.stringify({ open_to_connect: nextState })
    });
    state.isOpenToConnect = !!response.is_open_to_connect;
    const user = getUser();
    if (user) {
      user.is_open_to_connect = state.isOpenToConnect;
      setSession(getToken(), user);
    }
    toast(nextState ? 'You are now open to connect.' : 'You are now hidden from connection requests.');
    networking();
  } catch (error) {
    toast(error.message || 'Unable to update your networking availability.');
  }
}
async function connectWithProfile(profileId,profileName){networkingStatuses[profileId]='pending';toast(`Connection request to ${profileName} is pending.`);try{const response=await fetch('/network/connect/'+profileId,{method:'POST',headers:{'Content-Type':'application/json',...(typeof getToken==='function'&&getToken()?{Authorization:'Bearer '+getToken()}:{})}});if(!response.ok)throw new Error('Connection request failed');const result=await response.json().catch(()=>({}));networkingStatuses[profileId]=result.status||'pending';}catch(error){}}
function openMessageComposer(profileId,profileName){openModal(`<h2>Message ${profileName}</h2><p class="muted">This connection is accepted. Send a message to continue the conversation.</p><form id="networkMessageForm" class="form-grid"><div class="field full"><label for="networkMessage">Your message</label><textarea id="networkMessage" rows="5" required placeholder="Write a thoughtful introduction..."></textarea></div><div class="field full"><button class="btn">Send message</button></div></form>`);$('#networkMessageForm').onsubmit=async event=>{event.preventDefault();const message=$('#networkMessage').value.trim();try{const response=await fetch('/api/networking/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({recipientId:profileId,message})});if(!response.ok)throw new Error('Message could not be sent');toast(`Message sent to ${profileName}.`)}catch(error){toast(`Message to ${profileName} saved in demo mode.`)}closeModal()}}
function scheduleCard(s){return `<div class="card schedule-card" data-date="${s.date}" data-type="${s.type}"><div><span class="tag">${s.type}</span><h4>${s.title}</h4><p>${s.date} · ${s.time} · ${s.venue}</p></div><div class="actions">${button('Details',`details(${s.id})`,'btn ghost')}${button(state.saved.includes(s.id)?'Saved':'Save',`save(${s.id})`,'btn')}</div></div>`}
function filterSchedule(){const d=$('#dayFilter').value,t=$('#typeFilter').value;document.querySelectorAll('#scheduleList .schedule-card').forEach(c=>c.style.display=(d!=='all'&&c.dataset.date!==d)||(t!=='all'&&c.dataset.type!==t)?'none':'flex')}
async function badge(){const config=await api('/api/config').catch(()=>({}));const appOrigin=config.public_app_url||window.location.origin;const accessId=`HAX-${(state.personId||'').replaceAll('-','').slice(0,8).toUpperCase()}-26`;const verificationUrl=new URL(`/portal/badge.html?person_id=${encodeURIComponent(state.personId||'')}`,appOrigin).href;content.innerHTML=`<div class="page-intro"><h2>Your digital badge</h2><p>Scan the QR code to view this badge's registered name and access status.</p></div><div class="badge-card"><div class="badge-top"><span>HACSA AXIS · 2026</span><span>AXIS PASS</span></div><div class="badge-name">${state.name}</div><div class="badge-role">${state.category} · Accra, Ghana</div><div class="badge-bottom"><div><p style="font-size:11px;color:#d8e2d9">ACCESS ID</p><b style="font-size:13px">${accessId}</b><p style="font-size:11px;color:#d8e2d9;margin-top:20px">10–15 DECEMBER 2026</p></div><div class="qr" id="qr"></div></div></div><div style="margin-top:18px">${button('Download / print preview','printBadge()')}</div>`;new QRCode($('#qr'),{text:verificationUrl,width:95,height:95,colorDark:'#123a26',colorLight:'#ffffff'})}

function scanner(){content.innerHTML=`<div class="page-intro"><h2>Badge verification</h2><p>Scan a HACSA Axis QR code with your camera, or upload an image if the camera is unavailable. This demo validates locally without a backend.</p></div><div class="scanner-layout"><div class="card"><div id="qr-reader" class="qr-reader"></div><div class="scanner-actions"><button class="btn" id="startScan">Start camera</button><button class="btn secondary" id="stopScan">Stop camera</button></div><label class="upload-label">Upload QR image<input type="file" id="qrUpload" accept="image/*" /></label><p class="muted">Camera access requires HTTPS or localhost.</p></div><div class="card"><h3>Verification result</h3><div id="scanResult" class="scan-result neutral">Waiting for a QR code…</div><p class="muted">Valid demo badges begin with <b>HACSA-AXIS|</b> and include an email and user category.</p></div></div>`;let reader=null;const result=$('#scanResult');function verify(raw){if(!raw)return;const valid=raw.startsWith('HACSA-AXIS|');if(valid){const parts=raw.split('|');result.className='scan-result valid';result.innerHTML=`<strong>VALID BADGE</strong><br>Email: ${parts[1]||'Unknown'}<br>Category: ${parts[2]||'Unknown'}<br><small>Local demo verification only</small>`;}else{result.className='scan-result invalid';result.innerHTML='<strong>INVALID BADGE</strong><br>This QR code is not recognized by HACSA Axis.';}}$('#startScan').onclick=async()=>{if(!window.Html5Qrcode)return toast('Scanner library unavailable.');reader=new Html5Qrcode('qr-reader');try{await reader.start({facingMode:'environment'},{fps:10,qrbox:{width:220,height:220}},verify,()=>{});toast('Camera scanner started.');}catch(e){toast('Camera could not start. Try uploading an image.');}};$('#stopScan').onclick=async()=>{if(reader){try{await reader.stop();reader.clear();}catch(e){}toast('Scanner stopped.');}};$('#qrUpload').onchange=e=>{const file=e.target.files[0];if(!file)return;const img=new Image();const url=URL.createObjectURL(file);img.onload=()=>{const canvas=document.createElement('canvas');canvas.width=img.width;canvas.height=img.height;const ctx=canvas.getContext('2d');ctx.drawImage(img,0,0);const data=ctx.getImageData(0,0,canvas.width,canvas.height);const code=window.jsQR?jsQR(data.data,data.width,data.height):null;verify(code?code.data:null);if(!code){result.className='scan-result invalid';result.innerHTML='<strong>UNREADABLE QR</strong><br>Try a clearer image with the full code visible.';}URL.revokeObjectURL(url);};img.src=url;};}
async function engage(){content.innerHTML=`<div class="page-intro"><h2>Make your voice count</h2><p>Vote in live polls, submit feedback and send questions. Your responses are saved to the HACSA Axis programme.</p></div><div class="grid" id="engageGrid"><div class="card"><p class="muted">Loading live polls...</p></div></div>`;
try{
  const polls=await api('/engagement/polls');
  const live=Array.isArray(polls)&&polls[0]?polls[0]:null;
  const results=live?await api(`/engagement/polls/${live.id}/results`).catch(()=>null):null;
  const options=live&&live.options&&live.options.length?live.options.map(option=>option.option_text):['Education and skills','Heritage preservation','Women and girls in technology','Diaspora collaboration'];
  $('#engageGrid').innerHTML=`<div class="card"><span class="tag">LIVE POLL</span><h3>${live?live.question:'What should shape the next decade?'}</h3><p class="muted">Choose one priority for the next HACSA chapter.</p><div class="list">${options.map(x=>`<button class="choice" data-poll="${x.replace(/"/g,'&quot;')}">${x}</button>`).join('')}</div><div style="margin-top:15px">${button('Submit vote','poll()')}</div><p id="pollResult" class="muted">${results&&results.total_votes?results.results.map(item=>`${item.option_text}: ${item.vote_count}`).join(' · '):''}</p></div><div class="card"><span class="tag">FEEDBACK</span><h3>Tell us about your experience</h3><p class="muted">Your feedback helps organizers improve the summit experience.</p>${button('Open feedback form','feedback()')}</div><div class="card"><span class="tag">Q&A</span><h3>Ask a question</h3><p class="muted">Send a question for a session moderator.</p>${button('Submit a question','question()')}</div>`;
  document.querySelectorAll('[data-poll]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-poll]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.poll=b.dataset.poll});
}catch(error){
  $('#engageGrid').innerHTML=`<div class="card"><span class="tag">LIVE POLL</span><h3>What should shape the next decade?</h3><div class="list">${['Education and skills','Heritage preservation','Women and girls in technology','Diaspora collaboration'].map(x=>`<button class="choice" data-poll="${x}">${x}</button>`).join('')}</div><div style="margin-top:15px">${button('Submit vote','poll()')}</div><p id="pollResult" class="muted"></p></div>`;
  document.querySelectorAll('[data-poll]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-poll]').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');state.poll=b.dataset.poll});
}}
/* Operations administration is intentionally backend-only in this two-role frontend. */
function operations(){const store=JSON.parse(localStorage.getItem('hacsaAxisMockAuth')||'{"registrations":[],"audit":[]}');const pending=store.registrations.filter(item=>item.status==='Pending Admin Verification'||item.status==='Under Admin Review');content.innerHTML=`<div class="page-intro"><span class="tag">OPERATIONS WORKSPACE · MOCK SERVICE</span><h2>Registration verification</h2><p>Review applications before activation. This local demo models the approval boundary; production authorization must be enforced server-side.</p></div><div class="grid"><div class="card stat"><div><small>Pending applications</small><strong>${pending.length}</strong></div><span class="tag">Needs review</span></div><div class="card stat"><div><small>Active accounts</small><strong>${store.registrations.filter(item=>item.status==='Active').length}</strong></div><span class="tag">Verified</span></div><div class="card stat"><div><small>Audit events</small><strong>${store.audit.length}</strong></div><span class="tag">Tracked</span></div></div><div class="section-head"><h3>New registration requests</h3></div><div class="card verification-table"><div class="verification-row verification-head"><span>Applicant</span><span>Role</span><span>Status</span><span>Actions</span></div>${store.registrations.length?store.registrations.map(item=>`<div class="verification-row"><span><strong>${item.name}</strong><small>${item.email}</small></span><span>${item.role}</span><span><span class="status-pill">${item.status}</span></span><span class="verification-actions">${item.status==='Pending Admin Verification'?button('Approve',`approveRegistration('${item.id}')`,'btn')+button('Reject',`rejectRegistration('${item.id}')`,'btn ghost'):item.status==='Approved, Verification Required'?button('View code',`showVerificationCode('${item.id}')`,'btn ghost'):''}${button('Review',`reviewRegistration('${item.id}')`,'btn ghost')}</span></div>`).join(''):'<div class="empty">No registration requests yet. Submit one from the standalone sign-in page.</div>'}</div><div class="section-head"><h3>Verification history</h3></div><div class="card list">${store.audit.slice().reverse().map(event=>`<div class="notice"><b>${event.action}</b><br><span class="muted">${event.email||'system'} · ${new Date(event.at).toLocaleString()}</span></div>`).join('')||'<div class="empty">No audit events yet.</div>'}</div>`}
async function updateMockRegistration(id,action){const store=readAuthStore();const item=store.registrations.find(entry=>entry.id===id);if(!item)return;if(action==='approve'){const code=`AX-${crypto.randomUUID().replaceAll('-','').slice(0,12).toUpperCase()}`;item.status='Approved, Verification Required';item.verificationExpires=Date.now()+15*60*1000;item.verificationHash=await mockDigest(code);store.audit.push({action:'Registration approved; code issued',email:item.email,at:new Date().toISOString()});writeAuthStore(store);openModal(`<h2>Registration approved</h2><p class="muted">Controlled demo code for <b>${item.email}</b>. It is displayed once for this Operations session and is not stored in plaintext.</p><div class="notice"><strong>${code}</strong><br>Expires in 15 minutes.</div>`)}else if(action==='reject'){item.status='Rejected';item.rejectionReason='Application did not meet review requirements.';store.audit.push({action:'Registration rejected',email:item.email,at:new Date().toISOString()});writeAuthStore(store);toast('Registration rejected in demo mode.')}render()}
function approveRegistration(id){updateMockRegistration(id,'approve')};function rejectRegistration(id){updateMockRegistration(id,'reject')};function showVerificationCode(){openModal('<h2>Verification code</h2><p class="muted">For security, the mock service displays a code only once during approval. Request a new code through the controlled Operations flow.</p>')}function reviewRegistration(id){const store=readAuthStore();const item=store.registrations.find(entry=>entry.id===id);if(item)openModal(`<h2>Applicant review</h2><p><b>${item.name}</b><br>${item.email}<br>${item.role}</p><p class="muted">Status: ${item.status}<br>Submitted: ${new Date(item.createdAt).toLocaleString()}</p>`)}
function support(){content.innerHTML=`<div class="page-intro"><h2>Support & assistance</h2><p>Report an issue or request help from the event team. High-priority and medical reports trigger an operations alarm.</p></div><div class="card"><form id="supportForm" class="form-grid"><div class="field"><label for="supportCategory">Issue category</label><select id="supportCategory"><option>Access / badge</option><option>Registration</option><option>Venue navigation</option><option>Schedule</option><option>Accessibility</option><option>Safety concern</option><option>Medical emergency</option><option>Other</option></select></div><div class="field"><label for="supportLocation">Area at the event</label><select id="supportLocation" required><option value="">Select an area</option><option>Main Entrance</option><option>Exhibition Hall</option><option>VIP Lounge</option><option>Loading Bay</option><option>Main Auditorium</option><option>Innovation Lab</option><option>Heritage Hall</option><option>Other event area</option></select></div><div class="field"><label for="supportPriority">Priority</label><select id="supportPriority"><option value="low">Standard</option><option value="high">High priority</option><option value="critical">Medical emergency / immediate danger</option></select></div><div class="field full"><label for="supportDescription">Describe your request</label><textarea id="supportDescription" required rows="5" placeholder="Tell us what you need..."></textarea></div><div class="field full"><button class="btn">Submit request</button></div></form></div>`;$('#supportForm').onsubmit=async e=>{e.preventDefault();const submit=e.currentTarget.querySelector('button[type="submit"],button:not([type])');submit.disabled=true;try{const id=await eventId();const category=$('#supportCategory').value;const severity=category==='Medical emergency'?'critical':$('#supportPriority').value;await api('/api/v1/incidents/',{method:'POST',body:JSON.stringify({event_id:id,title:category,location:$('#supportLocation').value,description:$('#supportDescription').value.trim(),severity})});toast(severity==='high'||severity==='critical'?'Urgent report sent. Operations has been alerted.':'Your request was sent to the event team.');e.currentTarget.reset()}catch(error){toast(error.message||'Your request could not be sent.')}finally{submit.disabled=false}}}
function donate(){content.innerHTML=`<div class="donation donation-hero"><div><span class="tag">GIVE WITH PURPOSE</span><h2>Turn one generous moment into lasting opportunity.</h2><p>Help HACSA protect heritage, expand Tech4Girls, and create more spaces where young people and communities can learn, lead and connect across Africa and the diaspora.</p><a class="btn" href="https://www.thehacsa.org/donate/" target="_blank" rel="noopener">Donate on the HACSA website ↗</a></div><div class="donation-hero-mark">✦</div></div><div class="section-head"><h3>Your support keeps the work moving</h3></div><div class="grid"><div class="card"><h4>Preserve heritage</h4><p class="muted">Help celebrate, document and promote African history, identity and culture.</p></div><div class="card"><h4>Expand education</h4><p class="muted">Support learning, skills training and initiatives such as Tech4Girls.</p></div><div class="card"><h4>Empower communities</h4><p class="muted">Create room for collaboration, leadership, innovation and social impact.</p></div></div>`}
function login(){openModal(`<h2>Enter HACSA Axis</h2><p class="muted">Use any email for this frontend demo. Speaker email can represent a speaker login.</p><form id="loginForm" class="form-grid"><div class="field full"><label>Email</label><input id="loginEmail" type="email" required value="${state.email}" /></div><div class="field"><label>Password</label><input type="password" value="demo123" required /></div><div class="field"><label>Role</label><select id="loginRole"><option>General attendee</option><option>Speaker</option><option>Speaker</option></select></div><div class="field full"><button class="btn">Continue</button></div></form>`);$('#loginForm').onsubmit=e=>{e.preventDefault();state.email=$('#loginEmail').value;state.role=$('#loginRole').value;state.category=state.role;closeModal();toast('Demo login successful.');render()}}
function details(id){const s=sessions.find(x=>x.id===id);openModal(`<h2>${s.title}</h2><span class="tag">${s.type}</span><p class="muted">${s.date} · ${s.time}</p><p><b>Venue:</b> ${s.venue}</p><p class="muted">Session details, speaker assignments and live participation controls can be connected to the official programme and backend services later.</p>${button('Save session',`save(${s.id})`)}`)}
function feedback(){openModal(`<h2>Session feedback</h2><form id="feedbackForm" class="form-grid"><div class="field full"><label>Session</label><select><option>Opening Ceremony & Welcome</option><option>Women and Girls in Technology</option><option>Sankofa Dialogue</option></select></div><div class="field"><label>Rating</label><select id="feedbackRating"><option>5 — Excellent</option><option>4 — Good</option><option>3 — Fair</option><option>2 — Needs improvement</option><option>1 — Poor</option></select></div><div class="field"><label>Would you recommend it?</label><select><option>Yes</option><option>No</option></select></div><div class="field full"><label>Comments</label><textarea id="feedbackComment" rows="4"></textarea></div><div class="field full"><button class="btn">Submit feedback</button></div></form>`);$('#feedbackForm').onsubmit=async e=>{e.preventDefault();try{const first=sessions[0];if(first)await api(`/engagement/sessions/${first.id}/feedback`,{method:'POST',body:JSON.stringify({rating:parseInt($('#feedbackRating').value,10),comment:$('#feedbackComment').value.trim()||null})});}catch(error){}closeModal();toast('Feedback submitted in demo mode.')}}
function question(){openModal(`<h2>Ask a question</h2><form id="questionForm"><div class="field"><label>Your question</label><textarea id="questionText" rows="5" required placeholder="Write your question..."></textarea></div><br><button class="btn">Send question</button></form>`);$('#questionForm').onsubmit=async e=>{e.preventDefault();try{const first=sessions[0];if(first)await api(`/engagement/sessions/${first.id}/questions`,{method:'POST',body:JSON.stringify({question_text:$('#questionText').value.trim()})});}catch(error){}closeModal();toast('Question added to the demo queue.')}}
async function poll(){if(!state.poll)return toast('Select an option first.');try{const polls=await api('/engagement/polls');const live=Array.isArray(polls)?polls[0]:null;const option=live&&(live.options||[]).find(item=>item.option_text===state.poll);if(live&&option)await api(`/engagement/polls/${live.id}/vote/${option.id}`,{method:'POST'});const results=live?await api(`/engagement/polls/${live.id}/results`):null;if(results){$('#pollResult').textContent=results.results.map(item=>`${item.option_text}: ${item.vote_count}`).join(' · ');toast('Your vote was saved.');return}}catch(error){}$('#pollResult').textContent=`Vote recorded: ${state.poll}`;toast('Your poll response was recorded.')}
function save(id){if(state.saved.includes(id))state.saved=state.saved.filter(x=>x!==id);else state.saved.push(id);toast(state.saved.includes(id)?'Session saved.':'Session removed.');if(typeof api==='function'){api(`/schedule/sessions/${id}/interest`,{method:'POST'}).catch(()=>{})}render()}

function assistant(){content.innerHTML=`<div class="page-intro"><h2>Axis AI Assistant</h2><p>Ask for help navigating HACSA Axis. This offline demo answers common event questions without sending data to a server.</p></div><div class="card"><div class="field"><label>Your question</label><input id="aiQuestion" placeholder="e.g. When is the Sankofa Summit?"></div><div style="margin-top:12px">${button('Ask Axis','askAxis()')}</div><div id="aiAnswer" class="notice" style="margin-top:16px">Your answer will appear here.</div></div>`}
function askAxis(){const q=$('#aiQuestion').value.toLowerCase();let a='I can help with the HACSA Axis homepage, events, schedules, registration, badges, accessibility and support.';if(q.includes('summit'))a='The Sankofa Summit 2026 runs 10–15 December 2026 in Accra, Ghana. Experiences include the Conference, Charity Gala, Sankofa Fest, Heritage Tours and Heritage Brunch.';else if(q.includes('hackathon'))a='The HACSA Tech4Girls Hackathon is listed for 18 September 2026 at the HACSA Campus.';else if(q.includes('graduation'))a='Tech4Girls Cohort 5 Graduation is listed for 29 September 2026 at the HACSA Campus.';else if(q.includes('speaker'))a='Speakers can use the Speaker workspace to view assigned sessions, venues and reminder previews.';else if(q.includes('badge')||q.includes('qr'))a='Open Digital Badge to view your demo QR code, or Scan Badge to verify a code locally.';$('#aiAnswer').textContent=a}
function accessibility(){content.innerHTML=`<div class="page-intro"><h2>Accessibility tools</h2><p>Adjust the reading experience or listen to selected website content using browser-supported speech.</p></div><div class="card"><div class="actions">${button('Increase text','changeText(1)')} ${button('Decrease text','changeText(-1)','btn ghost')} ${button('High contrast','toggleContrast()','btn ghost')}</div><div class="field" style="margin-top:18px"><label>Text to read aloud</label><textarea id="speechText" rows="4">Welcome to HACSA Axis. Discover culture, heritage, innovation and events connecting Ghana and the diaspora.</textarea></div><div style="margin-top:12px">${button('Read aloud','speakText()')} ${button('Stop speech','stopSpeech()','btn ghost')}</div></div>`}
function changeText(n){const root=document.documentElement;const current=parseFloat(getComputedStyle(root).getPropertyValue('--a11y-scale')||'1');root.style.setProperty('--a11y-scale',Math.max(.85,Math.min(1.3,current+n*.08)));document.body.style.fontSize=(Math.max(.85,Math.min(1.3,current+n*.08))*100)+'%'}
function toggleContrast(){document.body.classList.toggle('high-contrast')}
function speakText(){if('speechSynthesis' in window){window.speechSynthesis.cancel();window.speechSynthesis.speak(new SpeechSynthesisUtterance($('#speechText').value))}else toast('Speech is not supported by this browser.')}
function stopSpeech(){if('speechSynthesis' in window)window.speechSynthesis.cancel()}
function speaker(){content.innerHTML=`<div class="speaker-hero"><div><span class="tag">SPEAKER STUDIO · PRIVATE WORKSPACE</span><h2>Own the room before you enter it.</h2><p>Track every appearance, prepare with confidence and stay aligned with the HACSA Axis programme team.</p><div class="hero-meta"><span>${speakerAssignments.length} scheduled appearances</span><span>Accra · December 2026</span></div></div><div class="speaker-hero-mark">✦</div></div><div class="speaker-stats"><div class="speaker-stat"><span>Scheduled events</span><strong>${speakerAssignments.length}</strong><small>Across the summit programme</small></div><div class="speaker-stat"><span>Confirmed</span><strong>${speakerAssignments.filter(x=>x.status==='Confirmed').length}</strong><small>Ready for production planning</small></div><div class="speaker-stat"><span>Preparation</span><strong>Live</strong><small>Use each session card to review next steps</small></div></div><div class="section-head"><h3>Your scheduled appearances</h3><button data-action="go('schedule')">View full schedule →</button></div><div class="speaker-session-grid">${speakerAssignments.map(item=>speakerSessionCard(item)).join('')}</div><div class="speaker-bottom-grid"><div class="card"><span class="tag">SPEAKER CHECKLIST</span><h3>Before you take the floor</h3><div class="checklist"><label><input type="checkbox"> Confirm arrival and technical check-in</label><label><input type="checkbox"> Review your session objectives</label><label><input type="checkbox"> Prepare slides, notes or workshop materials</label><label><input type="checkbox"> Confirm accessibility and stage requirements</label></div></div><div class="card"><span class="tag">REMINDER PREVIEW</span><h3>Your next programme touchpoint</h3><p class="muted">Reminder messages are simulated locally. A future backend can send verified, event-specific notices.</p>${button('Preview speaker reminder','notify()')}</div></div>`}
function speakerSessionCard(s){return `<article class="speaker-session-card"><div class="speaker-session-top"><span class="tag">${s.type}</span><span class="status-pill ${s.status.toLowerCase()}">${s.status}</span></div><p class="speaker-date">${s.date} · ${s.time}</p><h3>${s.title}</h3><p class="muted">${s.venue} · ${s.event}</p><div class="speaker-session-footer"><span>${s.prep}</span><button class="btn ghost" data-action="speakerDetails('${s.id}')">Open details</button></div></article>`}
function speakerDetails(id){const s=speakerAssignments.find(x=>x.id===id);if(!s)return;openModal(`<span class="tag">${s.type}</span><h2>${s.title}</h2><p class="muted"><b>Event:</b> ${s.event}</p><div class="notice"><strong>Event details</strong><br><b>Date:</b> ${s.date}<br><b>Time:</b> ${s.time}<br><b>Venue:</b> ${s.venue}<br><b>Status:</b> ${s.status}</div><h3>Preparation notes</h3><p>${s.prep}</p><button class="btn" data-action="go('schedule')">Open full schedule</button>`)}

function enterApp(role,requestedView){state.role=role;state.category=roleLabels[role];state.authenticated=true;state.isOpenToConnect = getUser()?.is_open_to_connect !== false;state.view=requestedView|| (role==='speaker'?'speaker':'dashboard');const authScreen=document.getElementById('authScreen');if(authScreen)authScreen.classList.add('hidden');const appShell=document.querySelector('.app-shell');if(appShell)appShell.classList.remove('auth-locked');updateProfileInitials();render();loadNotifications();}
const demoAccessCodes={'AXIS-PART-2026':'participant','AXIS-SPEAK-2026':'speaker'};
function setAuthMode(mode){const signup=mode==='signup';document.querySelectorAll('[data-auth-mode]').forEach(b=>b.classList.toggle('active',b.dataset.authMode===mode));const authTitle=document.getElementById('authTitle');const authIntro=document.getElementById('authIntro');const authSubmit=document.getElementById('authSubmit');if(authTitle)authTitle.textContent=signup?'Create your event space':'Sign in to your event space';if(authIntro)authIntro.textContent=signup?'Select your role and submit an application. Operations must approve it before access is granted.':'Use your approved email and password to access HACSA Axis.';if(authSubmit)authSubmit.textContent=signup?'Submit for admin review':'Sign in securely';const authName=document.getElementById('authName');const authRole=document.getElementById('authRole');const authConfirmPassword=document.getElementById('authConfirmPassword');const authCode=document.getElementById('authCode');const authPassword=document.getElementById('authPassword');const authRememberField=document.getElementById('authRememberField');const authForgot=document.getElementById('authForgot');const authNameField=document.querySelector('.auth-name-field');const authRoleField=document.querySelector('.auth-role-field');const authConfirmPasswordField=document.querySelector('.auth-confirm-password-field');const authCodeField=document.querySelector('.auth-code-field');const authPasswordField=document.querySelector('.auth-password-field');if(authNameField)authNameField.classList.toggle('hidden',!signup);if(authRoleField)authRoleField.classList.toggle('hidden',!signup);if(authConfirmPasswordField)authConfirmPasswordField.classList.toggle('hidden',!signup);if(authCodeField)authCodeField.classList.add('hidden');if(authPasswordField)authPasswordField.classList.remove('hidden');if(authRememberField)authRememberField.classList.toggle('hidden',signup);if(authForgot)authForgot.classList.toggle('hidden',signup);if(authName)authName.required=signup;if(authRole)authRole.required=signup;if(authConfirmPassword)authConfirmPassword.required=signup;if(authCode)authCode.required=false;if(authPassword)authPassword.required=true;const authError=document.getElementById('authError');if(authError)authError.textContent=''}
async function authenticate(e){e.preventDefault();const emailField=document.getElementById('authEmail');const passwordField=document.getElementById('authPassword');const authError=document.getElementById('authError');if(!emailField||!passwordField||!authError)return;const email=emailField.value.trim().toLowerCase();const store=readAuthStore();const authName=document.getElementById('authName');if(authName&&authName.required){if(!authName.value.trim()||!document.getElementById('authRole').value||!passwordField.value||passwordField.value!==document.getElementById('authConfirmPassword').value){authError.textContent='Complete all fields and make sure the passwords match.';return}if(passwordField.value.length<8){authError.textContent='Password must contain at least 8 characters.';return}if(store.registrations.some(item=>item.email===email)){ authError.textContent='This email already has a registration request.';return}store.registrations.push({id:crypto.randomUUID(),name:authName.value.trim(),email,role:document.getElementById('authRole').value,passwordHash:await mockDigest(passwordField.value),status:'Pending Admin Verification',createdAt:new Date().toISOString()});store.audit.push({action:'Registration submitted',email,at:new Date().toISOString()});writeAuthStore(store);authError.textContent='Your registration has been submitted successfully. An administrator will review your application before activation.';return}if(!email||!passwordField.value){authError.textContent='Enter an email and password to continue.';return}const item=store.registrations.find(entry=>entry.email===email);state.name=item?.name||email.split('@')[0];state.email=email;const role=item?.role?.toLowerCase()||'participant';enterApp(role)}
function signOut(){clearSession();window.location.href='/index.html';}
function applyRouteFromQuery(){const current=typeof getUser==='function'?getUser():null;if(typeof getToken==='function'&&(!getToken()||!current)){window.location.href='/index.html';return}if(current){state.name=current.full_name;state.email=current.email;state.personId=current.person_id;state.isOpenToConnect = current.is_open_to_connect !== false;}const params=new URLSearchParams(window.location.search);const role=params.get('role')||params.get('workspace')||current?.role;const requestedView=params.get('view');const validViews=['dashboard','schedule','badge','networking','scanner','engage','support','donate','speaker'];if(role&&roleLabels[role]){state.email=params.get('email')||state.email;const view=validViews.includes(requestedView)?requestedView:role==='speaker'?'speaker':'dashboard';enterApp(role,view);return}window.location.href='/index.html';}
function printBadge(){window.print()};function go(v){if(state.scanner){try{state.scanner.stop()}catch(e){}}state.view=v;render()};

function formatNotificationTime(value){
  if (!value) return 'Just now';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Just now';
  return date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

async function loadNotifications(){
  try {
    const notifications = await api('/notifications');
    state.notifications = Array.isArray(notifications) ? notifications : [];
    const bell = document.getElementById('notifyBtn');
    if (!bell) return;
    const unreadCount = state.notifications.filter(item => !item.is_read).length;
    const dot = bell.querySelector('.dot');
    if (dot) {
      dot.style.display = unreadCount > 0 ? 'block' : 'none';
    }
  } catch (error) {
    state.notifications = [];
    const bell = document.getElementById('notifyBtn');
    if (bell) {
      const dot = bell.querySelector('.dot');
      if (dot) dot.style.display = 'none';
    }
  }
}

async function listPendingConnections(){
  try {
    const pending = await api('/network/connections?status=pending');
    const directory = await api('/network/directory').catch(() => []);
    const userMap = new Map((Array.isArray(directory) ? directory : []).map(user => [String(user.id), user.full_name || user.name || 'HACSA member']));
    return Array.isArray(pending) ? pending.map(item => ({
      ...item,
      requester_name: userMap.get(String(item.requester_id)) || 'Someone'
    })) : [];
  } catch (error) {
    return [];
  }
}

async function respondConnection(connectionId, accept){
  try {
    const result = await api(`/network/connections/${connectionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ accept })
    });
    const action = accept ? 'accepted' : 'declined';
    toast(`Connection request ${action}.`);
    if (state.view === 'networking') {
      const profiles = await loadNetworkingProfiles();
      renderNetworkingProfiles(profiles, $('#networkSearch')?.value || '');
    }
    if (typeof notify === 'function') {
      await notify();
    }
    return result;
  } catch (error) {
    toast(error.message || 'Could not update this connection.');
    return null;
  }
}

async function notify(){
  const loading = '<h2>Recent activity</h2><div class="list"><div class="notice">Loading your latest event activity…</div></div>';
  openModal(loading);

  try {
    await loadNotifications();
    const pendingConnections = await listPendingConnections();
    const items = [...state.notifications, ...pendingConnections.map(item => ({
      id: `connect-${item.id}`,
      title: 'New connection request',
      message: `${item.requester_name} wants to connect with you.`,
      created_at: item.created_at,
      is_read: false,
      action: 'connection',
      connection_id: item.id,
      requester_name: item.requester_name
    }))].map(item => item.action === 'connection'
      ? `
          <div class="notice">
            <b>${item.title}</b><br>
            <small>${formatNotificationTime(item.created_at)}</small><br>
            ${item.message}<br>
            <div style="display:flex; gap:8px; margin-top:10px; flex-wrap:wrap;">
              ${button('Accept', `respondConnection(${item.connection_id}, true)`, 'btn')}
              ${button('Decline', `respondConnection(${item.connection_id}, false)`, 'btn ghost')}
            </div>
          </div>
        `
      : `
          <div class="notice">
            <b>${item.title}</b><br>
            <small>${formatNotificationTime(item.created_at)}</small><br>
            ${item.message}
          </div>
        `).join('');

    openModal(`<h2>Recent activity</h2><div class="list">${items || '<div class="notice"><b>No recent activity.</b><br>Your event activity will appear here once you register or interact with the summit.</div>'}</div>`);
  } catch (error) {
    openModal('<h2>Recent activity</h2><div class="list"><div class="notice"><b>No recent activity.</b><br>There are no live notifications available right now.</div></div>');
  }
}
const appShell=document.querySelector('.app-shell');if(appShell)appShell.classList.add('auth-locked');const authModeButtons=document.querySelectorAll('[data-auth-mode]');if(authModeButtons.length){authModeButtons.forEach(b=>b.onclick=()=>setAuthMode(b.dataset.authMode));const authForm=document.getElementById('authForm');if(authForm)authForm.onsubmit=authenticate;const authForgot=document.getElementById('authForgot');if(authForgot)authForgot.onclick=()=>{const authError=document.getElementById('authError');if(authError)authError.textContent='Password reset requests will be handled by Operations support in the production service.'};}
const nav=document.getElementById('nav');if(nav){nav.addEventListener('click',e=>{const b=e.target.closest('[data-view]');if(b){state.view=b.dataset.view;render();const sidebar=document.getElementById('sidebar');if(sidebar)sidebar.classList.remove('open')}})};const menu=document.getElementById('menu');if(menu){menu.onclick=()=>{const sidebar=document.getElementById('sidebar');if(sidebar)sidebar.classList.toggle('open')}};const modalClose=document.getElementById('modalClose');if(modalClose)modalClose.onclick=closeModal;const modal=document.getElementById('modal');if(modal)modal.onclick=e=>{if(e.target.id==='modal')closeModal()};const notifyBtn=document.getElementById('notifyBtn');if(notifyBtn)notifyBtn.onclick=notify;const profileBtn=document.getElementById('profileBtn');if(profileBtn)profileBtn.onclick=()=>window.location.href='/index.html';document.addEventListener('click',e=>{const b=e.target.closest('[data-action]');if(b){const action=b.dataset.action;try{new Function(action)()}catch(err){console.error(err)}}});document.addEventListener('click',e=>{const b=e.target.closest('#nav [data-view="donate"]');if(b){e.preventDefault();e.stopImmediatePropagation();window.open('https://www.thehacsa.org/donate/','_blank','noopener')}},true);render();applyRouteFromQuery();
(async function hydrateFromBackend(){
  try{
    const [live,venues,speakers]=await Promise.all([api('/schedule/sessions'),api('/venues').catch(()=>[]),api('/speakers').catch(()=>[])]);
    const venueName=Object.fromEntries((venues||[]).map(venue=>[venue.id,venue.name]));
    if(Array.isArray(live)&&live.length){
      live.forEach((item,index)=>{
        const start=new Date(item.start_time);
        sessions[index]={
          id:item.id,
          date:start.toLocaleDateString(undefined,{weekday:'short',day:'numeric',month:'short'}),
          time:start.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),
          title:item.title,
          venue:venueName[item.venue_id]||(item.venue_id?('Venue '+item.venue_id):'HACSA Campus'),
          type:item.status||'Session'
        };
      });
    }
    if(Array.isArray(speakers)&&speakers.length){
      featuredSpeakers=speakers.map((speaker,index)=>({
        name:speaker.full_name||speaker.title||'Speaker',
        title:speaker.title||speaker.expertise||'Featured speaker',
        organization:speaker.organization||'HACSA Axis',
        photo_url:speakerPhoto(index,speaker.photo_url,speaker.full_name||speaker.title)
      }));
    }
    try{
      const me=await api('/speakers/me');
      const assigned=await api(`/speakers/${me.speaker_code}/sessions`);
      if(Array.isArray(assigned)&&assigned.length){
        assigned.forEach((item,index)=>{
          const start=new Date(item.start_time);
          const end=new Date(item.end_time);
          speakerAssignments[index]={
            id:String(item.id),
            event:'HACSA Axis',
            date:start.toLocaleDateString(undefined,{weekday:'short',day:'numeric',month:'short',year:'numeric'}),
            time:`${start.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}–${end.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}`,
            title:item.title,
            venue:venueName[item.venue_id]||'HACSA Campus',
            type:item.status||'Session',
            status:'Confirmed',
            prep:'Review arrival time, technical check-in and session objectives.'
          };
        });
      }
    }catch(error){}
    if(state.authenticated)render();
  }catch(e){}
})();

