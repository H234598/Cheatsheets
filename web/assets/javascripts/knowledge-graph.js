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
    nodeTypes: new Set(Object.keys(TYPE_LABELS)),
    edgeTypes: new Set(["contains", "tagged"]),
    scale: 1,
  };
  const nodeElements = new Map();
  const edgeElements = [];
  let graphSvg = null;

  function htmlElement(tag, attributes = {}, text = "") {
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
    const wrapper = htmlElement("label", { className: "cheat-graph-option" });
    const input = htmlElement("input", { type: "checkbox", name, value });
    input.checked = checked;
    wrapper.append(input, document.createTextNode(label));
    return { input, wrapper };
  }

  function updateViewBox() {
    if (!graphSvg || !state.graph) return;
    const viewbox = state.graph.viewbox;
    const width = viewbox.width / state.scale;
    const height = viewbox.height / state.scale;
    graphSvg.setAttribute(
      "viewBox",
      `${(viewbox.width - width) / 2} ${(viewbox.height - height) / 2} ${width} ${height}`,
    );
  }

  function buildControls() {
    const host = root.querySelector("[data-cheat-graph-controls]");
    if (!host) return;
    host.replaceChildren();
    host.className = "cheat-graph-controls";

    const searchLabel = htmlElement("label", { className: "cheat-graph-search" });
    searchLabel.append(document.createTextNode("Knoten suchen"));
    const search = htmlElement("input", {
      type: "search",
      autocomplete: "off",
      placeholder: "Titel, Alias, Kategorie oder Tag",
      "data-cheat-graph-search": "",
    });
    search.value = state.query;
    search.addEventListener("input", () => {
      state.query = normalized(search.value);
      updatePresentation();
    });
    searchLabel.append(search);

    const nodeFieldset = htmlElement("fieldset");
    nodeFieldset.append(htmlElement("legend", {}, "Knotentypen"));
    for (const [type, label] of Object.entries(TYPE_LABELS)) {
      const option = checkbox("node-type", type, label, state.nodeTypes.has(type));
      option.input.addEventListener("change", () => {
        if (option.input.checked) state.nodeTypes.add(type);
        else state.nodeTypes.delete(type);
        updatePresentation();
      });
      nodeFieldset.append(option.wrapper);
    }

    const edgeFieldset = htmlElement("fieldset");
    edgeFieldset.append(htmlElement("legend", {}, "Beziehungen"));
    for (const [type, label] of Object.entries(EDGE_LABELS)) {
      const option = checkbox("edge-type", type, label, state.edgeTypes.has(type));
      option.input.addEventListener("change", () => {
        if (option.input.checked) state.edgeTypes.add(type);
        else state.edgeTypes.delete(type);
        updatePresentation();
      });
      edgeFieldset.append(option.wrapper);
    }

    const zoom = htmlElement("div", {
      className: "cheat-graph-zoom",
      "aria-label": "Darstellungsgröße",
    });
    const zoomOut = htmlElement("button", { type: "button", className: "md-button" }, "−");
    zoomOut.setAttribute("aria-label", "Graph verkleinern");
    const zoomReset = htmlElement(
      "button",
      { type: "button", className: "md-button" },
      `${Math.round(state.scale * 100)} %`,
    );
    zoomReset.setAttribute("aria-label", "Darstellungsgröße zurücksetzen");
    const zoomIn = htmlElement("button", { type: "button", className: "md-button" }, "+");
    zoomIn.setAttribute("aria-label", "Graph vergrößern");
    const applyScale = (value) => {
      state.scale = Math.min(1.8, Math.max(0.65, value));
      zoomReset.textContent = `${Math.round(state.scale * 100)} %`;
      updateViewBox();
    };
    zoomOut.addEventListener("click", () => applyScale(state.scale - 0.15));
    zoomReset.addEventListener("click", () => applyScale(1));
    zoomIn.addEventListener("click", () => applyScale(state.scale + 0.15));
    zoom.append(zoomOut, zoomReset, zoomIn);

    const reset = htmlElement(
      "button",
      { type: "button", className: "md-button" },
      "Auswahl zurücksetzen",
    );
    reset.addEventListener("click", () => {
      state.query = "";
      state.selectedId = null;
      state.nodeTypes = new Set(Object.keys(TYPE_LABELS));
      state.edgeTypes = new Set(["contains", "tagged"]);
      state.scale = 1;
      buildControls();
      updateViewBox();
      updatePresentation();
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

  function nodeDescription(node) {
    const parts = [TYPE_LABELS[node.type], node.label];
    if (Number.isFinite(node.page_count)) parts.push(`${node.page_count} Fachseiten`);
    if (Number.isFinite(node.minutes)) parts.push(`ca. ${node.minutes} Minuten`);
    return parts.join(" – ");
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
      htmlElement("p", { className: "cheat-graph-details__type" }, TYPE_LABELS[node.type]),
      htmlElement("h3", {}, node.label),
    );
    const facts = htmlElement("dl");
    const addFact = (term, value) => {
      facts.append(htmlElement("dt", {}, term), htmlElement("dd", {}, value));
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
    if (relationText) body.append(htmlElement("p", {}, relationText));

    const url = safeUrl(offlineMode() ? node.offline_url : node.url);
    if (url) {
      body.append(htmlElement("a", { className: "md-button", href: url.href }, "Knoten öffnen"));
    }
    details.hidden = false;
  }

  function selectNode(nodeId) {
    state.selectedId = nodeId;
    updatePresentation();
  }

  function updatePresentation() {
    if (!state.graph) return;
    const status = root.querySelector("[data-cheat-graph-status]");
    const neighborhood = state.selectedId ? adjacentIds(state.selectedId) : null;
    let visibleNodes = 0;
    let matches = 0;

    for (const node of state.graph.nodes) {
      const element = nodeElements.get(node.id);
      if (!element) continue;
      const visible = state.nodeTypes.has(node.type);
      const match = !state.query || normalized(node.search || node.label).includes(state.query);
      element.classList.toggle("is-hidden", !visible);
      element.classList.toggle("is-match", Boolean(state.query && match));
      element.classList.toggle("is-selected", node.id === state.selectedId);
      element.classList.toggle(
        "is-dimmed",
        Boolean((state.query && !match) || (neighborhood && !neighborhood.has(node.id))),
      );
      if (visible) visibleNodes += 1;
      if (visible && match) matches += 1;
    }

    let visibleEdges = 0;
    for (const record of edgeElements) {
      const source = state.graph.nodes.find((node) => node.id === record.edge.source);
      const target = state.graph.nodes.find((node) => node.id === record.edge.target);
      const visible = Boolean(
        source &&
          target &&
          state.edgeTypes.has(record.edge.type) &&
          state.nodeTypes.has(source.type) &&
          state.nodeTypes.has(target.type),
      );
      record.element.classList.toggle("is-hidden", !visible);
      record.element.classList.toggle(
        "is-dimmed",
        Boolean(
          neighborhood &&
            !(neighborhood.has(record.edge.source) && neighborhood.has(record.edge.target)),
        ),
      );
      if (visible) visibleEdges += 1;
    }

    if (status) {
      const queryText = state.query ? `, ${matches} Suchtreffer` : "";
      status.textContent = `${visibleNodes} Knoten und ${visibleEdges} Beziehungen sichtbar${queryText}.`;
    }
    renderDetails();
  }

  function renderGraph() {
    const host = root.querySelector("[data-cheat-graph-stage]");
    if (!host || !state.graph) return;
    host.replaceChildren();
    nodeElements.clear();
    edgeElements.length = 0;

    graphSvg = svgElement("svg", {
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

    for (const edge of state.graph.edges) {
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
      edgeLayer.append(line);
      edgeElements.push({ edge, element: line });
    }

    for (const node of state.graph.nodes) {
      const url = safeUrl(offlineMode() ? node.offline_url : node.url);
      const wrapper = svgElement(url ? "a" : "g", {
        class: `cheat-graph-node cheat-graph-node--${node.type}`,
        transform: `translate(${node.x} ${node.y})`,
        tabindex: "0",
        role: url ? "link" : "button",
        "aria-label": nodeDescription(node),
      });
      if (url) wrapper.setAttribute("href", url.href);
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
      nodeElements.set(node.id, wrapper);
    }

    graphSvg.append(edgeLayer, nodeLayer);
    host.append(graphSvg);
    host.hidden = false;
    root.setAttribute("aria-busy", "false");
    updateViewBox();
    updatePresentation();
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
