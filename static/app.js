const HOME_TIMEZONE = 'America/New_York';

function renderDateCard() {
    const now = new Date();

    document.getElementById('date-weekday').textContent =
    now.toLocaleDateString('en-US', { weekday: 'long', timeZone: HOME_TIMEZONE });
    document.getElementById('date-month-year').textContent =
    now.toLocaleDateString('en-US', { month: 'long', timeZone: HOME_TIMEZONE });
    document.getElementById('date-day').textContent =
    now.toLocaleDateString('en-US', { day: 'numeric', timeZone: HOME_TIMEZONE });
}

// Startup
renderDateCard();