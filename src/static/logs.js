// Logs page JavaScript - handles Socket.IO log streaming and live messages

console.log("Live Activity Viewer initialized!");

// State
let socket = null;
let isPaused = false;
let itemCount = 0;
let messageCount = 0;
let autoScroll = true;
let currentFilter = 'all'; // 'all', 'logs', 'messages'

// DOM elements
const logsList = document.getElementById('logs-list');
const connectionStatus = document.getElementById('connection-status');
const connectionText = document.getElementById('connection-text');
const clearBtn = document.getElementById('clear-btn');
const pauseBtn = document.getElementById('pause-btn');
const autoScrollToggle = document.getElementById('auto-scroll-toggle');
const logCountEl = document.getElementById('log-count');
const filterBtns = document.querySelectorAll('.filter-btn');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initSocketConnection();
    setupEventListeners();
});

function setupEventListeners() {
    // Clear button
    clearBtn.addEventListener('click', () => {
        clearDisplay();
    });

    // Pause/Resume button
    pauseBtn.addEventListener('click', () => {
        togglePause();
    });

    // Auto-scroll toggle
    autoScrollToggle.addEventListener('change', (e) => {
        autoScroll = e.target.checked;
    });

    // Filter buttons
    filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const filter = e.target.dataset.filter;
            setFilter(filter);
        });
    });
}

function setFilter(filter) {
    currentFilter = filter;

    // Update active button
    filterBtns.forEach(btn => {
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Show/hide items based on filter
    const logLines = logsList.querySelectorAll('.log-line');
    const messageCards = logsList.querySelectorAll('.message-card');

    logLines.forEach(line => {
        if (filter === 'all' || filter === 'logs') {
            line.style.display = '';
        } else {
            line.style.display = 'none';
        }
    });

    messageCards.forEach(card => {
        if (filter === 'all' || filter === 'messages') {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });

    updateItemCount();
}

function initSocketConnection() {
    // Create Socket.IO connection
    socket = io({
        path: "/socket.io",
    });

    // Connection opened
    socket.on("connect", () => {
        console.log("Socket.IO connected");
        updateConnectionStatus('connected', 'Connected');

        // Start log streaming
        socket.emit("start_log_stream");
    });

    // Connection closed
    socket.on("disconnect", () => {
        console.log("Socket.IO disconnected");
        updateConnectionStatus('error', 'Disconnected');
    });

    // Log connected event
    socket.on("log_connected", (data) => {
        console.log("Log stream connected:", data.message);
        clearWelcomeMessage();
    });

    // Receive log lines
    socket.on("log_line", (data) => {
        if (!isPaused) {
            addLogLine(data.content);
        }
    });

    // Receive live messages
    socket.on("message", (msg) => {
        console.log("Received message:", msg);
        clearWelcomeMessage();

        if (!isPaused) {
            addMessage(msg.message);
        }
    });

    // Handle errors
    socket.on("log_error", (data) => {
        console.error("Log stream error:", data.message);
        showError(data.message);
        updateConnectionStatus('error', 'Error: ' + data.message);
    });
}

function clearWelcomeMessage() {
    const welcomeMsg = logsList.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
}

function addLogLine(content) {
    // Create log line element
    const logLine = document.createElement('div');
    logLine.className = 'log-line';
    logLine.dataset.type = 'log';
    logLine.dataset.timestamp = Date.now();

    // Parse log level and apply appropriate styling
    const logClass = detectLogLevel(content);
    if (logClass) {
        logLine.classList.add(logClass);
    }

    // Add timestamp if present
    const timestampMatch = content.match(/^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[.,]\d+)/);
    if (timestampMatch) {
        const timestamp = document.createElement('span');
        timestamp.className = 'log-timestamp';
        timestamp.textContent = timestampMatch[1];
        logLine.appendChild(timestamp);

        const message = document.createElement('span');
        message.className = 'log-message';
        message.textContent = content.substring(timestampMatch[0].length).trim();
        logLine.appendChild(message);
    } else {
        logLine.textContent = content;
    }

    // Apply filter
    if (currentFilter === 'messages') {
        logLine.style.display = 'none';
    }

    // Add to list
    logsList.appendChild(logLine);
    itemCount++;
    updateItemCount();

    // Limit to last 500 items to prevent memory issues
    limitItems();

    // Auto-scroll if enabled
    if (autoScroll) {
        scrollToBottom();
    }
}

function addMessage(message) {
    const messageCard = document.createElement('div');
    messageCard.className = 'message-card';
    messageCard.dataset.type = 'message';
    messageCard.dataset.timestamp = Date.now();

    // Extract data
    const fromName = message?.from_bakchod?.pretty_name || 'Unknown';
    const chatTitle = message?.update?.message?.chat?.title || 'Direct Message';
    const messageText = message.text || '';
    const timestamp = message.time_sent;
    const messageId = message.message_id;

    const userColor = getColorForUser(fromName);
    const initials = getInitials(fromName);

    messageCard.innerHTML = `
        <div class="message-avatar" style="background-color: ${userColor}">
            ${initials}
        </div>
        <div class="message-content">
            <div class="message-header">
                <div class="message-user-info">
                    <span class="message-user-name" style="color: ${userColor}">${escapeHtml(fromName)}</span>
                    <span class="message-chat-badge">${escapeHtml(chatTitle)}</span>
                </div>
                <span class="message-timestamp" title="${timestamp}">${formatTimestamp(timestamp)}</span>
            </div>
            <div class="message-text">${escapeHtml(messageText)}</div>
            <div class="message-footer">
                <span class="message-id">#${messageId}</span>
            </div>
        </div>
    `;

    // Apply filter
    if (currentFilter === 'logs') {
        messageCard.style.display = 'none';
    }

    // Add to list
    logsList.appendChild(messageCard);
    itemCount++;
    messageCount++;
    updateItemCount();

    // Add animation
    setTimeout(() => {
        messageCard.classList.add('message-card-visible');
    }, 10);

    // Limit items
    limitItems();

    // Auto-scroll if enabled
    if (autoScroll) {
        scrollToBottom();
    }
}

function limitItems() {
    const maxItems = 500;
    const allItems = logsList.querySelectorAll('.log-line, .message-card');

    if (allItems.length > maxItems) {
        const itemsToRemove = allItems.length - maxItems;
        for (let i = 0; i < itemsToRemove; i++) {
            allItems[i].remove();
            itemCount--;
        }
    }
}

function detectLogLevel(content) {
    const contentLower = content.toLowerCase();
    if (contentLower.includes('error') || contentLower.includes('exception')) {
        return 'log-error';
    } else if (contentLower.includes('warning') || contentLower.includes('warn')) {
        return 'log-warning';
    } else if (contentLower.includes('debug')) {
        return 'log-debug';
    } else if (contentLower.includes('info')) {
        return 'log-info';
    } else if (contentLower.includes('success')) {
        return 'log-success';
    }
    return null;
}

// Helper functions from live.js
function getInitials(name) {
    if (!name) return '?';
    const parts = name.trim().split(' ');
    if (parts.length === 1) return parts[0][0].toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getColorForUser(name) {
    if (!name) return '#6c757d';

    const colors = [
        '#007bff', '#28a745', '#17a2b8', '#ffc107', '#dc3545',
        '#6610f2', '#e83e8c', '#fd7e14', '#20c997', '#6f42c1',
    ];

    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';

    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateConnectionStatus(status, text) {
    connectionStatus.className = 'status-indicator status-' + status;
    connectionText.textContent = text;
}

function clearDisplay() {
    logsList.innerHTML = '';
    itemCount = 0;
    messageCount = 0;
    updateItemCount();
}

function togglePause() {
    isPaused = !isPaused;
    pauseBtn.textContent = isPaused ? 'Resume' : 'Pause';
    pauseBtn.classList.toggle('btn-primary', isPaused);

    if (isPaused) {
        updateConnectionStatus('paused', 'Paused');
        // Stop streaming
        if (socket && socket.connected) {
            socket.emit("stop_log_stream");
        }
    } else {
        updateConnectionStatus('connected', 'Connected');
        // Resume streaming
        if (socket && socket.connected) {
            socket.emit("start_log_stream");
        }
    }
}

function scrollToBottom() {
    const logsContainer = document.getElementById('logs-container');
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

function updateItemCount() {
    const visibleItems = Array.from(logsList.querySelectorAll('.log-line, .message-card'))
        .filter(item => item.style.display !== 'none').length;

    logCountEl.textContent = `${visibleItems} item${visibleItems !== 1 ? 's' : ''} displayed`;
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'log-line log-error';
    errorDiv.dataset.type = 'log';
    errorDiv.textContent = `ERROR: ${message}`;
    logsList.appendChild(errorDiv);

    if (autoScroll) {
        scrollToBottom();
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (socket) {
        socket.emit("stop_log_stream");
        socket.disconnect();
    }
});
