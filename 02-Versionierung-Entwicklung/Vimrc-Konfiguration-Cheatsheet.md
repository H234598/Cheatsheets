---
title: ".vimrc – Konfiguration und Praxis"
aliases:
  - ".vimrc"
  - "_vimrc"
  - "Vimrc-Konfiguration"
  - "Vimscript-Konfiguration"
created: '2026-10-12'
modified: '2026-10-12'
date: '2026-10-12'
type: reference
status: fertig
tags:
  - vim
  - vimrc
  - vimscript
  - editor
  - konfiguration
  - keymaps
  - plugins
updates:
  - date: '2026-10-12'
    change: "Erstveröffentlichung mit Basisdatei, Dateitypregeln, optionalem Undo, Plattformhinweisen und offizieller Referenz."
source: "https://vimhelp.org/usr_05.txt.html"
---

# .vimrc – Konfiguration und Praxis

> [!abstract] Zweck
> Eine verständliche, wartbare Konfiguration für **Vim 9.x**: richtige Datei finden, eine vollständige Basis übernehmen, Optionen und Tastenkürzel gezielt ändern und Fehler nachvollziehbar eingrenzen. Alle Konfigurationsbeispiele verwenden **klassisches Vimscript**.

> [!info] Geltungsbereich
> Ausgangspunkt ist eine reguläre Vim-Installation mit Skriptunterstützung und zugehörigen Runtime-Dateien. Kleine Rettungsinstallationen können Funktionen weglassen. `:version` zeigt den tatsächlichen Build; dessen lokale `:help` ist für verfügbare Optionen maßgeblich. Die Bedienung behandelt [[Vim-Cheatsheet]]; Neovims `init.lua` steht in [[Neovim-Konfiguration-und-Plugins-Cheatsheet]].

## Inhalt

- [[#Die tatsächlich verwendete Datei finden]]
- [[#Kopierbare Basis-vimrc]]
- [[#Startreihenfolge und defaults.vim]]
- [[#Klassisches Vimscript lesen]]
- [[#Optionen und ihre Gültigkeit]]
- [[#Mappings und Leader]]
- [[#Dateitypen und Autocommands]]
- [[#Swap, Backup und persistentes Undo]]
- [[#Zwischenablage gezielt anbinden]]
- [[#Farben, Maus und Terminal]]
- [[#Native Pakete und Plugins]]
- [[#Konfiguration aufteilen]]
- [[#Neuladen und Fehleranalyse]]
- [[#Konfigurationscode und Vertrauen]]
- [[#Quellen]]
- [[#Verwandte Notizen]]

## Die tatsächlich verwendete Datei finden

Zuerst in einem **normal gestarteten Vim** `:echo $MYVIMRC`, `:echo expand('~')` und `:scriptnames` ausführen. So lässt sich erkennen, welche Datei geladen wurde und welches Home-Verzeichnis dieser Prozess verwendet.

| Umgebung | Übliche persönliche Konfiguration | Ergänzungen |
|---|---|---|
| Linux, Unix, macOS-Terminal | `~/.vimrc` oder `~/.vim/vimrc` | Eigene Runtime-Dateien gewöhnlich unter `~/.vim/` |
| Natives Windows-Vim | `$HOME/_vimrc` oder `$HOME/vimfiles/vimrc` | Außerdem existieren weitere Suchpfade, etwa `$VIM/_vimrc` |
| Vim innerhalb von WSL | Linux-Pfade im WSL-Benutzerkonto | Getrennt von einer nativen Windows-Installation |
| Neuere Builds mit XDG-Unterstützung | `$XDG_CONFIG_HOME/vim/vimrc` beziehungsweise dessen Standardpfad | Mit der installierten Hilfe `:help xdg-vimrc` prüfen |

Die üblichen persönlichen Dateien sind Alternativen: Vim lädt beim normalen Suchen die erste passende Datei. Eine bestehende `~/.vimrc` kann deshalb eine andere gewünschte Konfiguration verdecken. Unter Windows Dateiendungen einblenden, damit nicht versehentlich `_vimrc.txt` entsteht.

`$MYVIMRC` kann leer sein, etwa ohne persönliche Konfiguration oder beim Start mit `-u`. Dann direkt den beabsichtigten Pfad öffnen. `:edit $MYVIMRC` erst verwenden, wenn die Variable tatsächlich einen Dateinamen enthält. Die vollständigen Regeln einschließlich `VIMINIT` stehen in der [Vim-Starthilfe](https://vimhelp.org/starting.txt.html#vimrc).

## Kopierbare Basis-vimrc

**Vollständiger Inhalt für eine neue persönliche vimrc.** Eine vorhandene Datei vorher sichern und gezielt ergänzen. Der folgende Block definiert seine Einstellungen selbst; optionale Erweiterungen folgen in eigenen Abschnitten.

```vim
" Basis-vimrc: klassisches Vimscript fuer regulaeres Vim 9.x.
set nocompatible
scriptencoding utf-8

" Leader vor den zugehoerigen Mappings festlegen.
let mapleader = ' '
let maplocalleader = ','

" Anzeige und Fenster.
set number
set ruler
set showcmd
set cursorline
set scrolloff=5
set splitbelow
set splitright

" Bearbeiten und Einruecken.
set backspace=indent,eol,start
set hidden
set autoindent
set expandtab
set shiftwidth=4
set softtabstop=4
set tabstop=8

" Suche und Vervollstaendigung der Befehlszeile.
set incsearch
set hlsearch
set ignorecase
set smartcase
set wildmenu
set wildmode=longest:full,full

" Wiederherstellung und Schutz beim Schreiben erhalten.
set swapfile
set nobackup
set writebackup

" Projektdateien nicht automatisch als Konfiguration ausfuehren.
set noexrc
set nomodeline
if exists('+modelineexpr')
  set nomodelineexpr
endif

" Mitgelieferte Dateityp-, Einrueckungs- und Syntaxregeln.
filetype plugin indent on
if has('syntax')
  syntax enable
endif

" Speichern und Suchmarkierung ausblenden.
nnoremap <Leader>w :write<CR>
nnoremap <silent> <Leader>h :nohlsearch<CR>

" Auswahl nach Ein- oder Ausruecken behalten.
xnoremap < <gv
xnoremap > >gv

" Nur die eigenen Regeln beim erneuten Laden ersetzen.
augroup UserVimrc
  autocmd!
  autocmd FileType python setlocal expandtab shiftwidth=4 softtabstop=4 tabstop=8
  autocmd FileType yaml setlocal expandtab shiftwidth=2 softtabstop=2
  autocmd FileType make setlocal noexpandtab shiftwidth=8 softtabstop=0 tabstop=8
augroup END
```

Danach speichern, Vim neu starten und `:messages` prüfen. Mit `Leertaste`, danach `w`, wird gespeichert; `Leertaste`, danach `h`, blendet die aktuellen Suchmarkierungen aus.

Die Basis installiert keine zusätzlichen Pakete. `filetype plugin indent on` aktiviert die mitgelieferten Mechanismen. Die Einrückungsbreiten sind ein Ausgangspunkt; Projektvorgaben bleiben maßgeblich. Klassische Make-Rezepte erhalten echte Tabulatoren. `tabstop=8` steuert deren Darstellung, während `shiftwidth` und `softtabstop` die gewählte Einrückung bestimmen. Die Python-Regel setzt auch `tabstop` ausdrücklich, damit eine abweichende Vorgabe des mitgelieferten Python-Plugins diesen Wert nicht verändert.

`hidden` erlaubt ungesicherte Buffer im Hintergrund. Das ist **kein automatisches Speichern**: `:ls` zeigt den Zustand, `:wall` schreibt geänderte Buffer, und `:qa` weist auf verbliebene Änderungen hin. Weitere Erläuterungen: [Vim-Einstellungen](https://vimhelp.org/usr_05.txt.html), [Dateien wechseln](https://vimhelp.org/usr_07.txt.html).

## Startreihenfolge und defaults.vim

Bei einem normalen Terminalstart ist folgende Reihenfolge für die Fehlersuche hilfreich:

| Phase | Was Einstellungen beeinflussen kann |
|---|---|
| Frühe Initialisierung | Eingebaute Werte, Startargumente, `--cmd` |
| Grundkonfiguration | System-vimrc, danach persönliche Konfiguration oder alternative Initialisierung |
| Erweiterungen | Runtime-Plugins, automatisch geladene Pakete, `after/`-Dateien |
| Geöffnete Dateien | Dateityperkennung, Filetype-Plugins, Einrückungsskripte, eigene Ereignisregeln |
| Abschluss | `-c`-Befehle und `VimEnter` |

Spätere Skripte können frühere Einstellungen überschreiben. Die tatsächlich ausgeführten Dateien zeigt `:scriptnames`; bei einer konkreten Option hilft beispielsweise `:verbose setlocal shiftwidth?`. Details: [Initialisierung](https://vimhelp.org/starting.txt.html#initialization).

### Warum eine leere vimrc das Verhalten verändert

Ohne eigene vimrc kann Vim `$VIMRUNTIME/defaults.vim` laden. Sobald eine persönliche vimrc existiert, erfolgt dieser automatische Rückgriff nicht mehr. Wer die mitgelieferten Vorgaben übernehmen möchte, setzt nahe an den Anfang:

```vim
unlet! skip_defaults_vim
source $VIMRUNTIME/defaults.vim

" Eigene Abweichungen erst danach.
set number
```

`defaults.vim` setzt auch Bedienverhalten und Mappings. Den Inhalt bei Bedarf mit `:edit $VIMRUNTIME/defaults.vim` ansehen. Die oben angebotene Basis ist bereits eigenständig; für sie ist dieser Zusatz nicht erforderlich. [Erklärung von defaults.vim](https://vimhelp.org/usr_05.txt.html#defaults.vim-explained), [offizieller Skriptquelltext](https://github.com/vim/vim/blob/master/runtime/defaults.vim).

## Klassisches Vimscript lesen

Befehle stehen in der Datei gewöhnlich **ohne führenden Doppelpunkt**. `"` beginnt einen Kommentar; einfache Zeichenketten verwenden `'...'`. In doppelten Anführungszeichen werden Escape-Sequenzen ausgewertet.

```vim
" Option.
set number

" Globale Variable und skriptlokale Variable.
let g:mein_projektmodus = 1
let s:config_dir = expand('~/.vim')

" Nur ausfuehren, wenn die Option verfuegbar ist.
if exists('+relativenumber')
  set relativenumber
endif
```

| Schreibweise | Bedeutung |
|---|---|
| `g:name` | Globale Variable |
| `s:name` | Variable innerhalb dieses Skripts |
| `b:name` | Variable des aktuellen Buffers |
| `w:name` | Variable des aktuellen Fensters |
| `&option` | Wert einer Editoroption |
| `has('merkmal')` | Merkmal des Builds oder der Laufzeit prüfen |
| `exists('+option')` | Nutzbarkeit einer Option prüfen |
| `exists('*Funktion')` | Vorhandensein einer Funktion prüfen |

Vim 9 unterstützt weiterhin klassisches Vimscript. Die Zeile `vim9script` schaltet auf eine andere Skriptsprache um; sie gehört **nicht** vor die Beispiele dieser Seite. `vim.opt` und `vim.keymap.set` sind wiederum Neovim-Lua-APIs. [Vimscript](https://vimhelp.org/usr_41.txt.html), [Featureprüfungen](https://vimhelp.org/builtin.txt.html#has()), [Vim9-Sprache](https://vimhelp.org/vim9.txt.html).

## Optionen und ihre Gültigkeit

### Einstellungen prüfen und ändern

| Befehl | Wirkung |
|---|---|
| `:set number` | Zeilennummern aktivieren |
| `:set nonumber` | Zeilennummern deaktivieren |
| `:set number!` | Boolean umschalten; für interaktive Nutzung |
| `:set number?` | Aktuellen Wert anzeigen |
| `:verbose set number?` | Zusätzlich die letzte bekannte Herkunft anzeigen |
| `:set shiftwidth=4` | Zahlenwert setzen |
| `:set wildignore+=*.o` | Eintrag ergänzen |
| `:set wildignore-=*.o` | Eintrag entfernen |
| `:setlocal shiftwidth<` | Lokalen Wert auf die globale Vorgabe zurücksetzen |

In wiederholt geladenen Dateien feste Werte verwenden. `set number!` würde bei jedem Laden erneut umschalten.

### Global, bufferlokal und fensterlokal

`:set` setzt bei gewöhnlichen lokalen Optionen den aktuellen Wert und ihre Vorgabe. `:setlocal` ändert gezielt den aktuellen Buffer beziehungsweise das Fenster; `:setglobal` die globale Vorgabe. Eine rein globale Option wird durch `:setlocal` nicht lokal.

```vim
" Allgemeine Vorgabe.
set shiftwidth=4

" Nur dieser Buffer.
setlocal shiftwidth=2

" Nur dieses Fenster.
setlocal nowrap
```

Einige Optionen sind ausdrücklich `global-local` und besitzen zusätzliche Vererbungsregeln. Bei Unklarheiten `:help 'optionsname'` lesen. Die Referenz erläutert [lokale Optionen](https://vimhelp.org/options.txt.html#local-options).

### Bewusste Entscheidungen

| Einstellung | Praktische Entscheidung |
|---|---|
| `expandtab` | Neu eingegebene Einrückung als Leerzeichen; ändert vorhandene Tabs nicht rückwirkend |
| `tabstop` | Anzeige vorhandener Tabs; nicht mit Einrückungsbreite gleichsetzen |
| `shiftwidth` | Breite von Einrückungsoperationen wie `>>` |
| `softtabstop` | Verhalten von Tab und Backspace beim Einfügen |
| `wrap` / `nowrap` | Lange Zeilen am Fenster umbrechen oder horizontal anzeigen |
| `ignorecase smartcase` | Suchmuster ohne Großbuchstaben toleranter behandeln |
| `textwidth` | Automatische beziehungsweise angeforderte Textformatierung beeinflussen |
| `formatoptions` | Unter anderem Kommentarfortsetzung und Umbruchverhalten steuern |

Eine vimrc legt Verhalten fest; sie sollte nicht beim Speichern ungefragt komplette Dateien umformatieren. Solche Eingriffe getrennt pro Projekt einrichten und ihre Diffs prüfen. [Einfügen und Einrücken](https://vimhelp.org/insert.txt.html), [Einstellungsbeispiele](https://vimhelp.org/usr_05.txt.html).

## Mappings und Leader

`<Leader>` wird **bei Definition des Mappings** durch den damaligen Wert von `mapleader` ersetzt. Ohne eigene Festlegung ist der Leader gewöhnlich der Backslash. Nach einem Wechsel des Leaders Vim neu starten; bereits vorhandene Mappings wechseln nicht nachträglich ihren Präfix.

| Befehl | Gültigkeit |
|---|---|
| `nnoremap` | Normalmodus |
| `inoremap` | Einfügemodus |
| `xnoremap` | Visueller Modus |
| `cnoremap` | Befehlszeile |
| `<buffer>` | Mapping auf diesen Buffer beschränken |
| `<silent>` | Anzeige des ausgeführten Mappings unterdrücken |

`noremap`-Varianten vermeiden normalerweise das erneute Interpretieren der rechten Seite als Benutzermapping. Unbeabsichtigte Mapping-Ketten werden damit seltener.

```vim
" Nur im Normalmodus: aktuelle Datei speichern.
nnoremap <Leader>w :write<CR>

" Ergebnisliste schliessen.
nnoremap <silent> <Leader>c :cclose<CR>

" Bereits vorhandenes Mapping und seine Herkunft anzeigen.
:verbose nmap <Leader>w
```

Kommentare vor Mappings auf eine eigene Zeile setzen: Angehängter Text kann sonst Teil der rechten Seite werden. Unterscheide `<CR>` als ausgeschriebenes Tastensymbol von einem tatsächlichen Zeilenumbruch. `timeoutlen` beeinflusst die Wartezeit auf eine vollständige Tastenkombination. [Mapping-Referenz](https://vimhelp.org/map.txt.html), [eigene Befehle und Tastenkürzel](https://vimhelp.org/usr_40.txt.html).

## Dateitypen und Autocommands

Die Basis verwendet `FileType`, weil die Regel den **erkannten Dateityp** betrifft. Ein Dateityp ist kein Dateiname: Das Muster `python` gehört zu `FileType`; `*.py` passt zu Dateiereignissen wie `BufRead`.

```vim
:filetype
:setlocal filetype?
:verbose setlocal expandtab? shiftwidth? softtabstop? tabstop?
:autocmd UserVimrc
```

Die Kombination aus benannter Gruppe und `autocmd!` ersetzt beim Neuladen ausschließlich die eigenen Ereignisregeln. `autocmd!` nicht wahllos außerhalb dieser Gruppe verwenden. Eine neu definierte `FileType`-Regel wird durch `:source` allein noch nicht auf alle bereits geöffneten Buffer angewandt. [Autocommands](https://vimhelp.org/autocmd.txt.html), [Dateityperkennung](https://vimhelp.org/filetype.txt.html).

### Größere Regeln in after/ftplugin auslagern

| Datei bei üblichem Unix-Aufbau | Zweck |
|---|---|
| `~/.vim/after/ftplugin/python.vim` | Eigene Python-Ergänzungen |
| `~/.vim/after/ftplugin/yaml.vim` | Eigene YAML-Ergänzungen |
| `~/.vim/after/ftplugin/make.vim` | Eigene Make-Ergänzungen |

Unter nativem Windows entsprechend `~/vimfiles/after/ftplugin/` verwenden; bei anderen Layouts `:set runtimepath?` prüfen.

Beispiel für `after/ftplugin/python.vim`:

```vim
setlocal expandtab
setlocal shiftwidth=4
setlocal softtabstop=4
setlocal tabstop=8
setlocal textwidth=88

let b:undo_ftplugin = get(b:, 'undo_ftplugin', '')
      \ . '|setlocal expandtab< shiftwidth< softtabstop< tabstop< textwidth<'
```

`b:undo_ftplugin` ergänzt das Aufräumen, wenn der Dateityp desselben Buffers später wechselt. Vorhandene Aufräumbefehle bleiben erhalten. Die entsprechende Python-Autocommand-Regel aus der Basis dann durch diese Datei ersetzen, damit es eine klare zuständige Stelle gibt. Die Breite `88` ist eine Beispielentscheidung. [Filetype-Plugins schreiben und zurücksetzen](https://vimhelp.org/usr_43.txt.html#filetype-plugin).

## Swap, Backup und persistentes Undo

Diese Mechanismen lösen unterschiedliche Probleme:

| Mechanismus | Zweck | Verhalten der Basis |
|---|---|---|
| Swap | Wiederherstellung nach einem Absturz; Hinweise auf paralleles Bearbeiten | `swapfile` bleibt an |
| Schreibbackup | Vorherigen Dateiinhalt während des Schreibens absichern | `writebackup` bleibt an |
| Dauerhaftes Backup | Vorherige Dateifassung nach erfolgreichem Schreiben behalten | `backup` ist aus |
| Persistentes Undo | Bearbeitungsschritte auch nach einem Neustart zurücknehmen | Wird optional ergänzt |
| Viminfo | Unter anderem Verlauf, Register und Positionen über Sitzungen behalten | Keine eigene Vorgabe |

`nobackup writebackup` ist somit eine sinnvolle Kombination: kein dauerhaftes Sicherungsexemplar nach erfolgreichem Schreiben, aber ein temporärer Schutz beim Schreibvorgang. [Dateisicherungen](https://vimhelp.org/usr_07.txt.html), [Swap-Wiederherstellung](https://vimhelp.org/recover.txt.html), [Undo-Persistenz](https://vimhelp.org/undo.txt.html#undo-persistence), [Sitzungsdaten](https://vimhelp.org/usr_21.txt.html).

### Optionale Erweiterung: persönliche Zustandsverzeichnisse

Diesen Block bei Bedarf **zusätzlich** in die vimrc übernehmen. Er legt Verzeichnisse an und aktiviert persistentes Undo, wenn vorhanden:

```vim
let s:state_dir = has('win32') || has('win64')
      \ ? expand('~/vimfiles/state')
      \ : expand('~/.vim/state')

for s:kind in ['swap', 'backup', 'undo']
  call mkdir(s:state_dir . '/' . s:kind, 'p', 0700)
endfor

" Bei :let muessen Leerzeichen nicht wie bei :set maskiert werden.
" Kommas bleiben Trennzeichen der Verzeichnisliste und werden maskiert.
let &directory = escape(s:state_dir . '/swap', ',') . '//'
let &backupdir = escape(s:state_dir . '/backup', ',') . '//'

if has('persistent_undo')
  let &undodir = escape(s:state_dir . '/undo', ',')
  set undofile
endif
```

Das abschließende `//` erzeugt für Swap und Backup Namen aus dem vollständigen Dateipfad und vermeidet Namenskollisionen. Bei `undodir` außerhalb des Dateiverzeichnisses verwendet Vim bereits vollständige Pfadinformationen.

`0700` betrifft unter Unix neu erstellte Verzeichnisse; bestehende Rechte werden nicht repariert. Unter Windows gelten die tatsächlichen ACLs. Bei fehlenden Rechten eine konkrete Fehlermeldung beheben, statt Wiederherstellung pauschal abzuschalten. Persönlicher Swap macht außerdem nicht zwangsläufig die Bearbeitung desselben Dokuments durch **andere Benutzer oder Rechner** sichtbar. [Verzeichnisoptionen](https://vimhelp.org/options.txt.html#'directory'), [Verzeichnisse anlegen](https://vimhelp.org/builtin.txt.html#mkdir()).

Prüfen:

```vim
:set directory? backupdir? backup? writebackup?
:echo has('persistent_undo')
:set undofile? undodir?
:undolist
```

Die beiden `undo`-Optionsabfragen setzen das entsprechende Buildmerkmal voraus.

> [!warning] Gespeicherte Textreste
> Swap, Backup und Undo können frühere oder inzwischen gelöschte Inhalte enthalten. `set noundofile` entfernt bestehende Undo-Dateien nicht. Speicherorte, Sicherungsprogramme und Zugriffsrechte bei vertraulichen Dokumenten bewusst wählen; die vimrc allein ersetzt kein Schutzkonzept für solche Dateien.

## Zwischenablage gezielt anbinden

Vim-Register, Betriebssystem-Zwischenablage und Terminal-Einfügen sind getrennte Wege. Die Basis verändert `clipboard` nicht.

```vim
:version
:echo has('clipboard')
:echo has('unnamedplus')
:echo exists('+clipmethod')
:echo exists('v:clipproviders')
```

Auf unterstützten Systemen spricht `"+y` im visuellen Modus die Zwischenablage an, `"+p` fügt daraus ein. `"*` kann unter X11 die primäre Auswahl ansprechen; native Windows-Implementierungen behandeln die Register anders. [Auswahlregister](https://vimhelp.org/gui.txt.html#clipboard), [X11-Auswahl](https://vimhelp.org/gui_x11.txt.html#x11-selection).

Optional alle normalen Kopier-, Lösch- und Einfügevorgänge anbinden:

```vim
" Erst nach Einrichtung eines eventuell benoetigten Providers auswerten.
if has('unnamedplus')
  set clipboard^=unnamedplus
elseif has('clipboard')
  set clipboard^=unnamed
endif
```

`^=` fügt vorn ein, sodass ein vorhandener `exclude:`-Eintrag nicht verschoben werden muss. Diese Umleitung betrifft auch `d` und `c`; dadurch kann ein Löschvorgang die System-Zwischenablage ersetzen.

Neuere Vim-Builds können Clipboard-Provider anbieten, die `"+` und `"*` auch ohne klassisches `+clipboard` bereitstellen. Daher entscheidet nicht allein `has('clipboard')` über sämtliche Möglichkeiten. Provider-API und `clipmethod` nur verwenden, wenn der installierte Build sie kennt; die lokale Hilfe `:help clipboard-providers` beschreibt deren Einrichtung. [Provider-Referenz](https://vimhelp.org/eval.txt.html#clipboard-providers), [Zwischenablageoption](https://vimhelp.org/options.txt.html#'clipboard').

Ein positives Merkmal garantiert keine funktionierende Desktop-Verbindung. Unter Wayland, SSH, WSL und Multiplexern den tatsächlichen Übertragungsweg prüfen. Ein entferntes Vim erreicht nicht automatisch die Zwischenablage des lokalen Rechners. [Vim unter Wayland](https://vimhelp.org/wayland.txt.html).

## Farben, Maus und Terminal

### Farbschema und Truecolor

```vim
" Ein mitgeliefertes Farbschema als einfacher Ausgangspunkt.
colorscheme default

" Nur aktivieren, wenn die gesamte Terminalverbindung 24-Bit-Farben traegt.
if exists('+termguicolors')
  set termguicolors
endif
```

Die Featureprüfung bestätigt die Vim-Option; sie prüft nicht Terminal, SSH-Strecke und Multiplexer. Bei falschen Farben zunächst `:set notermguicolors` ausprobieren. `background=dark` beschreibt den gewünschten Hintergrundmodus für Farbanpassungen; es erzeugt keinen schwarzen Terminalhintergrund. [Farbschemata](https://vimhelp.org/usr_06.txt.html), [Truecolor im Terminal](https://vimhelp.org/term.txt.html#xterm-true-color).

### Maus und Einfügen

```vim
" Optional: Vim darf die Maus verwenden.
if has('mouse')
  set mouse=a
endif
```

Mit aktiver Vim-Maus kann das Markieren durch das Terminal eine zusätzliche Taste erfordern; diese gehört zur Terminalkonfiguration. `:set mouse=` deaktiviert die Vim-Maus wieder.

Wenn eingefügter Text unerwartet eingerückt wird, zuerst den verwendeten Einfügeweg prüfen. Für einen manuellen Sonderfall kann `:set paste` vor dem Einfügen und `:set nopaste` danach helfen. `paste` nicht dauerhaft aktivieren, weil es Bearbeitungsfunktionen verändert. Moderne Terminalpfade können Einfügen automatisch erkennen. [Erkanntes Terminal-Einfügen](https://vimhelp.org/term.txt.html#xterm-bracketed-paste), [Terminalsteuerung](https://vimhelp.org/term.txt.html).

## Native Pakete und Plugins

Vim kann Pakete ohne zusätzlichen Pluginmanager laden:

| Lage bei üblichem Unix-Aufbau | Verhalten |
|---|---|
| `~/.vim/pack/vendor/start/paketname/` | Beim normalen Start automatisch laden |
| `~/.vim/pack/vendor/opt/paketname/` | Bei Bedarf mit `:packadd paketname` laden |

`vendor` ist ein frei gewählter Gruppierungsname. Unter Windows gewöhnlich `~/vimfiles/pack/` verwenden; entscheidend ist `:set packpath?`.

Die Distribution kann optionale Pakete mitbringen. Beispiel für das vorhandene Paket `matchit`:

```vim
" In der vimrc: zur spaeteren normalen Plugin-Ladephase vormerken.
packadd! matchit
```

Zum direkten Ausprobieren während einer laufenden Sitzung:

```vim
:packadd matchit
:help matchit
```

`packadd!` ergänzt den Runtime-Pfad, lädt die Plugin-Dateien aber nicht sofort. Die normale Startphase übernimmt das Laden und respektiert `--noplugin`. Nach einem bloßen Neuladen der vimrc ist deshalb nicht jeder neu ergänzte Paketbefehl bereits aktiv. Fehlt das Paket, meldet Vim den fehlenden Namen; dessen Bereitstellung zunächst klären.

Externe Pakete bewusst installieren, Version oder Commit dokumentieren und Updates einzeln prüfen. Ein Pluginmanager kann diesen Ablauf organisieren, ist für die Basis aber nicht nötig. [Native Pakete](https://vimhelp.org/repeat.txt.html#packages), [mitgelieferte Pakete](https://vimhelp.org/usr_05.txt.html#add-package).

## Konfiguration aufteilen

Eine große Datei lässt sich später nach Verantwortung zerlegen:

| Eigene Datei | Inhalt |
|---|---|
| `~/.vim/config/options.vim` | Allgemeine Optionen |
| `~/.vim/config/maps.vim` | Tastenkürzel |
| `~/.vim/config/autocmds.vim` | Eigene benannte Gruppen |
| `~/.vim/after/ftplugin/*.vim` | Dateitypregeln |
| `~/.vim/pack/` | Pakete |

Beispiel für eine bewusst gewählte, vorhandene Datei:

```vim
execute 'source ' . fnameescape(expand('~/.vim/config/options.vim'))
```

`fnameescape()` schützt Sonderzeichen des Dateinamens beim Aufbau des Ex-Befehls. Ein fehlendes benötigtes Modul sollte sichtbar fehlschlagen. Nur tatsächlich optionale Dateien vorher mit `filereadable()` prüfen. Eigene Konfiguration in Git dokumentieren; Swap, Undo, lokale Zustandsdaten und vertrauliche Werte ausnehmen. [Skripte laden](https://vimhelp.org/repeat.txt.html#%3Asource), [[Git-Cheatsheet]].

## Neuladen und Fehleranalyse

### Änderungen sicher ausprobieren

Für einfache Einstellungen kann nach dem Speichern in der **geöffneten eigenen vimrc** Folgendes ausgeführt werden:

```vim
:write
:source %
:messages
```

`%` bezeichnet die aktuelle Datei. `:source` führt deren Inhalt aus; diesen Befehl nur in der beabsichtigten Konfiguration verwenden.

Die benannte Augroup verhindert doppelte eigene Ereignisregeln. Ein Reload entfernt aber keine inzwischen aus der Datei gelöschten Mappings, macht Pluginzustände nicht rückgängig und setzt bereits geänderte Buffer nicht vollständig zurück. Nach strukturellen Änderungen neu starten. [Skriptausführung](https://vimhelp.org/repeat.txt.html#%3Asource), [Autocommand-Gruppen](https://vimhelp.org/autocmd.txt.html#autocmd-groups).

### Vergleichsstarts

Die folgenden Befehle gehören in das Terminal:

```bash
vim --clean beispiel.txt
vim -N -u NONE -U NONE -i NONE beispiel.txt
vim --noplugin beispiel.txt
vim -u ./test-vimrc -U NONE -i NONE --noplugin beispiel.txt
```

| Start | Aussage |
|---|---|
| `--clean` | Saubere Umgebung mit `defaults.vim`, ohne persönliche Initialisierung und Viminfo |
| `-N -u NONE -U NONE -i NONE` | Explizit Vim-Modus; keine vimrc, gvimrc, Plugins oder Viminfo; kein `defaults.vim` |
| `--noplugin` | Eigene vimrc bleibt aktiv; automatische Plugin-Ladephase wird ausgelassen |
| `-u ./test-vimrc …` | Gezielt diese Datei statt der regulären Konfiguration verwenden |

`-u NONE` allein kann Vim im kompatiblen Modus belassen. Deshalb steht im minimalistischen Vergleich ausdrücklich `-N`. Ein `--noplugin` verhindert keine Plugin-Dateien, die die eigene vimrc ausdrücklich mit `source` oder `packadd` lädt. [Startoptionen](https://vimhelp.org/starting.txt.html#-u).

### Diagnose nach Symptom

| Problem | Prüfung und nächster Schritt |
|---|---|
| Einstellung hat keine Wirkung | `:verbose set optionsname?`; korrekte Datei und spätere Überschreibungen suchen |
| Einrückung nur bei einer Sprache falsch | `:setlocal filetype?`, danach `:verbose setlocal shiftwidth? expandtab?` |
| Mapping reagiert anders | `:verbose nmap <Leader>w`; Modus und tatsächlichen Leader prüfen |
| Ereignis läuft mehrfach | `:autocmd UserVimrc`; doppelte Definitionen oder andere Gruppen prüfen |
| `E518`: unbekannte Option | Schreibweise, `:version` und installierte Hilfe prüfen |
| `E492`: unbekannter Befehl | Falsche Skriptsprache, fehlendes Paket oder fehlendes Buildmerkmal prüfen |
| `E185`: Farbschema fehlt | Namen, Runtime-Pfad und Paketbereitstellung prüfen |
| `E303` oder `E739` | Swap- beziehungsweise Verzeichniszugriff prüfen |
| Problem nur mit der vollständigen Konfiguration | Eigene Blöcke schrittweise halbieren, bis ein kleiner reproduzierbarer Fall bleibt |

Für die Startzeit:

```bash
vim --startuptime vim-startup.log -c 'quit'
```

Eine bestehende Logdatei wird ergänzt. Bei schwer erkennbaren Startfehlern kann `vim -V1vim-debug.log` helfen; Diagnoseprotokolle können persönliche Pfade enthalten. [Startzeit und Verbose-Modus](https://vimhelp.org/starting.txt.html#--startuptime), [Meldungen](https://vimhelp.org/message.txt.html#%3Amessages).

## Konfigurationscode und Vertrauen

Eine vimrc und ihre Plugins sind ausführbarer Code mit den Rechten des gestarteten Prozesses. Die Basis setzt deshalb `noexrc`: Projektverzeichnisse sollen nicht automatisch eigene `.vimrc`- oder `.exrc`-Dateien ausführen.

Modelines sind dagegen Einstellungszeilen innerhalb bearbeiteter Dokumente. Die Basis deaktiviert sie mit `nomodeline` und erlaubt keine Modeline-Ausdrücke. Neuere Builds können zusätzliche Beschränkungen wie `modelinestrict` besitzen; solche Optionen nur nach Prüfung der lokalen Hilfe verwenden.

`secure` ist kein allgemeiner Schutzkasten für sämtliche Skripte. Insbesondere kann eine frisch heruntergeladene Projektdatei bereits dem eigenen Benutzer gehören. Projektabhängige Regeln besser ausdrücklich in der eigenen geprüften Konfiguration verwalten. [Projekt-vimrc und Sicherheitsgrenzen](https://vimhelp.org/starting.txt.html#trojan-horse), [Modelines](https://vimhelp.org/options.txt.html#modeline).

## Quellen

**Recherche und redaktioneller Stand: 12. Oktober 2026.** Die verlinkten Vim-Hilfen werden fortlaufend aktualisiert. Lokale `:help` und `:version` beschreiben die tatsächlich installierte Version.

| Thema | Offizielle Vim-Dokumentation |
|---|---|
| Einstellungen und Basisdatei | [usr_05.txt](https://vimhelp.org/usr_05.txt.html) |
| Start, Pfade und Diagnoseargumente | [starting.txt](https://vimhelp.org/starting.txt.html) |
| Optionen und Gültigkeit | [options.txt](https://vimhelp.org/options.txt.html) |
| Mappings | [map.txt](https://vimhelp.org/map.txt.html) |
| Autocommands | [autocmd.txt](https://vimhelp.org/autocmd.txt.html) |
| Dateityperkennung | [filetype.txt](https://vimhelp.org/filetype.txt.html) |
| Eigene Filetype-Plugins | [usr_43.txt](https://vimhelp.org/usr_43.txt.html) |
| Vimscript und Funktionen | [usr_41.txt](https://vimhelp.org/usr_41.txt.html), [builtin.txt](https://vimhelp.org/builtin.txt.html) |
| Vim9-Sprache | [vim9.txt](https://vimhelp.org/vim9.txt.html) |
| Pakete und Skripte | [repeat.txt](https://vimhelp.org/repeat.txt.html) |
| Undo und Wiederherstellung | [undo.txt](https://vimhelp.org/undo.txt.html), [recover.txt](https://vimhelp.org/recover.txt.html) |
| Clipboard-Provider | [eval.txt](https://vimhelp.org/eval.txt.html#clipboard-providers) |
| Terminal und Wayland | [term.txt](https://vimhelp.org/term.txt.html), [wayland.txt](https://vimhelp.org/wayland.txt.html) |
| Offizieller Runtime-Quelltext | [vim/vim](https://github.com/vim/vim) |

## Verwandte Notizen

- [[Vim-Cheatsheet|Vim – Bedienung, Bewegungen und Arbeitsabläufe]]
- [[Neovim-Cheatsheet|Neovim – eigener Editor und Funktionsumfang]]
- [[Neovim-Konfiguration-und-Plugins-Cheatsheet|Neovim – Lua-Konfiguration und Plugins]]
- [[Neovim-Shortcuts-und-Bewegungen|Verwandte Bewegungen und Textobjekte]]
- [[Git-Cheatsheet|Konfiguration nachvollziehbar versionieren]]
- [[Make-und-Source-Builds-Cheatsheet|Makefiles und Buildsysteme]]
- [[02-Versionierung-Entwicklung/INDEX|Versionierung, Entwicklung & Editoren]]
