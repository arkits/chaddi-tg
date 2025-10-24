// Dashboard incremental data loader
document.addEventListener('DOMContentLoaded', () => {
  // Load data in parallel for faster loading
  Promise.all([
    loadMetrics(),
    loadActivity(),
    loadRandomQuote(),
    loadVersion(),
  ]).catch(error => {
    console.error('Error loading dashboard data:', error);
  });
});

// Load basic metrics
async function loadMetrics() {
  try {
    const response = await fetch('/api/dashboard/metrics');
    const data = await response.json();

    // Update counts with number formatting
    document.getElementById('bakchods-count').textContent = formatNumber(data.bakchods_count);
    document.getElementById('groups-count').textContent = formatNumber(data.groups_count);
    document.getElementById('messages-count').textContent = formatNumber(data.messages_count);
    document.getElementById('quotes-count').textContent = formatNumber(data.quotes_count);
    document.getElementById('roll-count').textContent = formatNumber(data.roll_count);
    document.getElementById('jobs-count').textContent = formatNumber(data.jobs_count);

    // Update recent activity indicators
    if (data.recent_bakchods > 0) {
      const recentBakchods = document.getElementById('recent-bakchods');
      recentBakchods.textContent = `+${formatNumber(data.recent_bakchods)} active (24h)`;
      recentBakchods.style.display = 'block';
    }

    if (data.recent_messages > 0) {
      const recentMessages = document.getElementById('recent-messages');
      recentMessages.textContent = `+${formatNumber(data.recent_messages)} (24h)`;
      recentMessages.style.display = 'block';
    }

    // Update 24h stats
    document.getElementById('active-users-24h').textContent = formatNumber(data.recent_bakchods);
    document.getElementById('messages-24h').textContent = formatNumber(data.recent_messages);
  } catch (error) {
    console.error('Error loading metrics:', error);
    showError('metrics');
  }
}

// Load activity data (most active users/groups)
async function loadActivity() {
  try {
    const response = await fetch('/api/dashboard/activity');
    const data = await response.json();

    // Most active user
    if (data.most_active_bakchod) {
      const userName = data.most_active_bakchod.pretty_name || data.most_active_bakchod.username || 'Unknown';
      document.getElementById('most-active-user').textContent = userName;
    } else {
      document.getElementById('most-active-user-item').style.display = 'none';
    }

    // Most active group
    if (data.most_active_group) {
      document.getElementById('most-active-group').textContent = data.most_active_group.name || 'Unknown';
    } else {
      document.getElementById('most-active-group-item').style.display = 'none';
    }

    // Latest message time
    if (data.latest_message_time) {
      const date = new Date(data.latest_message_time);
      const formatted = date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
      document.getElementById('latest-message').textContent = formatted;
    } else {
      document.getElementById('latest-message-item').style.display = 'none';
    }
  } catch (error) {
    console.error('Error loading activity:', error);
    showError('activity');
  }
}

// Load random quote
async function loadRandomQuote() {
  try {
    const response = await fetch('/api/dashboard/random-quote');
    const data = await response.json();

    if (data.quote) {
      document.getElementById('quote-text').textContent = data.quote.text;

      const authorName = data.quote.author_bakchod.pretty_name || data.quote.author_bakchod.username || 'Unknown';
      document.getElementById('quote-author').textContent = `— ${authorName}`;

      document.getElementById('quote-group').textContent = `📍 ${data.quote.quoted_in_group.name || 'Unknown Group'}`;

      const date = new Date(data.quote.created);
      document.getElementById('quote-date').textContent = `🕐 ${date.toLocaleDateString('en-US')}`;

      // Show the quote section
      document.getElementById('quote-section').style.display = 'block';
    }
  } catch (error) {
    console.error('Error loading quote:', error);
    // Don't show quote section if there's an error
  }
}

// Load version info
async function loadVersion() {
  try {
    const response = await fetch('/api/dashboard/version');
    const data = await response.json();

    document.getElementById('version').textContent = data.semver;
    document.getElementById('git-commit').textContent = data.git_commit_id.substring(0, 8);
    document.getElementById('commit-time').textContent = data.git_commit_time;
    document.getElementById('uptime').textContent = data.pretty_uptime;
  } catch (error) {
    console.error('Error loading version:', error);
    showError('version');
  }
}

// Utility: Format numbers with commas
function formatNumber(num) {
  if (num === null || num === undefined) return '0';
  return num.toLocaleString('en-US');
}

// Utility: Show error message
function showError(section) {
  console.error(`Failed to load ${section} data`);
  // Optionally show error in UI
}
