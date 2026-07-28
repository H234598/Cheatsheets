---
title: "Neovim – Cheatsheet"
aliases: ["nvim Cheatsheet", "Neovim ausführlich", "Vim Neovim"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [neovim, vim, editor, lua, shortcuts, development]
source: "https://neovim.io/doc/user/"
---

# Neovim – Cheatsheet

> [!abstract] Zweck
> Zentrale ausführliche Neovim-Referenz: Denkmodell, Modi, Operator-Motion-Sprache, Dateien, Buffer, Fenster, Tabs, Suche, Ersetzen, Register, Makros, Quickfix, Terminal, Sessions und Diagnose.

> [!abstract] Denkmodell
> Neovim wird nicht primär über einzelne Tastenkürzel gelernt, sondern als Sprache: **Anzahl + Operator + Bewegung/Textobjekt**. Beispiel `3dw` bedeutet „dreimal: bis zum nächsten Wort löschen“, `ci"` bedeutet „Inhalt innerhalb der Anführungszeichen ändern“.

## Inhalt

- [[#Start und Hilfe]]
- [[#Modi]]
- [[#Operatoren, Bewegungen und Textobjekte]]
- [[#Einfügen und Ändern]]
- [[#Dateien und Buffer]]
- [[#Fenster und Tabs]]
- [[#Suche und Ersetzen]]
- [[#Register, Zwischenablage und Löschen]]
- [[#Marks, Jumps und Change List]]
- [[#Makros und Wiederholung]]
- [[#Quickfix, Location List und Diagnose]]
- [[#Terminal, Sessions und externe Befehle]]
- [[#Gesundheitsprüfung und Rettung]]

Vertiefungen:

- [[Neovim-Shortcuts-und-Bewegungen]]
- [[Neovim-Konfiguration-und-Plugins-Cheatsheet]]
- [[Neovim-LSP-Debugging-Cheatsheet]]

## Start und Hilfe

```bash
nvim datei.txt
nvim +42 datei.txt
nvim +/suchtext datei.txt
nvim -R datei.txt                 # read-only
nvim -d alt.txt neu.txt           # Diffmodus
nvim -u NONE -N                   # ohne Benutzerkonfiguration, nocompatible
nvim --clean                      # saubere Sitzung mit Defaults
nvim --headless '+checkhealth' +qa
```

In Neovim:

```vim
:version
:checkhealth
:messages
:scriptnames
:set runtimepath?
```

Hilfe ist hyperverlinkt:

```vim
:help
:help user-manual
:help motion.txt
:help operator
:help text-objects
:help :substitute
:help lua-guide
:help diagnostic
```

Navigation in Hilfe:

```text
Ctrl-]   Link unter Cursor öffnen
Ctrl-T   zurück
Ctrl-O   ältere Sprungposition
:q       Hilfefenster schließen
```

> [!tip]
> Bei unbekanntem Befehl erst `:help <begriff>` verwenden. Ex-Befehle mit Doppelpunkt suchen: `:help :write`; Optionen in Apostrophen: `:help 'number'`; Normalmodus-Taste: `:help CTRL-W`.

## Modi

| Modus | Eintritt | Verlassen/Zweck |
|---|---|---|
| Normal | `Esc` | Navigation und Operatoren |
| Insert | `i`, `a`, `o` | Text eingeben; `Esc` zurück |
| Visual char | `v` | zeichenweise Auswahl |
| Visual line | `V` | zeilenweise Auswahl |
| Visual block | `Ctrl-V` | rechteckige Auswahl |
| Command-line | `:` `/` `?` | Ex-Befehle/Suche |
| Replace | `R` | Zeichen überschreiben |
| Terminal-Job | in Terminal | Programmeingabe |
| Terminal-Normal | `Ctrl-\ Ctrl-N` | Terminalbuffer wie Buffer navigieren |

`Esc` ist die zentrale Rückkehr in den Normalmodus. Alternativ kann `Ctrl-[` dienen.

## Operatoren, Bewegungen und Textobjekte

Formel:

```text
[count] operator [count] motion
```

### Operatoren

| Taste | Wirkung |
|---|---|
| `d` | delete, landet in Register |
| `c` | change: löschen + Insertmodus |
| `y` | yank/kopieren |
| `>` / `<` | ein-/ausrücken |
| `=` | formatieren/einrücken |
| `g~` | Groß-/Kleinschreibung umkehren |
| `gu` / `gU` | klein/groß schreiben |
| `!` | durch externen Filter schicken |

Doppelte Operatoren wirken zeilenweise:

```text
dd   Zeile löschen
yy   Zeile kopieren
cc   Zeile ändern
>>   einrücken
==   einrücken/formatieren
```

### Bewegungen

```text
h j k l        links, unten, oben, rechts
w b e          Wortanfang vor/zurück, Wortende
W B E          WORD: durch Leerraum getrennt
0 ^ $          Spaltenanfang, erstes Nichtleerzeichen, Zeilenende
g_             letztes Nichtleerzeichen
f{char}        bis Zeichen vorwärts
F{char}        rückwärts
t{char}        vor Zeichen
; ,            letzte f/t-Bewegung wiederholen/umkehren
( )            Satz zurück/vor
{ }            Absatz zurück/vor
gg G           Dateianfang/Dateiende
50G            Zeile 50
%              passende Klammer/Struktur
Ctrl-D/U       halbe Seite ab/auf
Ctrl-F/B       ganze Seite ab/auf
zz zt zb       Cursorzeile Mitte/oben/unten
```

### Textobjekte

```text
iw / aw        inner word / a word
iW / aW        WORD
is / as        Satz
ip / ap        Absatz
i" / a"        innerhalb/inkl. Anführungszeichen
i' / a'
i` / a`
i( / a(        Klammern; auch ib/ab
 i[ / a[
i{ / a{        Blöcke; auch iB/aB
it / at        HTML/XML-Tag
```

Beispiele:

```text
ciw     aktuelles Wort ersetzen
daw     Wort inkl. Umgebung löschen
yi"     Inhalt in Anführungszeichen kopieren
di{     Blockinhalt löschen
gUap    Absatz groß schreiben
=G      bis Dateiende einrücken
```

## Einfügen und Ändern

| Taste | Aktion |
|---|---|
| `i` / `a` | vor/nach Cursor einfügen |
| `I` / `A` | am ersten Nichtleerzeichen/Zeilenende |
| `o` / `O` | neue Zeile unter/über |
| `s` / `S` | Zeichen/Zeile ersetzen |
| `r{char}` | ein Zeichen ersetzen |
| `R` | Replace-Modus |
| `x` / `X` | Zeichen unter/vor Cursor löschen |
| `J` | nächste Zeile verbinden |
| `gJ` | ohne zusätzlichen Abstand verbinden |
| `u` | rückgängig |
| `Ctrl-R` | wiederholen/redo |
| `.` | letzte Änderung wiederholen |

Insertmodus:

```text
Ctrl-W         vorheriges Wort löschen
Ctrl-U         bis Zeilenanfang löschen
Ctrl-T/D       Einrückung erhöhen/verringern
Ctrl-N/P       Completion vor/zurück
Ctrl-R {reg}   Register einfügen
Ctrl-O {cmd}   genau einen Normalbefehl ausführen
```

> [!tip] Punktbefehl planen
> Eine Änderung so formulieren, dass sie mit `.` wiederholbar ist. `ciwTEXT<Esc>` ist wiederholbarer als viele Einzelbewegungen.

## Dateien und Buffer

### Datei öffnen/speichern

```vim
:e pfad/datei.txt
:edit %:h/andere.txt
:w
:w neuer-name.txt
:saveas neuer-name.txt
:update
:q
:wq
:x
:q!
:wall
:qall
:wqall
```

`%` ist aktueller Dateiname:

```vim
:echo expand('%:p')
:pwd
:cd /pfad
:lcd /pfad
:tcd /pfad
```

### Buffer

```vim
:ls
:buffers
:bnext
:bprevious
:buffer 3
:bdelete
:bwipeout
```

Normalmodus:

```text
]b / [b   nächster/vorheriger Buffer, falls Mapping/Version unterstützt
Ctrl-^    alternativer Buffer
```

Ohne Mapping zuverlässig:

```vim
:bn
:bp
:b#
```

Begriffe:

- Buffer: Text im Speicher
- Window: Sicht auf einen Buffer
- Tabpage: Sammlung von Fenstern

Ein Buffer kann in mehreren Fenstern sichtbar sein.

### Alte Dateien und Argumentliste

```vim
:oldfiles
:browse oldfiles
:args *.py
:args
:next
:previous
:argdo update
```

## Fenster und Tabs

### Splits

```vim
:split datei
:vsplit datei
:new
:vnew
:only
:close
```

`Ctrl-W`-Familie:

```text
Ctrl-W s / v      horizontal/vertikal teilen
Ctrl-W h/j/k/l    Fokus wechseln
Ctrl-W w          zyklisch wechseln
Ctrl-W q/c        schließen
Ctrl-W o          nur aktuelles Fenster
Ctrl-W =          Größen ausgleichen
Ctrl-W _ / |      maximale Höhe/Breite
Ctrl-W +/-        Höhe ändern
Ctrl-W </>        Breite ändern
Ctrl-W H/J/K/L    Fenster verschieben
```

### Tabs

```vim
:tabnew
:tabedit datei
:tabnext
:tabprevious
:tabclose
:tabonly
:tabs
```

Normalmodus:

```text
gt        nächster Tab
gT        vorheriger Tab
3gt       Tab 3
```

> [!important]
> Tabs sind keine Buffer. Für viele Dateien meist Buffer + Fenster verwenden; Tabs eignen sich als unterschiedliche Arbeitslayouts.

## Suche und Ersetzen

### Suche

```text
/pattern     vorwärts
?pattern     rückwärts
n / N        wiederholen/umkehren
* / #        Wort unter Cursor vor/rückwärts
```

Optionen:

```vim
:set ignorecase
:set smartcase
:set incsearch
:set hlsearch
:nohlsearch
```

Magic:

```vim
/\v(foo|bar)+
```

`
\v` schaltet „very magic“ ein und reduziert Escape-Bedarf.

### Ersetzen

Aktuelle Zeile, erstes Vorkommen:

```vim
:s/alt/neu/
```

Alle der Zeile:

```vim
:s/alt/neu/g
```

Gesamte Datei, bestätigen:

```vim
:%s/alt/neu/gc
```

Wortgrenzen:

```vim
:%s/\<alt\>/neu/g
```

Groß-/Kleinschreibung:

```vim
:%s/alt/neu/gi
:%s/\CAlt/Neu/g
```

Gruppen:

```vim
:%s/\v([A-Za-z]+), ([A-Za-z]+)/\2 \1/g
```

Ausdruck:

```vim
:%s/\d\+/\=submatch(0) + 1/g
```

Bereich:

```vim
:10,20s/foo/bar/g
:'<,'>s/foo/bar/g
```

## Register, Zwischenablage und Löschen

Register anzeigen:

```vim
:registers
:reg a
```

| Register | Zweck |
|---|---|
| `"` | unnamed, Standard |
| `0` | letzter Yank |
| `1`–`9` | Löschhistorie |
| `-` | kleine Löschungen |
| `_` | Black-Hole, verwirft |
| `a`–`z` | benannte Register |
| `A`–`Z` | an benanntes Register anhängen |
| `+` | Systemzwischenablage |
| `*` | Primary Selection/Clipboard je System |
| `:` | letzter Ex-Befehl |
| `/` | letztes Suchmuster |
| `%` | aktueller Dateiname |

Beispiele:

```text
"ayy       Zeile nach a kopieren
"ap        a einfügen
"Ayy       an a anhängen
"_dd       löschen ohne Register zu überschreiben
"0p        letzten Yank einfügen, trotz späterem Löschen
"+y        in Systemclipboard kopieren
"+p        aus Systemclipboard einfügen
```

Einfügen:

```text
p / P      nach/vor Cursor
]p / [p    mit Einrückungsanpassung
```

Clipboard prüfen:

```vim
:checkhealth provider
:set clipboard?
```

Option:

```lua
vim.opt.clipboard = "unnamedplus"
```

Nicht zwingend setzen, wenn getrennte Vim-/Systemregister gewünscht sind.

## Marks, Jumps und Change List

Marks:

```text
ma        Mark a setzen
'a        zur Zeile von a
`a        exakt zu a
mA        globale Mark A, dateiübergreifend
:marks    anzeigen
```

Spezielle Marks:

```text
``        vorherige Position
`.        letzte Änderung
`[ / `]   Anfang/Ende letzter Änderung/Yank
'< / '>   Anfang/Ende letzter visueller Auswahl
```

Jump List:

```text
Ctrl-O    zurück
Ctrl-I    vor
:jumps
```

Change List:

```text
g;        ältere Änderung
g,        neuere Änderung
:changes
```

> [!tip]
> `Ctrl-O`, `Ctrl-I`, `` ` `` und `g;` sparen viel Scrollen. Sie bilden einen navigierbaren Verlauf statt einer einzigen „Zurück“-Taste.

## Makros und Wiederholung

Aufzeichnen:

```text
qa          Aufnahme in Register a starten
...         Befehle
q           stoppen
@a          abspielen
@@          letztes Makro wiederholen
10@a        zehnmal
```

Makro bearbeiten:

```text
"ap         Inhalt von a einfügen
# Text bearbeiten
"ayy        wieder in a kopieren
```

Makro über Zeilen:

```vim
:'<,'>normal @a
```

Normalbefehl auf Bereich:

```vim
:%normal I# 
```

Punktbefehl, Makro, `:normal`, `:global` und Substitute sind vier unterschiedliche Wiederholungswerkzeuge.

### Global

```vim
:g/pattern/print
:g/pattern/delete
:v/pattern/delete
:g/TODO/normal A  # geprüft
```

Vor destruktivem globalen Befehl zunächst `print` oder Kopie/Undo-Punkt.

## Quickfix, Location List und Diagnose

Quickfix ist globale Fehler-/Trefferliste:

```vim
:make
:copen
:cclose
:cnext
:cprevious
:cfirst
:clast
:cdo s/foo/bar/g | update
```

Location List ist fensterlokal:

```vim
:lopen
:lnext
:lprevious
:ldo ...
```

Vimgrep:

```vim
:vimgrep /TODO/j **/*.py
:copen
```

Mit externem grep:

```vim
:set grepprg=rg\ --vimgrep\ --smart-case
:grep TODO **/*.py
:copen
```

Fehlermeldungen:

```vim
:messages
:verbose set number?
:verbose nmap <leader>f
:verbose autocmd BufWritePre
```

`verbose` zeigt häufig die Datei, die Option/Mapping zuletzt gesetzt hat.

## Terminal, Sessions und externe Befehle

### Terminal

```vim
:terminal
:split | terminal
:vsplit | terminal
```

Terminal-Normalmodus:

```text
Ctrl-\ Ctrl-N
```

Dann normale Navigation/Yank. Zur Job-Eingabe `i` oder `a`.

### Shellbefehle

```vim
:!ls -la
:r !date
:.!sort
:'<,'>!sort
```

`!` als Operator:

```text
!ip sort
```

### Sessions und Views

```vim
:mksession! Session.vim
:source Session.vim
:mkview
:loadview
```

Sessionoptionen:

```vim
:set sessionoptions?
```

Sessiondateien können Pfade und Befehle enthalten; aus untrusted Quelle nicht blind sourcen.

## Gesundheitsprüfung und Rettung

### Ohne Konfiguration testen

```bash
nvim --clean datei
nvim -u NONE -N datei
```

Wenn Fehler nur mit Config auftritt:

```vim
:scriptnames
:messages
:checkhealth
```

Startup-Profil:

```bash
nvim --startuptime startup.log +qa
```

Lua-Fehler:

```vim
:lua print(vim.inspect(vim.api.nvim_list_bufs()))
:lua =vim.opt.number:get()
```

### Swap/Recovery

Beim Hinweis auf Swap:

- prüfen, ob Datei wirklich noch in anderer Sitzung geöffnet ist
- `R`/`:recover` zur Wiederherstellung
- geretteten Inhalt unter neuem Namen speichern
- Diff gegen Original
- Swap erst danach löschen

```bash
nvim -r
nvim -r datei.txt
```

### Undo-Datei

```vim
:set undofile
:earlier 10m
:later 5m
:undolist
```

Persistent Undo ist nützlich, aber Undo-Verzeichnis und Datenschutz beachten.

### Universelle Diagnose

```text
1. :messages
2. :checkhealth
3. :verbose <map/set/autocmd>
4. nvim --clean reproduzieren
5. Plugins halbieren/deaktivieren
6. :scriptnames und runtimepath prüfen
7. minimale init.lua erstellen
8. exakte Neovim-Version und Log sichern
```

## Quellen
- [Neovim User Manual](https://neovim.io/doc/user/)
- [Neovim Lua Guide](https://neovim.io/doc/user/lua-guide.html)
- [Neovim FAQ](https://neovim.io/doc/user/faq.html)

## Verwandte Notizen
- [[Neovim-Shortcuts-und-Bewegungen]]
- [[Neovim-Konfiguration-und-Plugins-Cheatsheet]]
- [[Neovim-LSP-Debugging-Cheatsheet]]
- [[Git-Cheatsheet]]
