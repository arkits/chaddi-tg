let load_messages_button = document.getElementById("load-messages-button");

load_messages_button.addEventListener("click", function () {
  let page_number = document.getElementById("group-messages-page-number").value;
  let limit = document.getElementById("group-messages-limit").value;

  const parser = new URL(window.location);
  parser.searchParams.set("page", page_number);
  parser.searchParams.set("limit", limit);

  window.location = parser.href;
});
