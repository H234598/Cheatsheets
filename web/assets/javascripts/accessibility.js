(() => {
  "use strict";

  function enhanceScrollableRegions() {
    const selectors = [
      [".md-typeset__table", "Horizontal scrollbare Tabelle"],
      [".md-typeset pre", "Horizontal scrollbarer Codeblock"],
    ];

    for (const [selector, label] of selectors) {
      document.querySelectorAll(selector).forEach((element, index) => {
        if (!element.hasAttribute("tabindex")) element.tabIndex = 0;
        if (!element.hasAttribute("aria-label")) {
          element.setAttribute("aria-label", `${label} ${index + 1}`);
        }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enhanceScrollableRegions, {
      once: true,
    });
  } else {
    enhanceScrollableRegions();
  }

  document.addEventListener("cheatsheets:ui-ready", enhanceScrollableRegions);
})();
