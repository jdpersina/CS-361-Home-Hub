
const HUB_TIMEZONE = 'America/New_York';

function renderDateCard() {
    const now = new Date();

    document.getElementById('date-month-year').textContent =
    now.toLocaleDateString('en-US', { month: 'long', year:'numeric', timeZone: HUB_TIMEZONE }).toUpperCase();
    document.getElementById('date-weekday').textContent =
    now.toLocaleDateString('en-US', { weekday: 'long', timeZone: HUB_TIMEZONE });
    document.getElementById('date-day').textContent =
    now.toLocaleDateString('en-US', { day: 'numeric', timeZone: HUB_TIMEZONE });
}

// Events API
async function loadEvents() {
    const response = await fetch('/api/events');
    return await response.json();
}

// Rendering
function renderTodayList(events) {
  const todayStr = new Date().toLocaleDateString('en-CA', { timeZone: HUB_TIMEZONE }); 

  const todays = events.filter(e => e.start.startsWith(todayStr));

  document.getElementById('today-count').textContent = `${todays.length} ${todays.length === 1 ? 'event' : 'events'} today`;
  document.getElementById('today-events').replaceChildren();
  todays.forEach(e => {
    const li = document.createElement('li');
    li.textContent = `${e.start.slice(11, 16)} - ${e.title}`;
    document.getElementById('today-events').appendChild(li);
  });
}

function showView(name) {
    document.querySelectorAll('.view').forEach(v => v.hidden = true);
    document.getElementById(`view-${name}`).hidden = false;
  }

document.getElementById('btn-open-calendar').addEventListener('click', () => showView('calendar'));
document.getElementById('btn-back-home').addEventListener('click', () => showView('home'));

// Startup
renderDateCard();
loadEvents().then(renderTodayList);