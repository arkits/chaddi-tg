let update_rokda_button = document.getElementById("update-rokda-button");

update_rokda_button.addEventListener("click", function () {
  let tg_id = document.getElementById("tg-id").value;
  let rokda = document.getElementById("rokda-input").value;

  let headers = new Headers();
  headers.append("Content-Type", "application/json");

  let requestOptions = {
    method: "POST",
    headers: headers,
    body: JSON.stringify({
      bakchod_id: tg_id,
      rokda: rokda,
    }),
    redirect: "follow",
  };

  fetch("/api/bakchod/rokda", requestOptions)
    .then((response) => response.text())
    .then((result) => location.reload())
    .catch((error) => console.log("error", error));
});

let update_metadata_button = document.getElementById("update-metadata-button");

update_metadata_button.addEventListener("click", function () {
  let tg_id = document.getElementById("tg-id").value;
  let metadata = document.getElementById("metadata-textarea").value;

  let headers = new Headers();
  headers.append("Content-Type", "application/json");

  let requestOptions = {
    method: "POST",
    headers: headers,
    body: JSON.stringify({
      bakchod_id: tg_id,
      metadata: metadata,
    }),
    redirect: "follow",
  };

  fetch("/api/bakchod/metadata", requestOptions)
    .then((response) => response.text())
    .then((result) => location.reload())
    .catch((error) => console.log("error", error));
});
