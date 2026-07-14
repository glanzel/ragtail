(function () {
  var toggle = document.getElementById("site-nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!toggle || !nav) return;

  function isMobile() {
    return window.matchMedia("(max-width: 767px)").matches;
  }

  function setOpen(open) {
    nav.classList.toggle("hidden", !open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Menü schließen" : "Menü öffnen");
  }

  toggle.addEventListener("click", function () {
    setOpen(nav.classList.contains("hidden"));
  });

  nav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      if (isMobile()) {
        setOpen(false);
      }
    });
  });

  window.addEventListener("resize", function () {
    if (!isMobile()) {
      nav.classList.remove("hidden");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Menü öffnen");
    } else if (!toggle.getAttribute("aria-expanded") || toggle.getAttribute("aria-expanded") === "false") {
      nav.classList.add("hidden");
    }
  });
})();
