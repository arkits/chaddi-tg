// Logs page JavaScript - handles Socket.IO log streaming

console.log("Logs Viewer initialized!");

// State
let socket = null;
let isPaused = false;
let logCount = 0;
let autoScroll = true;

// DOM elements
const logsList = document.getElementById('logs-list');
const connectionStatus = document.getElementById('connection-status');
const connectionText = document.getElementById('connection-text');
const clearBtn = document.getElementById('clear-btn');
const pauseBtn = document.getElementById('pause-btn');
const autoScrollToggle = document.getElementById('auto-scroll-toggle');
const logCountEl = document.getElementById('log-count');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initSocketConnection();
    setupEventListeners();
});

function setupEventListeners() {
    // Clear button
    clearBtn.addEventListener('click', () => {
        clearLogs();
    });

    // Pause/Resume button
    pauseBtn.addEventListener('click', () => {
        togglePause();
    });

    // Auto-scroll toggle
    autoScrollToggle.addEventListener('change', (e) => {
        autoScroll = e.target.checked;
    });
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

    // Add to list
    logsList.appendChild(logLine);
    logCount++;
    updateLogCount();

    // Limit to last 500 lines to prevent memory issues
    const maxLines = 500;
    if (logsList.children.length > maxLines) {
        logsList.removeChild(logsList.firstChild);
        logCount--;
    }

    // Auto-scroll if enabled
    if (autoScroll) {
        scrollToBottom();
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

function updateConnectionStatus(status, text) {
    connectionStatus.className = 'status-indicator status-' + status;
    connectionText.textContent = text;
}

function clearLogs() {
    logsList.innerHTML = '';
    logCount = 0;
    updateLogCount();
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

function updateLogCount() {
    logCountEl.textContent = `${logCount} line${logCount !== 1 ? 's' : ''} displayed`;
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'log-line log-error';
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
