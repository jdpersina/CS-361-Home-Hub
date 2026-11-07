const HUB_TIMEZONE = document.body.dataset.hubTimezone;
const MAX_CHIPS_PER_DAY = 2;

const state = {
  events: [],
  today: '',      // "YYYY-MM-DD" in HUB_TIMEZONE
  month: null,    // { year, month } with month 0-11
  selected: '',   // "YYYY-MM-DD"
};

// Dates
// Calendar dates are kept as "YYYY-MM-DD" strings and do their math on UTC
// Date objects, so daylight-saving changes never shift a day.
function todayInHub() {
  return new Date().toLocaleDateString('en-CA', { timeZone: HUB_TIMEZONE });
}

function parseDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function toISODate(date) {
  return date.toISOString().slice(0, 10);
}

function addDays(date, days) {
  return new Date(date.getTime() + days * 86400000);
}

function formatDate(iso, options) {
  return parseDate(iso).toLocaleDateString('en-US', { ...options, timeZone: 'UTC' });
}

function formatTime(date) {
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'UTC' });
}

function eventTimes(e) {
  const [datePart, timePart] = e.start.split('T');
  const [h, min] = timePart.split(':').map(Number);
  const start = parseDate(datePart);
  start.setUTCHours(h, min);
  const end = new Date(start.getTime() + e.durationMinutes * 60000);
  return { start, end };
}

function eventsOn(iso) {
  return state.events.filter(e => e.start.startsWith(iso));
}

function memberClass(e) {
  const first = e.participants?.[0];
  return first ? `member-${first.toLowerCase()}` : '';
}

// Events API
async function loadEvents() {
  const response = await fetch('/api/events');
  return await response.json();
}

// Home view
function renderDateCard() {
  document.getElementById('date-month-year').textContent =
    formatDate(state.today, { month: 'long', year: 'numeric' }).toUpperCase();
  document.getElementById('date-weekday').textContent =
    formatDate(state.today, { weekday: 'long' });
  document.getElementById('date-day').textContent =
    formatDate(state.today, { day: 'numeric' });
}

function renderTodayList() {
  const count = document.getElementById('today-count');
  const list = document.getElementById('today-events');
  list.replaceChildren();

  const todays = eventsOn(state.today);
  count.textContent = `${todays.length} ${todays.length === 1 ? 'event' : 'events'} today`;
  todays.forEach(e => {
    const li = document.createElement('li');
    li.textContent = `${formatTime(eventTimes(e).start)} - ${e.title}`;
    list.appendChild(li);
  });
}

// Calendar view
function renderCalendar() {
  document.getElementById('calendar-header-date').textContent =
    formatDate(state.today, { weekday: 'long', month: 'long', day: 'numeric' });
  renderMonthGrid();
  renderDayPanel();
}

function renderMonthGrid() {
  const { year, month } = state.month;
  const first = new Date(Date.UTC(year, month, 1));
  const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
  const weeks = Math.ceil((first.getUTCDay() + daysInMonth) / 7);
  const gridStart = addDays(first, -first.getUTCDay());

  document.getElementById('month-title').textContent =
    first.toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' });

  const cells = [];
  for (let i = 0; i < weeks * 7; i++) {
    const date = addDays(gridStart, i);
    const iso = toISODate(date);
    const dayEvents = eventsOn(iso);

    const cell = document.createElement('button');
    cell.type = 'button';
    cell.className = 'day-cell';
    cell.dataset.date = iso;
    cell.classList.toggle('outside-month', date.getUTCMonth() !== month);
    cell.classList.toggle('is-today', iso === state.today);
    cell.classList.toggle('is-selected', iso === state.selected);
    cell.setAttribute('aria-pressed', iso === state.selected);
    cell.setAttribute('aria-label',
      `${formatDate(iso, { weekday: 'long', month: 'long', day: 'numeric' })}, ` +
      `${dayEvents.length} ${dayEvents.length === 1 ? 'event' : 'events'}`);

    const number = document.createElement('span');
    number.className = 'day-number';
    number.textContent = date.getUTCDate();
    cell.appendChild(number);

    dayEvents.slice(0, MAX_CHIPS_PER_DAY).forEach(e => {
      const chip = document.createElement('span');
      chip.className = `event-chip ${memberClass(e)}`;
      chip.textContent = `${e.title} · ${e.participants.join(', ')}`;
      cell.appendChild(chip);
    });
    if (dayEvents.length > MAX_CHIPS_PER_DAY) {
      const more = document.createElement('span');
      more.className = 'more-events';
      more.textContent = `+${dayEvents.length - MAX_CHIPS_PER_DAY} more`;
      cell.appendChild(more);
    }

    cells.push(cell);
  }
  document.getElementById('month-grid').replaceChildren(...cells);
}

function renderDayPanel() {
  document.getElementById('selected-date').textContent =
    formatDate(state.selected, { weekday: 'long', month: 'long', day: 'numeric' });

  const list = document.getElementById('day-events');
  list.replaceChildren();

  const dayEvents = eventsOn(state.selected);
  if (dayEvents.length === 0) {
    list.appendChild(emptyItem('No events'));
    return;
  }

  dayEvents.forEach(e => {
    const { start, end } = eventTimes(e);
    const li = document.createElement('li');
    li.className = `day-event ${memberClass(e)}`;
    li.append(
      textSpan('day-event-time', `${formatTime(start)} – ${formatTime(end)}`),
      textSpan('day-event-title', e.title),
      textSpan('day-event-location', e.location),
      textSpan('day-event-participants', e.participants.join(', ')),
    );
    list.appendChild(li);
  });
}

function textSpan(className, text) {
  const span = document.createElement('span');
  span.className = className;
  span.textContent = text;
  return span;
}

function emptyItem(text) {
  const li = document.createElement('li');
  li.className = 'day-empty';
  li.textContent = text;
  return li;
}

function selectDate(iso) {
  const date = parseDate(iso);
  state.selected = iso;
  state.month = { year: date.getUTCFullYear(), month: date.getUTCMonth() };
  renderCalendar();
}

function shiftMonth(delta) {
  const { year, month } = state.month;
  const shifted = new Date(Date.UTC(year, month + delta, 1));
  state.month = { year: shifted.getUTCFullYear(), month: shifted.getUTCMonth() };
  renderMonthGrid();
}

// The calendar is a layer on top of the home view. Home stays rendered
// underneath so closing the calendar shows it instantly.
function openCalendar() {
  selectDate(state.today);
  document.getElementById('view-home').inert = true;
  document.getElementById('view-calendar').hidden = false;
}

function closeCalendar() {
  document.getElementById('view-calendar').hidden = true;
  document.getElementById('view-home').inert = false;
}

document.getElementById('btn-open-calendar').addEventListener('click', openCalendar);
document.getElementById('btn-back-home').addEventListener('click', closeCalendar);
document.getElementById('btn-today').addEventListener('click', () => selectDate(state.today));
document.getElementById('btn-prev-month').addEventListener('click', () => shiftMonth(-1));
document.getElementById('btn-next-month').addEventListener('click', () => shiftMonth(1));
document.getElementById('month-grid').addEventListener('click', event => {
  const cell = event.target.closest('.day-cell');
  if (cell) selectDate(cell.dataset.date);
});

// Startup
async function start() {
  state.today = todayInHub();
  state.selected = state.today;
  renderDateCard();

  state.events = await loadEvents();
  renderTodayList();
}

start();
