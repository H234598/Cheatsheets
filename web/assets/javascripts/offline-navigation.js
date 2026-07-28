(() => {
  "use strict";

  const offline = document.querySelector('meta[name="cheatsheets-offline"][content="true"]');
  if (!offline) return;

  const GOTO_TIMEOUT_MS = 1500;
  const TARGETS = Object.freeze({
    i: "index/gesamt.html",
    k: "kategorien/index.html",
    d: "downloads/index.html",
  });
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
      if (Date.now() > deadline || !TARGETS[key]) return;

      deadline = 0;
      event.preventDefault();
      event.stopImmediatePropagation();
      window.location.assign(new URL(TARGETS[key], baseUrl()).href);
    },
    { capture: true },
  );
})();
