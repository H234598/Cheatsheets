---
title: "Neovim – Konfiguration und Plugins"
aliases: ["init.lua", "Neovim Lua Config", "Neovim Plugins"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [neovim, lua, configuration, plugins, keymaps]
source: "https://neovim.io/doc/user/lua-guide.html"
---

# Neovim – Konfiguration und Plugins

> [!abstract] Zweck
> Ausführliche Unterseite für eine wartbare Neovim-Lua-Konfiguration: Verzeichnisstruktur, Optionen, Keymaps, Autocommands, Filetype, Pluginmanagement, Lazy Loading, Colors, Statusline, Sessions und Fehleranalyse.

> [!important]
> Eine gute Neovim-Konfiguration ist klein startfähig, modular, versionskontrolliert und mit `nvim --clean` beziehungsweise minimaler `init.lua` diagnostizierbar. Plugins ergänzen den Editor; sie sollten grundlegende Bedienung nicht vollständig verdecken.

## Inhalt

- [[#Konfigurationspfade]]
- [[#Empfohlene Struktur]]
- [[#Optionen]]
- [[#Keymaps]]
- [[#Autocommands und Filetypes]]
- [[#Lua und Neovim-API]]
- [[#Plugins und Paketmanagement]]
- [[#Lazy Loading und Abhängigkeiten]]
- [[#Beispielkonfiguration]]
- [[#Versionierung und Lockfiles]]
- [[#Performance und Diagnose]]

## Konfigurationspfade

Pfad anzeigen:

```vim
:echo stdpath('config')
:echo stdpath('data')
:echo stdpath('state')
:echo stdpath('cache')
```

Typisch unter Linux:

```text
~/.config/nvim/
~/.local/share/nvim/
~/.local/state/nvim/
~/.cache/nvim/
```

Windows typischerweise unter `%LOCALAPPDATA%\nvim`, genaue Pfade mit `stdpath()` prüfen.

Startdateien:

```text
init.lua    empfohlen für Lua-Konfiguration
init.vim    Vimscript, alternativ
```

Neovim lädt nicht beide als gleichwertige Hauptkonfiguration.

## Empfohlene Struktur

```text
~/.config/nvim/
├── init.lua
├── lua/
│   └── config/
│       ├── options.lua
│       ├── keymaps.lua
│       ├── autocmds.lua
│       ├── lazy.lua
│       └── plugins/
│           ├── editor.lua
│           ├── lsp.lua
│           └── ui.lua
├── after/
│   └── ftplugin/
│       ├── python.lua
│       └── markdown.lua
└── spell/
```

`init.lua`:

```lua
require("config.options")
require("config.keymaps")
require("config.autocmds")
require("config.lazy")
```

## Optionen

### Solide Basis

```lua
local opt = vim.opt

opt.number = true
opt.relativenumber = true
opt.cursorline = true
opt.signcolumn = "yes"
opt.wrap = false
opt.scrolloff = 6
opt.sidescrolloff = 8

opt.expandtab = true
opt.shiftwidth = 2
opt.tabstop = 2
opt.softtabstop = 2
opt.smartindent = true

opt.ignorecase = true
opt.smartcase = true
opt.incsearch = true
opt.hlsearch = true

opt.splitright = true
opt.splitbelow = true
opt.undofile = true
opt.swapfile = true
opt.backup = false
opt.writebackup = true
opt.updatetime = 300
opt.timeoutlen = 500
opt.completeopt = { "menu", "menuone", "noselect" }
opt.termguicolors = true
```

> [!warning]
> Optionen nicht blind kopieren. `wrap`, Swap/Backup, Clipboard, Undo, Einrückung und Mouse sind persönliche beziehungsweise betriebliche Entscheidungen. Datenschutz bei persistentem Undo/Swap bedenken.

Option prüfen:

```vim
:set number?
:verbose set number?
```

Lua:

```lua
print(vim.inspect(vim.opt.number:get()))
```

### Lokale Optionen

```lua
vim.opt_local.shiftwidth = 4
vim.bo.textwidth = 88
vim.wo.wrap = true
```

- `vim.o`: globale Option
- `vim.bo`: bufferlokal
- `vim.wo`: fensterlokal
- `vim.opt`: komfortabler Optionwrapper
- `vim.opt_local`: lokale Instanz

## Keymaps

Leader früh setzen:

```lua
vim.g.mapleader = " "
vim.g.maplocalleader = ","
```

Mapping:

```lua
local map = vim.keymap.set

map("n", "<leader>w", "<cmd>write<cr>", { desc = "Datei speichern" })
map("n", "<leader>q", "<cmd>quit<cr>", { desc = "Fenster schließen" })
map("n", "<Esc>", "<cmd>nohlsearch<cr>")
map("v", "<", "<gv", { desc = "Ausrücken und Auswahl behalten" })
map("v", ">", ">gv", { desc = "Einrücken und Auswahl behalten" })
```

Lua-Funktion:

```lua
map("n", "<leader>p", function()
  print(vim.fn.expand("%:p"))
end, { desc = "Dateipfad anzeigen" })
```

Bufferlokal:

```lua
vim.keymap.set("n", "K", vim.lsp.buf.hover, {
  buffer = bufnr,
  desc = "LSP Hover",
})
```

Mapping prüfen:

```vim
:nmap <leader>w
:verbose nmap <leader>w
```

### Nichtrekursiv und silent

`vim.keymap.set` ist standardmäßig nichtrekursiv. `silent` nur setzen, wenn Befehlsausgabe nicht gebraucht wird.

```lua
map("n", "<leader>x", "<cmd>cclose<cr>", { silent = true, desc = "Quickfix schließen" })
```

> [!tip]
> Jedes wichtige Mapping mit `desc` versehen. Das hilft Dokumentation, Suchplugins und `:map`-Analyse.

## Autocommands und Filetypes

Gruppe erstellen, damit Reload keine Duplikate erzeugt:

```lua
local group = vim.api.nvim_create_augroup("UserConfig", { clear = true })

vim.api.nvim_create_autocmd("TextYankPost", {
  group = group,
  callback = function()
    vim.highlight.on_yank({ timeout = 150 })
  end,
})
```

Leerzeichen entfernen – nur wenn Projektpolitik passt:

```lua
vim.api.nvim_create_autocmd("BufWritePre", {
  group = group,
  pattern = { "*.lua", "*.py", "*.rs" },
  callback = function(args)
    local view = vim.fn.winsaveview()
    vim.cmd([[silent! keeppatterns %s/\s\+$//e]])
    vim.fn.winrestview(view)
  end,
})
```

> [!warning]
> Autoformat/Whitespace-Änderungen können große Diffs erzeugen. Nur für definierte Dateitypen/Projekte und mit Versionierung einsetzen.

### Filetype-Plugin

`after/ftplugin/python.lua`:

```lua
vim.opt_local.shiftwidth = 4
vim.opt_local.tabstop = 4
vim.opt_local.textwidth = 88
vim.opt_local.colorcolumn = "89"
```

Mit Undo für Settings bei Bufferwechsel:

```lua
vim.b.undo_ftplugin = (vim.b.undo_ftplugin or "") ..
  " | setlocal shiftwidth< tabstop< textwidth< colorcolumn<"
```

Autocommands prüfen:

```vim
:autocmd UserConfig
:verbose autocmd BufWritePre
```

## Lua und Neovim-API

### Nützliche Namespaces

| API | Zweck |
|---|---|
| `vim.api` | niedrige Neovim-API |
| `vim.fn` | Vimscript-Funktionen |
| `vim.opt` | Optionen |
| `vim.keymap` | Mappings |
| `vim.diagnostic` | Diagnosen |
| `vim.lsp` | LSP-Client |
| `vim.loop`/`vim.uv` | libuv-Zugriff, Version beachten |
| `vim.notify` | Benachrichtigung |

Inspect:

```lua
vim.print(vim.api.nvim_get_current_buf())
vim.print(vim.fn.getcwd())
vim.print(vim.api.nvim_buf_get_lines(0, 0, -1, false))
```

Command definieren:

```lua
vim.api.nvim_create_user_command("CopyPath", function()
  local path = vim.fn.expand("%:p")
  vim.fn.setreg("+", path)
  vim.notify("Kopiert: " .. path)
end, { desc = "Aktuellen Dateipfad kopieren" })
```

Reload eines Moduls:

```lua
package.loaded["config.options"] = nil
require("config.options")
```

Komplette Konfiguration live neu laden kann Autocommands, Mappings und Pluginzustände duplizieren. Häufig zuverlässiger: Neovim neu starten.

## Plugins und Paketmanagement

Neovim unterstützt native `pack/*/start`- und `opt`-Pakete. Viele Nutzer verwenden einen Pluginmanager für Lockfile, Lazy Loading und Updates.

### Native Paketstruktur

```text
~/.local/share/nvim/site/pack/vendor/start/plugin-name/
~/.local/share/nvim/site/pack/vendor/opt/plugin-name/
```

Optional laden:

```vim
:packadd plugin-name
```

### Beispiel mit lazy.nvim

Bootstrap:

```lua
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup("config.plugins", {
  lockfile = vim.fn.stdpath("config") .. "/lazy-lock.json",
  change_detection = { notify = false },
})
```

> [!warning]
> Bootstrap führt externen Git-Code aus. Repository, Pin/Branch, Netzwerkfehler und Supply-Chain-Risiko beachten. In kontrollierten Umgebungen Plugins spiegeln oder auf geprüfte Commits pinnen.

Plugin-Spec:

```lua
return {
  {
    "nvim-lua/plenary.nvim",
    lazy = true,
  },
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    event = { "BufReadPost", "BufNewFile" },
    opts = {
      highlight = { enable = true },
      indent = { enable = true },
    },
  },
}
```

## Lazy Loading und Abhängigkeiten

Mögliche Trigger:

- `event`: `BufReadPost`, `InsertEnter`
- `cmd`: erst bei Ex-Befehl
- `keys`: erst bei Mapping
- `ft`: Dateityp
- `dependencies`: abhängige Plugins

Nicht überoptimieren:

- Kernfunktionen müssen deterministisch verfügbar sein.
- zu spätes Laden erzeugt Race Conditions/fehlende Mappings.
- Startzeit messen, nicht nach Gefühl.
- Plugininterne Lazy-Mechanismen und Manager nicht doppelt komplizieren.

Spec mit Tasten:

```lua
{
  "plugin/selector",
  cmd = "Selector",
  keys = {
    { "<leader>ff", "<cmd>Selector files<cr>", desc = "Dateien suchen" },
  },
  opts = {},
}
```

## Beispielkonfiguration

`init.lua` in kompakt:

```lua
vim.g.mapleader = " "

vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.signcolumn = "yes"
vim.opt.undofile = true
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.splitright = true
vim.opt.splitbelow = true

vim.keymap.set("n", "<leader>w", "<cmd>write<cr>", { desc = "Speichern" })
vim.keymap.set("n", "<leader>e", "<cmd>Explore<cr>", { desc = "Dateibrowser" })

local augroup = vim.api.nvim_create_augroup("MinimalConfig", { clear = true })
vim.api.nvim_create_autocmd("TextYankPost", {
  group = augroup,
  callback = function() vim.highlight.on_yank() end,
})
```

Diese Konfiguration funktioniert ohne Plugins und ist gute Rettungsbasis.

## Versionierung und Lockfiles

Repository:

```bash
cd ~/.config/nvim
git init
git add init.lua lua after
git commit -m 'chore: Neovim-Konfiguration initialisieren'
```

Versionieren:

- Config-Code
- Plugin-Lockfile
- Formatter/Linter-Konfiguration
- README mit Voraussetzungen
- optional Installskript

Nicht versionieren:

- Cache, Swap, Undo, Logs
- lokale Secrets/Tokens
- maschinenspezifische Pfade ohne Abstraktion
- Plugin-Checkout, wenn Manager ihn reproduziert

Hostlokal:

```lua
local ok, local_config = pcall(require, "config.local")
if ok and type(local_config.setup) == "function" then
  local_config.setup()
end
```

`lua/config/local.lua` in `.gitignore` aufnehmen, aber keine geheimen Daten in Lua-Logs/Fehlern exponieren.

## Performance und Diagnose

### Startzeit

```bash
nvim --startuptime startup.log +qa
sort -nr -k2 startup.log | head -30
```

Pluginmanager-Profiler zusätzlich nutzen, aber Neovim-Startlog bleibt neutraler Ausgangspunkt.

### Fehlerquelle finden

```bash
nvim --clean
nvim -u /tmp/minimal.lua
```

Binäre Suche:

1. Hälfte der Plugin-Specs deaktivieren.
2. reproduzieren.
3. problematische Hälfte weiter halbieren.
4. minimalen reproduzierbaren Fall erstellen.

### Runtime und Mapping

```vim
:scriptnames
:set runtimepath?
:verbose nmap <leader>ff
:verbose set formatoptions?
:verbose autocmd BufWritePre
```

### Lua-Fehlerlog

```vim
:messages
:checkhealth
```

Headless:

```bash
nvim --headless -u ~/.config/nvim/init.lua '+lua print("ok")' +qa
```

### Pluginupdate bricht Config

1. Lockfile sichern/committen.
2. Update-Diff und Changelog lesen.
3. auf vorherige Lockfile-Version zurücksetzen.
4. Config an neue API anpassen und Tests durchführen.
5. Updates in kleinen Batches, nicht alle unkontrolliert.

### Sicherheitscheck

- Plugins sind Code mit Benutzerrechten.
- Install-/Buildhooks prüfen.
- untrusted Projektdateien nicht automatisch sourcen.
- Modelines und exrc-Verhalten kennen.
- LSP/Formatter können Projektcode/Config ausführen.
- Secrets nicht in Config, Befehlsverlauf oder Diagnoseausgabe.

## Quellen
- [Neovim Lua Guide](https://neovim.io/doc/user/lua-guide.html)
- [Neovim Options](https://neovim.io/doc/user/options.html)
- [Neovim Autocommands](https://neovim.io/doc/user/autocmd.html)
- [Neovim Packages](https://neovim.io/doc/user/repeat.html#packages)

## Verwandte Notizen
- [[Neovim-Premium-Spickzettel]]
- [[Neovim-Shortcuts-und-Bewegungen]]
- [[Neovim-LSP-Debugging-Premium-Spickzettel]]
- [[Git-Premium-Spickzettel]]
