(() => {
  "use strict";

  const root = document.querySelector("[data-cheat-knowledge-graph]");
  if (!root) return;

  const SVG_NS = "http://www.w3.org/2000/svg";
  const TYPE_LABELS = Object.freeze({
    category: "Kategorie",
    page: "Fachseite",
    tag: "Tag",
  });
  const EDGE_LABELS = Object.freeze({
    contains: "Kategoriezuordnung",
    tagged: "Tagbeziehung",
    links: "Querverweis",
  });
  const state = {
    graph: null,
    query: "",
    selectedId: null,
    nodeTypes: new Set(["category", "page", "tag"]),
    edgeTypes: new Set(["contains", "tagged"]),
    scale: 1,
  };

  function element(tag, attributes = {}, text = "") {
    const node = document.createElement(tag);
    for (const [name, value] of Object.entries(attributes)) {
      if (value === null || value === undefined) continue;
      if (name === "className") node.className = String(value);
      else node.setAttribute(name, String(value));
    }
    if (text) node.textContent = text;
    return node;
  }

  function svgElement(tag, attributes = {}) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [name, value] of Object.entries(attributes)) {
      if (value === null || value === undefined) continue;
      node.setAttribute(name, String(value));
    }
    return node;
  }

  function normalized(value) {
    return String(value || "")
      .normalize("NFKC")
      .trim()
      .toLocaleLowerCase("de");
  }

  function baseUrl() {
    const meta = document.querySelector('meta[name="cheatsheets-base-url"]');
    try {
      return new URL(meta?.content || "./", document.baseURI);
    } catch {
      return new URL("./", document.baseURI);
    }
  }

  function offlineMode() {
    return Boolean(
      document.querySelector('meta[name="cheatsheets-offline"][content="true"]'),
    );
  }

  function safeUrl(value) {
    try {
      const url = new URL(String(value || ""), baseUrl());
      const current = new URL(window.location.href);
      if (url.protocol === "file:" && current.protocol === "file:") return url;
      return url.origin === current.origin ? url : null;
    } catch {
      return null;
    }
  }

  function graphSource() {
    const source = root.dataset.graphSource || "../data/knowledge-graph.json";
    const url = new URL(source, document.baseURI);
    const current = new URL(window.location.href);
    if (url.protocol !== "file:" && url.origin !== current.origin) {
      throw new Error(`Unsicherer Graphdatenursprung: ${url.origin}`);
    }
    return url;
  }

  function validGraph(payload) {
    if (!payload || payload.schema_version !== 1) return false;
    if (!Array.isArray(payload.nodes) || !Array.isArray(payload.edges)) return false;
    if (!payload.viewbox || !Number.isFinite(payload.viewbox.width)) return false;
    const ids = new Set();
    for (const node of payload.nodes) {
      if (!node || typeof node.id !== "string" || ids.has(node.id)) return false;
      if (!TYPE_LABELS[node.type]) return false;
      if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) return false;
      ids.add(node.id);
    }
    return payload.edges.every(
      (edge) =>
        edge &&
        EDGE_LABELS[edge.type] &&
        ids.has(edge.source) &&
        ids.has(edge.target),
    );
  }

  function checkbox(name, value, label, checked) {
    const wrapper = element("label", { className: "cheat-graph-option" });
    const input = element("input", { type: "checkbox", name, value });
    input.checked = checked;
    wrapper.append(input, document.createTextNode(label));
    return { wrapper, input };
  }

  function buildControls() {
    const host = root.querySelector("[data-cheat-graph-controls]");
    if (!host) return;
    host.replaceChildren();
    host.className = "cheat-graph-controls";

    const searchLabel = element("label", { className: "cheat-graph-search" });
    searchLabel.append(document.createTextNode("Knoten suchen"));
    const search = element("input", {
      type: "search",
      autocomplete: "off",
      placeholder: "Titel, Alias, Kategorie oder Tag",
      "data-cheat-graph-search": "",
    });
    search.value = state.query;
    search.addEventListener("input", () => {
      state.query = normalized(search.value);
      renderGraph();
    });
    searchLabel.append(search);

    const nodeFieldset = element("fieldset");
    nodeFieldset.append(element("legend", {}, "Knotentypen"));
    for (const [type, label] of Object.entries(TYPE_LABELS)) {
      const option = checkbox("node-type", type, label, state.nodeTypes.has(type));
      option.input.addEventListener("change", () => {
        if (option.input.checked) state.nodeTypes.add(type);
        else state.nodeTypes.delete(type);
        renderGraph();
      });
      nodeFieldset.append(option.wrapper);
    }

    const edgeFieldset = element("fieldset");
    edgeFieldset.append(element("legend", {}, "Beziehungen"));
    for (const [type, label] of Object.entries(EDGE_LABELS)) {
      const option = checkbox("edge-type", type, label, state.edgeTypes.has(type));
      option.input.addEventListener("change", () => {
        if (option.input.checked) state.edgeTypes.add(type);
        else state.edgeTypes.delete(type);
        renderGraph();
      });
      edgeFieldset.append(option.wrapper);
    }

    const zoom = element("div", {
      className: "cheat-graph-zoom",
      "aria-label": "Darstellungsgröße",
    });
    const zoomOut = element("button", { type: "button", className: "md-button" }, "−");
    zoomOut.setAttribute("aria-label", "Graph verkleinern");
    const zoomReset = element(
      "button",
      { type: "button", className: "md-button" },
      `${Math.round(state.scale * 100)} %`,
    );
    zoomReset.setAttribute("aria-label", "Darstellungsgröße zurücksetzen");
    const zoomIn = element("button", { type: "button", className: "md-button" }, "+");
    zoomIn.setAttribute("aria-label", "Graph vergrößern");
    const applyScale = (value) => {
      state.scale = Math.min(1.8, Math.max(0.65, value));
      zoomReset.textContent = `${Math.round(state.scale * 100)} %`;
      renderGraph();
    };
    zoomOut.addEventListener("click", () => applyScale(state.scale - 0.15));
    zoomReset.addEventListener("click", () => applyScale(1));
    zoomIn.addEventListener("click", () => applyScale(state.scale + 0.15));
    zoom.append(zoomOut, zoomReset, zoomIn);

    const reset = element(
      "button",
      { type: "button", className: "md-button" },
      "Auswahl zurücksetzen",
    );
    reset.addEventListener("click", () => {
      state.query = "";
      state.selectedId = null;
      state.nodeTypes = new Set(["category", "page", "tag"]);
      state.edgeTypes = new Set(["contains", "tagged"]);
      state.scale = 1;
      buildControls();
      renderGraph();
      root.querySelector("[data-cheat-graph-search]")?.focus();
    });

    host.append(searchLabel, nodeFieldset, edgeFieldset, zoom, reset);
    host.hidden = false;
  }

  function adjacentIds(nodeId) {
    const result = new Set([nodeId]);
    if (!state.graph) return result;
    for (const edge of state.graph.edges) {
      if (edge.source === nodeId) result.add(edge.target);
      if (edge.target === nodeId) result.add(edge.source);
    }
    return result;
  }

  function nodeMatches(node) {
    return !state.query || normalized(node.search || node.label).includes(state.query);
  }

  function visibleNodeIds() {
    const ids = new Set();
    if (!state.graph) return ids;
    for (const node of state.graph.nodes) {
      if (state.nodeTypes.has(node.type)) ids.add(node.id);
    }
    return ids;
  }

  function nodeShape(node) {
    if (node.type === "category") {
      return svgElement("rect", { x: -11, y: -11, width: 22, height: 22, rx: 4 });
    }
    if (node.type === "tag") {
      return svgElement("polygon", { points: "0,-9 9,0 0,9 -9,0" });
    }
    return svgElement("circle", { cx: 0, cy: 0, r: 7 });
  }

  function nodeDescription(node) {
    const parts = [TYPE_LABELS[node.type], node.label];
    if (Number.isFinite(node.page_count)) parts.push(`${node.page_count} Fachseiten`);
    if (Number.isFinite(node.minutes)) parts.push(`ca. ${node.minutes} Minuten`);
    return parts.join(" – ");
  }

  function selectNode(nodeId) {
    state.selectedId = nodeId;
    renderGraph();
  }

  function renderDetails() {
    const details = root.querySelector("[data-cheat-graph-details]");
    const body = root.querySelector("[data-cheat-graph-details-body]");
    if (!details || !body || !state.graph) return;
    const node = state.graph.nodes.find((item) => item.id === state.selectedId);
    body.replaceChildren();
    if (!node) {
      details.hidden = true;
      return;
    }

    body.append(
      element("p", { className: "cheat-graph-details__type" }, TYPE_LABELS[node.type]),
    );
    body.append(element("h3", {}, node.label));
    const facts = element("dl");
    const addFact = (term, value) => {
      facts.append(element("dt", {}, term), element("dd", {}, value));
    };
    if (node.category_id) addFact("Kategorie", node.category_id);
    if (Number.isFinite(node.page_count)) addFact("Fachseiten", String(node.page_count));
    if (Number.isFinite(node.minutes)) addFact("Lesezeit", `ca. ${node.minutes} Min.`);
    if (Array.isArray(node.tags) && node.tags.length) addFact("Tags", node.tags.join(", "));
    body.append(facts);

    const relationCounts = {};
    for (const edge of state.graph.edges) {
      if (edge.source === node.id || edge.target === node.id) {
        relationCounts[edge.type] = (relationCounts[edge.type] || 0) + 1;
      }
    }
    const relationText = Object.entries(relationCounts)
      .map(([type, count]) => `${EDGE_LABELS[type]}: ${count}`)
      .join(" · ");
    if (relationText) body.append(element("p", {}, relationText));

    const url = safeUrl(offlineMode() ? node.offline_url : node.url);
    if (url) {
      body.append(element("a", { className: "md-button", href: url.href }, "Knoten öffnen"));
    }
    details.hidden = false;
  }

  function renderGraph() {
    const host = root.querySelector("[data-cheat-graph-stage]");
    const status = root.querySelector("[data-cheat-graph-status]");
    if (!host || !status || !state.graph) return;
    host.replaceChildren();

    const visible = visibleNodeIds();
    const selectedNeighborhood = state.selectedId ? adjacentIds(state.selectedId) : null;
    const viewbox = state.graph.viewbox;
    const scaledWidth = viewbox.width / state.scale;
    const scaledHeight = viewbox.height / state.scale;
    const offsetX = (viewbox.width - scaledWidth) / 2;
    const offsetY = (viewbox.height - scaledHeight) / 2;
    const svg = svgElement("svg", {
      viewBox: `${offsetX} ${offsetY} ${scaledWidth} ${scaledHeight}`,
      role: "img",
      "aria-label": "Wissensgraph aus Kategorien, Fachseiten und Tags",
      preserveAspectRatio: "xMidYMid meet",
    });
    const edgeLayer = svgElement("g", {
      class: "cheat-graph-edges",
      "aria-hidden": "true",
    });
    const nodeLayer = svgElement("g", { class: "cheat-graph-nodes" });
    const nodesById = new Map(state.graph.nodes.map((node) => [node.id, node]));

    let visibleEdges = 0;
    for (const edge of state.graph.edges) {
      if (!state.edgeTypes.has(edge.type)) continue;
      if (!visible.has(edge.source) || !visible.has(edge.target)) continue;
      const source = nodesById.get(edge.source);
      const target = nodesById.get(edge.target);
      if (!source || !target) continue;
      const line = svgElement("line", {
        x1: source.x,
        y1: source.y,
        x2: target.x,
        y2: target.y,
        class: `cheat-graph-edge cheat-graph-edge--${edge.type}`,
      });
      if (
        selectedNeighborhood &&
        !(selectedNeighborhood.has(edge.source) && selectedNeighborhood.has(edge.target))
      ) {
        line.classList.add("is-dimmed");
      }
      edgeLayer.append(line);
      visibleEdges += 1;
    }

    let visibleNodes = 0;
    let matches = 0;
    for (const node of state.graph.nodes) {
      if (!visible.has(node.id)) continue;
      const match = nodeMatches(node);
      if (match) matches += 1;
      const url = safeUrl(offlineMode() ? node.offline_url : node.url);
      const wrapper = svgElement(url ? "a" : "g", {
        class: `cheat-graph-node cheat-graph-node--${node.type}`,
        transform: `translate(${node.x} ${node.y})`,
        tabindex: "0",
        role: url ? "link" : "button",
        "aria-label": nodeDescription(node),
      });
      if (url) wrapper.setAttribute("href", url.href);
      if (!match && state.query) wrapper.classList.add("is-dimmed");
      if (node.id === state.selectedId) wrapper.classList.add("is-selected");
      if (selectedNeighborhood && !selectedNeighborhood.has(node.id)) {
        wrapper.classList.add("is-dimmed");
      }
      if (match && state.query) wrapper.classList.add("is-match");
      wrapper.addEventListener("click", (event) => {
        if (!event.metaKey && !event.ctrlKey) {
          event.preventDefault();
          selectNode(node.id);
        }
      });
      wrapper.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectNode(node.id);
        }
      });
      wrapper.addEventListener("focus", () => {
        if (state.selectedId !== node.id) selectNode(node.id);
      });
      wrapper.append(nodeShape(node));
      const title = svgElement("title");
      title.textContent = nodeDescription(node);
      wrapper.append(title);
      const label = svgElement("text", {
        x: 13,
        y: 4,
        class: "cheat-graph-node__label",
      });
      label.textContent = node.label;
      wrapper.append(label);
      nodeLayer.append(wrapper);
      visibleNodes += 1;
    }

    svg.append(edgeLayer, nodeLayer);
    host.append(svg);
    host.hidden = false;
    root.setAttribute("aria-busy", "false");
    const queryText = state.query ? `, ${matches} Suchtreffer` : "";
    status.textContent = `${visibleNodes} Knoten und ${visibleEdges} Beziehungen sichtbar${queryText}.`;
    renderDetails();
  }

  async function initialize() {
    try {
      const response = await fetch(graphSource(), {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const graph = await response.json();
      if (!validGraph(graph)) throw new Error("Ungültiges Wissensgraph-Datenformat");
      state.graph = graph;
      buildControls();
      renderGraph();
      document.documentElement.dataset.cheatsheetGraph = "ready";
    } catch (error) {
      root.setAttribute("aria-busy", "false");
      const status = root.querySelector("[data-cheat-graph-status]");
      if (status) {
        status.textContent =
          "Der Wissensgraph konnte nicht geladen werden. Die normalen Kategorien und Indizes bleiben verfügbar.";
      }
      console.warn("Wissensgraph konnte nicht initialisiert werden.", error);
    }
  }

  initialize();
})();
