(function () {
  function updatePreview(fieldName, id, title, url) {
    var input = document.getElementById("id_" + fieldName);
    var preview = document.getElementById("preview_" + fieldName);
    var editLink = document.getElementById("edit_" + fieldName);
    if (!input || !preview) return;
    input.value = id || "";
    if (url) {
      preview.innerHTML =
        '<img src="' +
        url +
        '" alt="' +
        (title || "Selected image") +
        '" class="max-h-48 w-full object-contain" />';
    } else {
      preview.innerHTML = '<p class="px-4 py-6 text-sm text-gray-500">No image selected</p>';
    }
    if (editLink) {
      if (id) {
        editLink.href = "/admin/images/" + id + "/edit/";
        editLink.hidden = false;
      } else {
        editLink.href = "#";
        editLink.hidden = true;
      }
    }
  }

  document.querySelectorAll(".ragtail-image-choose-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      var field = button.getAttribute("data-field");
      var url = button.getAttribute("data-chooser-url");
      if (!field || !url) return;
      window.open(url, "ragtail-image-chooser-" + field, "width=960,height=720");
    });
  });

  document.querySelectorAll(".ragtail-image-clear-btn").forEach(function (button) {
    button.addEventListener("click", function () {
      var field = button.getAttribute("data-field");
      if (!field) return;
      updatePreview(field, "", "", "");
    });
  });

  window.addEventListener("message", function (event) {
    if (event.origin !== window.location.origin) return;
    var data = event.data;
    if (!data || data.type !== "ragtail-image-selected") return;
    updatePreview(data.field, data.id, data.title, data.url);
  });
})();
