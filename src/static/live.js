console.log("Live!");

const socket = io({
  path: "/socket.io",
});

socket.on("connect", function () {
  console.log("connected");
  socket.emit("command", { data: "I'm connected!" });
});

socket.on("message", function (msg, cb) {
  console.log("sio recv message", msg);
  let messagesTbody = document.getElementById("messages-table-body");

  let messageTr = document.createElement("tr");

  let messageTd = createTd(msg.message.time_sent);
  messageTr.appendChild(messageTd);

  messageTd = createTd(msg.message.message_id);
  messageTr.appendChild(messageTd);

  messageTd = createTd(msg.message?.from_bakchod?.pretty_name);
  messageTr.appendChild(messageTd);

  messageTd = createTd(msg.message?.update?.message?.chat?.title);
  messageTr.appendChild(messageTd);

  messageTd = createTd(msg.message.text);
  messageTr.appendChild(messageTd);

  messagesTbody.insertBefore(messageTr, messagesTbody.firstChild);
});

function createTd(innerText) {
  let td = document.createElement("td");
  td.innerText = innerText;
  return td;
}
