(() => {
  "use strict";

  // Mermaid bleibt eine progressive Verbesserung: Ohne lokal bereitgestellte
  // Runtime bleibt der Quelltext vollständig lesbar. Es werden keine CDNs oder
  // fremden Origins kontaktiert.
  const blocks = document.querySelectorAll("pre > code.language-mermaid");
  if (blocks.length === 0 || !globalThis.mermaid) return;

  globalThis.mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
  for (const [index, code] of blocks.entries()) {
    const container = code.parentElement;
    if (!container) continue;
    const target = document.createElement("div");
    target.className = "mermaid";
    target.id = `mermaid-${index + 1}`;
    target.textContent = code.textContent || "";
    container.replaceWith(target);
  }
  globalThis.mermaid.run({ querySelector: ".mermaid" });
})();
