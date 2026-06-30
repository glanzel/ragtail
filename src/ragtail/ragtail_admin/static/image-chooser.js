(function () {
  var fieldInput = document.getElementById("ragtail-chooser-field");
  var fieldName = fieldInput ? fieldInput.value : "";
  document.querySelectorAll(".ragtail-image-chooser-item").forEach(function (button) {
    button.addEventListener("click", function () {
      var payload = {
        type: "ragtail-image-selected",
        field: fieldName,
        id: button.getAttribute("data-image-id"),
        title: button.getAttribute("data-image-title"),
        url: button.getAttribute("data-image-url"),
      };
      if (window.opener && !window.opener.closed) {
        window.opener.postMessage(payload, window.location.origin);
        window.close();
      } else if (window.parent && window.parent !== window) {
        window.parent.postMessage(payload, window.location.origin);
      }
    });
  });
})();
