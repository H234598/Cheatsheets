(() => {
  "use strict";

  const GOTO_TIMEOUT_MS = 1500;
  let deadline = 0;

  function isEditable(target) {
    return (
      target instanceof HTMLElement &&
      (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))
    );
  }

  function baseUrl() {
    const meta = document.querySelector('meta[name="cheatsheets-base-url"]');
    try {
      return new URL(meta?.content || "./", document.baseURI);
    } catch {
      return new URL("./", document.baseURI);
    }
  }

  function graphTarget() {
    const offline = document.querySelector(
      'meta[name="cheatsheets-offline"][content="true"]',
    );
    return offline ? "wissensgraph/index.html" : "wissensgraph/";
  }

  document.addEventListener(
    "keydown",
    (event) => {
      if (
        event.defaultPrevented ||
        event.ctrlKey ||
        event.altKey ||
        event.metaKey ||
        isEditable(event.target)
      ) {
        return;
      }

      const key = event.key.toLowerCase();
      if (key === "g") {
        deadline = Date.now() + GOTO_TIMEOUT_MS;
        return;
      }
      if (key !== "w" || Date.now() > deadline) return;

      deadline = 0;
      event.preventDefault();
      event.stopImmediatePropagation();
      window.location.assign(new URL(graphTarget(), baseUrl()).href);
    },
    { capture: true },
  );
})();
