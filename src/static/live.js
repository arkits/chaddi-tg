console.log("Live Messenger initialized!");

// State
let messageCount = 0;
let autoScroll = true;

// Elements
const messagesList = document.getElementById("messages-list");
const connectionStatus = document.getElementById("connection-status");
const connectionText = document.getElementById("connection-text");
const messageCountEl = document.getElementById("message-count");
const autoScrollToggle = document.getElementById("auto-scroll-toggle");
const messagesContainer = document.getElementById("messages-container");

// Auto-scroll toggle handler
autoScrollToggle.addEventListener("change", (e) => {
  autoScroll = e.target.checked;
  if (autoScroll) {
    scrollToBottom();
  }
});

// Socket.IO connection
const socket = io({
  path: "/ws/socket.io", // for agnee
  // path: "/socket.io", // for local dev
});

socket.on("connect", function () {
  console.log("Socket.IO connected");
  socket.emit("command", { data: "I'm connected!" });
  updateConnectionStatus(true);
});

socket.on("disconnect", function () {
  console.log("Socket.IO disconnected");
  updateConnectionStatus(false);
});

socket.on("message", function (msg, cb) {
  console.log("Received message:", msg);

  // Remove welcome message on first message
  const welcomeMsg = document.querySelector(".welcome-message");
  if (welcomeMsg) {
    welcomeMsg.remove();
  }

  addMessage(msg.message);
  messageCount++;
  updateMessageCount();

  if (autoScroll) {
    scrollToBottom();
  }
});

// Update connection status
function updateConnectionStatus(connected) {
  if (connected) {
    connectionStatus.className = "status-indicator status-connected";
    connectionText.textContent = "Connected";
  } else {
    connectionStatus.className = "status-indicator status-disconnected";
    connectionText.textContent = "Disconnected";
  }
}

// Update message count
function updateMessageCount() {
  messageCountEl.textContent = `${messageCount} message${messageCount !== 1 ? 's' : ''}`;
}

// Scroll to bottom
function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Get initials from name
function getInitials(name) {
  if (!name) return "?";
  const parts = name.trim().split(" ");
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// Get color for user (consistent color based on name hash)
function getColorForUser(name) {
  if (!name) return "#6c757d";

  const colors = [
    "#007bff", "#28a745", "#17a2b8", "#ffc107",
    "#dc3545", "#6610f2", "#e83e8c", "#fd7e14",
    "#20c997", "#6f42c1"
  ];

  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
}

// Format timestamp
function formatTimestamp(timestamp) {
  if (!timestamp) return "";

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;

  // Format as date and time
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Add message to the UI
function addMessage(message) {
  const messageCard = document.createElement("div");
  messageCard.className = "message-card";

  // Extract data
  const fromName = message?.from_bakchod?.pretty_name || "Unknown";
  const chatTitle = message?.update?.message?.chat?.title || "Direct Message";
  const messageText = message.text || "";
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

  messagesList.appendChild(messageCard);

  // Add animation
  setTimeout(() => {
    messageCard.classList.add("message-card-visible");
  }, 10);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
