// Messenger State
const state = {
  groups: {
    data: [],
    currentPage: 1,
    totalPages: 1,
    loading: false,
    hasMore: true,
  },
  messages: {
    data: [],
    currentPage: 1,
    totalPages: 1,
    loading: false,
    hasMore: true,
  },
  selectedGroupId: null,
  deeplinkGroupId: null,
};

// DOM Elements
const groupsList = document.getElementById('groupsList');
const messagesList = document.getElementById('messagesList');
const messagesHeader = document.getElementById('messagesHeader');
const messagesContainer = document.getElementById('messagesContainer');
const emptyState = document.getElementById('emptyState');
const groupsCount = document.getElementById('groupsCount');
const selectedGroupName = document.getElementById('selectedGroupName');
const selectedGroupId = document.getElementById('selectedGroupId');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Check for deep link group_id in URL
  const urlParams = new URLSearchParams(window.location.search);
  const groupId = urlParams.get('group_id');
  if (groupId) {
    state.deeplinkGroupId = groupId;
  }

  loadGroups();
  setupScrollListeners();
});

// Load Groups
async function loadGroups() {
  if (state.groups.loading || !state.groups.hasMore) return;

  state.groups.loading = true;

  try {
    const response = await fetch(`/api/groups?page_number=${state.groups.currentPage}`);
    const data = await response.json();

    if (state.groups.currentPage === 1) {
      state.groups.data = [];
      groupsList.innerHTML = '';
    }

    state.groups.data.push(...data.groups);
    state.groups.totalPages = data.total_pages;
    state.groups.hasMore = state.groups.currentPage < data.total_pages;

    // Update groups count
    groupsCount.textContent = `${data.total_groups} groups`;

    // Render groups
    data.groups.forEach(group => renderGroup(group));

    state.groups.currentPage++;

    // Check for deep link after first page load
    if (state.groups.currentPage === 2 && state.deeplinkGroupId) {
      const group = state.groups.data.find(g => g.group_id == state.deeplinkGroupId);
      if (group) {
        selectGroup(group);
        state.deeplinkGroupId = null; // Clear after use
      } else if (state.groups.hasMore) {
        // Group not found yet, load more pages
        await loadGroups();
      }
    }
  } catch (error) {
    console.error('Error loading groups:', error);
    groupsList.innerHTML = '<div class="loading-indicator" style="color: #dc3545;">Error loading groups</div>';
  } finally {
    state.groups.loading = false;
  }
}

// Render Group
function renderGroup(group) {
  const groupItem = document.createElement('div');
  groupItem.className = 'group-item';
  groupItem.dataset.groupId = group.group_id;

  const updatedDate = new Date(group.updated);
  const formattedDate = formatDate(updatedDate);

  groupItem.innerHTML = `
    <div class="group-info">
      <div class="group-name">${escapeHtml(group.name)}</div>
      <div class="group-updated">${formattedDate}</div>
    </div>
  `;

  groupItem.addEventListener('click', () => selectGroup(group));

  groupsList.appendChild(groupItem);
}

// Select Group
function selectGroup(group) {
  state.selectedGroupId = group.group_id;
  state.messages.currentPage = 1;
  state.messages.hasMore = true;
  state.messages.data = [];

  // Update UI
  document.querySelectorAll('.group-item').forEach(item => {
    item.classList.remove('active');
  });
  const selectedElement = document.querySelector(`[data-group-id="${group.group_id}"]`);
  if (selectedElement) {
    selectedElement.classList.add('active');
    // Scroll the selected group into view
    selectedElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  selectedGroupName.textContent = group.name;
  selectedGroupId.textContent = `ID: ${group.group_id}`;

  emptyState.style.display = 'none';
  messagesContainer.style.display = 'flex';
  messagesContainer.style.flexDirection = 'column';

  messagesList.innerHTML = '<div class="loading-indicator">Loading messages...</div>';

  loadMessages();
}

// Load Messages
async function loadMessages() {
  if (!state.selectedGroupId || state.messages.loading || !state.messages.hasMore) return;

  state.messages.loading = true;

  try {
    const response = await fetch(
      `/api/groups/${state.selectedGroupId}/messages?page_number=${state.messages.currentPage}`
    );
    const data = await response.json();

    if (state.messages.currentPage === 1) {
      state.messages.data = [];
      messagesList.innerHTML = '';
    }

    // Messages come in reverse chronological order, so we prepend them
    const newMessages = data.messages.reverse();
    state.messages.data.unshift(...newMessages);
    state.messages.totalPages = data.total_pages;
    state.messages.hasMore = state.messages.currentPage < data.total_pages;

    // Render messages
    newMessages.forEach(message => renderMessage(message));

    // If first page, scroll to bottom
    if (state.messages.currentPage === 1) {
      messagesList.scrollTop = messagesList.scrollHeight;
    }

    state.messages.currentPage++;
  } catch (error) {
    console.error('Error loading messages:', error);
    messagesList.innerHTML = '<div class="loading-indicator" style="color: #dc3545;">Error loading messages</div>';
  } finally {
    state.messages.loading = false;
  }
}

// Render Message
function renderMessage(message) {
  const messageItem = document.createElement('div');
  messageItem.className = 'message-item';

  const timeSent = new Date(message.time_sent);
  const formattedTime = formatDateTime(timeSent);

  const initials = getInitials(message.from_bakchod.pretty_name || message.from_bakchod.username);
  const authorName = message.from_bakchod.pretty_name || message.from_bakchod.username || 'Unknown';

  messageItem.innerHTML = `
    <div class="message-header">
      <div class="message-author">
        <div class="author-avatar" style="background: ${getColorForUser(authorName)}">
          ${escapeHtml(initials)}
        </div>
        <span class="author-name">${escapeHtml(authorName)}</span>
      </div>
      <span class="message-time">${formattedTime}</span>
    </div>
    <div class="message-text">${escapeHtml(message.text || '(No text)')}</div>
    <div class="message-id">Message ID: ${message.message_id}</div>
  `;

  messagesList.appendChild(messageItem);
}

// Setup Scroll Listeners for Infinite Scroll
function setupScrollListeners() {
  // Groups infinite scroll
  groupsList.addEventListener('scroll', () => {
    const { scrollTop, scrollHeight, clientHeight } = groupsList;
    if (scrollTop + clientHeight >= scrollHeight - 100) {
      loadGroups();
    }
  });

  // Messages infinite scroll (scroll up to load older messages)
  messagesList.addEventListener('scroll', () => {
    if (messagesList.scrollTop === 0 && state.messages.hasMore) {
      const oldScrollHeight = messagesList.scrollHeight;
      loadMessages().then(() => {
        // Maintain scroll position after loading older messages
        messagesList.scrollTop = messagesList.scrollHeight - oldScrollHeight;
      });
    }
  });
}

// Utility Functions
function formatDate(date) {
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return 'Today';
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString();
  }
}

function formatDateTime(date) {
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getInitials(name) {
  if (!name) return '?';
  const parts = name.split(' ');
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

function getColorForUser(name) {
  const colors = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
    'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
    'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
    'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
    'linear-gradient(135deg, #ff6e7f 0%, #bfe9ff 100%)',
  ];

  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
