(function () {
  var editor = document.getElementById("ragtail-focal-editor");
  if (!editor) return;
  var image = document.getElementById("ragtail-focal-image");
  var marker = document.getElementById("ragtail-focal-marker");
  var inputX = document.getElementById("id_focal_point_x");
  var inputY = document.getElementById("id_focal_point_y");
  if (!image || !marker || !inputX || !inputY) return;

  function placeMarker() {
    var x = parseFloat(inputX.value || "0.5");
    var y = parseFloat(inputY.value || "0.5");
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      x = 0.5;
      y = 0.5;
    }
    marker.style.left = x * 100 + "%";
    marker.style.top = y * 100 + "%";
    marker.hidden = false;
  }

  function setPoint(clientX, clientY) {
    var rect = image.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    var x = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    var y = Math.max(0, Math.min(1, (clientY - rect.top) / rect.height));
    inputX.value = x.toFixed(4);
    inputY.value = y.toFixed(4);
    placeMarker();
  }

  editor.addEventListener("click", function (event) {
    setPoint(event.clientX, event.clientY);
  });

  image.addEventListener("load", placeMarker);
  if (image.complete) {
    placeMarker();
  }
  window.addEventListener("resize", placeMarker);
})();
