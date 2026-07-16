(function () {
  var toggle = document.getElementById("ragtail-sidebar-toggle");
  var sidebar = document.getElementById("ragtail-sidebar");
  var backdrop = document.getElementById("ragtail-sidebar-backdrop");
  if (!toggle || !sidebar || !backdrop) return;

  function isMobile() {
    return window.matchMedia("(max-width: 767px)").matches;
  }

  function setOpen(open) {
    sidebar.classList.toggle("translate-x-0", open);
    sidebar.classList.toggle("-translate-x-full", !open);
    backdrop.classList.toggle("hidden", !open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Menü schließen" : "Menü öffnen");
    document.body.classList.toggle("overflow-hidden", open && isMobile());
  }

  toggle.addEventListener("click", function () {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  backdrop.addEventListener("click", function () {
    setOpen(false);
  });

  sidebar.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      if (isMobile()) {
        setOpen(false);
      }
    });
  });

  window.addEventListener("resize", function () {
    if (!isMobile()) {
      setOpen(false);
      document.body.classList.remove("overflow-hidden");
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      setOpen(false);
    }
  });
})();
