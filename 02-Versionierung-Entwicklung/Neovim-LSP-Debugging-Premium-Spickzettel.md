---
title: "Neovim – LSP, Diagnostics, Formatting und Debugging"
aliases: ["Neovim LSP", "nvim-dap", "Neovim Diagnostics"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [neovim, lsp, debugging, formatting, treesitter, dap]
source: "https://neovim.io/doc/user/lsp.html"
---

# Neovim – LSP, Diagnostics, Formatting und Debugging

> [!abstract] Zweck
> Ausführliche Unterseite für Sprachserver, Completion, Diagnostics, Formatting, Code Actions, Treesitter und Debug Adapter Protocol in Neovim – inklusive Diagnosepfaden.

> [!abstract] Architektur
> Neovim enthält einen LSP-Client, aber keinen Sprachserver. Für jede Sprache muss ein passender Server installiert, gestartet und mit Root/Dateityp/Capabilities konfiguriert werden. Completion-UI, Formatter und DAP sind separate Schichten.

## Inhalt

- [[#Schichtenmodell]]
- [[#LSP-Bordmittel]]
- [[#Sprachserver konfigurieren]]
- [[#Bufferlokale Mappings]]
- [[#Diagnostics]]
- [[#Completion]]
- [[#Formatting]]
- [[#Treesitter]]
- [[#Debug Adapter Protocol]]
- [[#Sprachexemplare]]
- [[#Diagnose-Reihenfolge]]

## Schichtenmodell

```text
Datei/Buffer
├── Parser/Highlight: Treesitter
├── Language Intelligence: LSP Server ↔ Neovim LSP Client
│   ├── Definition/References/Hover
│   ├── Diagnostics
│   ├── Rename/Code Actions
│   └── optional Formatting/Completion
├── Completion UI/Snippets
├── Formatter/Linter als eigener Prozess
└── Debugger: DAP Client ↔ Debug Adapter ↔ Programm
```

Fehler immer der richtigen Schicht zuordnen.

## LSP-Bordmittel

Status:

```vim
:checkhealth vim.lsp
:LspInfo
```

Je Neovim-Version können Befehle variieren; Lua-API ist maßgeblich.

Aktive Clients:

```lua
vim.print(vim.lsp.get_clients({ bufnr = 0 }))
```

Bufferdateityp:

```vim
:set filetype?
:lua =vim.api.nvim_buf_get_name(0)
```

Loglevel und Logpfad:

```lua
vim.lsp.set_log_level("debug")
vim.print(vim.lsp.get_log_path())
```

Nach Diagnose Loglevel zurücksetzen, da Logs groß und sensibel werden können.

## Sprachserver konfigurieren

Die konkrete Registrierungs-API hängt von Neovim-Version und Config-Ökosystem ab. Grundelemente bleiben:

```lua
local config = {
  cmd = { "mein-language-server", "--stdio" },
  filetypes = { "meinesprache" },
  root_dir = function(bufnr, on_dir)
    local root = vim.fs.root(bufnr, { ".git", "projekt.toml" })
    if root then on_dir(root) end
  end,
  settings = {},
  capabilities = vim.lsp.protocol.make_client_capabilities(),
}
```

### Root-Erkennung

Root bestimmt Projektkontext, Konfiguration, Indexierung und Workspace. Prüfen:

```lua
vim.print(vim.fs.root(0, { ".git", "pyproject.toml", "Cargo.toml" }))
```

Fehlerhafte zu hohe Root (`$HOME`) führt zu riesiger Indexierung; zu niedrige Root verhindert projektweite Referenzen.

### Serverinstallation

Möglichkeiten:

- Distribution/Systempaket
- Sprachpaketmanager (`npm`, `pipx`, `cargo`, `gem`, `go install`)
- Toolmanager/Plugin
- projektlokale Toolchain

Produktiv reproduzierbare Versionen und Vertrauensquelle dokumentieren. PATH in GUI/Terminal kann unterschiedlich sein.

```vim
:echo executable('rust-analyzer')
:echo exepath('rust-analyzer')
```

## Bufferlokale Mappings

Bei Attach:

```lua
vim.api.nvim_create_autocmd("LspAttach", {
  callback = function(args)
    local bufnr = args.buf
    local map = function(lhs, rhs, desc)
      vim.keymap.set("n", lhs, rhs, { buffer = bufnr, desc = desc })
    end

    map("gd", vim.lsp.buf.definition, "Definition")
    map("gD", vim.lsp.buf.declaration, "Deklaration")
    map("gr", vim.lsp.buf.references, "Referenzen")
    map("gi", vim.lsp.buf.implementation, "Implementierung")
    map("K", vim.lsp.buf.hover, "Hover")
    map("<leader>rn", vim.lsp.buf.rename, "Umbenennen")
    map("<leader>ca", vim.lsp.buf.code_action, "Code Action")
    map("<leader>ds", vim.lsp.buf.document_symbol, "Dokumentsymbole")
  end,
})
```

`gr*`-Standardmappings können je Neovim-Version bereits existieren. Vor Überschreiben `:verbose nmap gr` prüfen.

## Diagnostics

Navigation:

```lua
vim.diagnostic.jump({ count = 1, float = true })
vim.diagnostic.jump({ count = -1, float = true })
vim.diagnostic.open_float()
vim.diagnostic.setloclist()
```

Mappings:

```lua
vim.keymap.set("n", "]d", function()
  vim.diagnostic.jump({ count = 1, float = true })
end, { desc = "Nächste Diagnose" })

vim.keymap.set("n", "[d", function()
  vim.diagnostic.jump({ count = -1, float = true })
end, { desc = "Vorherige Diagnose" })
```

Darstellung:

```lua
vim.diagnostic.config({
  virtual_text = { spacing = 2, prefix = "●" },
  signs = true,
  underline = true,
  update_in_insert = false,
  severity_sort = true,
  float = { border = "rounded", source = "if_many" },
})
```

Nur Fehler in Location List:

```lua
vim.diagnostic.setloclist({ severity = vim.diagnostic.severity.ERROR })
```

Diagnosen stammen eventuell aus mehreren Quellen (LSP, Linter). Namespace und Duplikate prüfen:

```lua
vim.print(vim.diagnostic.get_namespaces())
vim.print(vim.diagnostic.get(0))
```

## Completion

LSP liefert Completionitems; eine Completion-UI übernimmt Trigger, Auswahl, Sortierung, Snippets und Bestätigung.

Grundfragen:

- Client unterstützt Completion?
- Client-Capabilities wurden mit Completionplugin erweitert?
- Server attached?
- Insert Completion manuell mit `Ctrl-X Ctrl-O`?
- Snippetengine korrekt?
- Mapping für Tab/Enter kollidiert?

Bordmittel:

```text
Ctrl-X Ctrl-O   Omni-Completion
Ctrl-N/P        Auswahl
Ctrl-Y          bestätigen, kontextabhängig
Ctrl-E          abbrechen
```

Completion nicht automatisch bei jedem Zeichen erzwingen, wenn Latenz/Noise stört.

## Formatting

LSP:

```lua
vim.lsp.buf.format({
  async = false,
  timeout_ms = 3000,
})
```

Bestimmten Client filtern:

```lua
vim.lsp.buf.format({
  filter = function(client)
    return client.name == "gewünschter-formatter"
  end,
})
```

### Format on Save

```lua
vim.api.nvim_create_autocmd("BufWritePre", {
  pattern = { "*.lua", "*.rs" },
  callback = function(args)
    vim.lsp.buf.format({ bufnr = args.buf, timeout_ms = 2000 })
  end,
})
```

> [!warning]
> Format-on-save kann blockieren, unerwartete Großdiffs erzeugen oder zwei Formatter konkurrieren lassen. Pro Dateityp genau eine Quelle festlegen, Timeout verwenden und Projektkonfiguration versionieren.

Externe Formatter über Plugin oder `:!`/`formatprg` integrieren. Beispiele:

```vim
:setlocal formatprg=black\ -q\ -
```

Praktischer sind Tools, die stdin/stdout, Range und Exitcodes sauber handhaben.

### Mehrere LSP-Clients

```lua
for _, client in ipairs(vim.lsp.get_clients({ bufnr = 0 })) do
  print(client.name, client:supports_method("textDocument/formatting"))
end
```

Formattingfähigkeit unerwünschten Clients deaktivieren oder per Filter auswählen.

## Treesitter

Treesitter stellt Syntaxbaum-basierte Funktionen bereit:

- Highlighting
- Einrückung, je Sprache/Qualität
- Textobjekte mit Plugin
- Folds
- strukturelle Auswahl

Parserstatus hängt von installiertem Parser und Neovim-Kompatibilität ab.

Diagnose:

```vim
:checkhealth nvim-treesitter
:set filetype?
:Inspect
:InspectTree
```

Fallback: Treesitter-Highlighting für problematische Sprache deaktivieren und klassisches Syntaxhighlighting nutzen.

> [!note]
> Treesitter ist kein LSP. Es kennt lokale Syntaxstruktur, aber nicht automatisch projektweite Typen, Definitionen oder Builds.

## Debug Adapter Protocol

DAP-Schichten:

```text
nvim-dap (Client)
  ↕ DAP
Debug Adapter, z. B. debugpy/codelldb/js-debug
  ↕ Debugger/Runtime
Programm
```

Typischer Workflow:

```text
Breakpoint setzen
→ Konfiguration wählen
→ Start/Continue
→ Step over/into/out
→ Variablen/Scopes/Stack prüfen
→ REPL/Evaluate
→ Stop/Terminate
```

Übliche Mappings, selbst definieren:

```lua
local dap = require("dap")
vim.keymap.set("n", "<F5>", dap.continue)
vim.keymap.set("n", "<F10>", dap.step_over)
vim.keymap.set("n", "<F11>", dap.step_into)
vim.keymap.set("n", "<F12>", dap.step_out)
vim.keymap.set("n", "<leader>db", dap.toggle_breakpoint)
vim.keymap.set("n", "<leader>dB", function()
  dap.set_breakpoint(vim.fn.input("Bedingung: "))
end)
```

> [!warning]
> Debugadapter und Programm laufen mit Benutzerrechten und können beliebigen Projektcode ausführen. Untrusted Repositorys isolieren.

### DAP-Diagnose

- Adapter executable/path?
- Port/stdio-Modus korrekt?
- Launch versus Attach?
- Programmpfad und `cwd`?
- Debugbuild/Symbole vorhanden?
- Source Map/Path Mapping?
- Runtime/venv/Toolchain korrekt?
- Adapterlog aktivieren.

## Sprachexemplare

### Python

Serveroptionen: Pyright-basierte oder andere LSPs. Wichtig:

```bash
which python
python -c 'import sys; print(sys.executable)'
```

LSP muss venv/Interpreter des Projekts erkennen. Formatter/Linter z. B. Ruff/Black nach Teamstandard. Debugadapter häufig `debugpy`.

### Rust

```bash
rust-analyzer --version
cargo check
```

Root über `Cargo.toml`; Proc-Macro/Buildscript und Features beeinflussen Analyse. Formatter `rustfmt`, Linter `clippy`, Debugger codelldb/lldb/gdb je Plattform.

### Lua/Neovim

Language Server benötigt Wissen über `vim`-Globals und Runtimebibliothek. Projektkonfiguration oder Neovim-spezifische Bibliotheksintegration setzen, statt undefined-global-Warnungen pauschal global zu deaktivieren.

### Web/TypeScript

Projektlokales `node_modules/.bin` und `tsconfig.json` beachten. Mehrere Server/Formatter können konkurrieren; ESLint, TypeScript LSP und Prettier-Aufgaben sauber trennen.

## Diagnose-Reihenfolge

### LSP attached nicht

```vim
:set filetype?
:echo executable('server-name')
:LspInfo
:checkhealth vim.lsp
:messages
```

Dann:

1. `cmd` direkt im Terminal ausführen.
2. Root-Erkennung anzeigen.
3. Dateityp gegen Konfiguration vergleichen.
4. Serverlog/LSP-Log prüfen.
5. minimal mit einem Server und ohne Completionplugin testen.
6. PATH aus Neovim mit Shell vergleichen.

### Definition/Hover funktioniert nicht

- Client attached?
- Server unterstützt Methode?
- Datei im Projekt/Root?
- Indexierung fertig?
- Code kompiliert/Abhängigkeiten installiert?
- korrekte Features/venv/SDK?

```lua
local clients = vim.lsp.get_clients({ bufnr = 0 })
for _, client in ipairs(clients) do
  print(client.name, client:supports_method("textDocument/definition"))
end
```

### Doppelte Diagnosen/Formatierung

```lua
vim.print(vim.lsp.get_clients({ bufnr = 0 }))
vim.print(vim.diagnostic.get_namespaces())
```

Linter/LSP/Formatterinventar pro Dateityp erstellen und Zuständigkeit festlegen.

### Minimaltest

`/tmp/minimal.lua`:

```lua
vim.opt.number = true
vim.lsp.set_log_level("debug")
-- genau eine Serverkonfiguration laden
```

```bash
nvim -u /tmp/minimal.lua projekt/datei
```

### Universelle Befehle

```vim
:checkhealth
:messages
:LspInfo
:verbose set filetype?
:verbose nmap gd
:lua =vim.lsp.get_clients({bufnr=0})
:lua =vim.lsp.get_log_path()
```

## Quellen
- [Neovim LSP](https://neovim.io/doc/user/lsp.html)
- [Neovim Diagnostics](https://neovim.io/doc/user/diagnostic.html)
- [Neovim Treesitter](https://neovim.io/doc/user/treesitter.html)
- [Debug Adapter Protocol](https://microsoft.github.io/debug-adapter-protocol/)

## Verwandte Notizen
- [[Neovim-Premium-Spickzettel]]
- [[Neovim-Konfiguration-und-Plugins-Premium-Spickzettel]]
- [[Python-3-Premium-Spickzettel]]
- [[Rust-Premium-Spickzettel]]
