---
title: "Neovim – Shortcuts, Bewegungen und Textobjekte"
aliases: ["Neovim Shortcuts", "Vim Bewegungen", "nvim Keymap"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [neovim, vim, shortcuts, motions, text-objects]
source: "https://neovim.io/doc/user/motion.html"
---

# Neovim – Shortcuts, Bewegungen und Textobjekte

> [!abstract] Zweck
> Dichte Unterseite mit Neovim-Tastenreferenz für Navigation, Operatoren, Textobjekte, Auswahl, Einfügen, Register, Fenster, Tabs, Folds, Completion und Kommandozeile.

## Merksystem

```text
[Anzahl] [Operator] [Bewegung/Textobjekt]
```

```text
2d3w   = 2 × (3 Wörter löschen) = 6 Wörter
diw    = inneres Wort löschen
ci(    = Inhalt in Klammern ändern
yap    = Absatz inklusive Umgebung kopieren
```

## Normalmodus – Navigation

### Zeichen und Zeilen

| Taste | Aktion |
|---|---|
| `h j k l` | links, unten, oben, rechts |
| `gj gk` | visuelle Bildschirmzeile ab/auf bei Umbruch |
| `0` | physischer Zeilenanfang |
| `^` | erstes Nichtleerzeichen |
| `$` | Zeilenende |
| `g_` | letztes Nichtleerzeichen |
| `|` | Spalte nach Count, z. B. `20|` |
| `+` / `-` | erste Nichtleerstelle nächste/vorherige Zeile |
| `_` | erste Nichtleerstelle, Count-Zeile abwärts |

### Wörter

| Taste | Aktion |
|---|---|
| `w` | nächster Wortanfang |
| `b` | vorheriger Wortanfang |
| `e` | Wortende |
| `ge` | vorheriges Wortende |
| `W B E gE` | dasselbe für WORDs, durch Whitespace getrennt |

### Zeichen suchen

```text
f{c}    auf nächstes c
t{c}    direkt vor nächstes c
F{c}    rückwärts auf c
T{c}    rückwärts direkt nach c
;       wiederholen
,       umgekehrt wiederholen
```

### Dokumentstruktur

```text
( )          Satz zurück/vor
{ }          Absatz zurück/vor
[[ ]]        Abschnitt/Funktionskontext, dateitypabhängig
[] ][        Varianten für Abschnitt/Klammern
%            passende Klammer/Preprocessor-Struktur
gg / G       erste/letzte Zeile
{n}G         Zeile n
{n}%         Prozentposition in Datei
H M L        obere/mittlere/untere sichtbare Zeile
```

### Scrollen und Ansicht

```text
Ctrl-E/Y     Ansicht eine Zeile ab/auf, Cursor bleibt
Ctrl-D/U     halbe Seite ab/auf
Ctrl-F/B     ganze Seite ab/auf
zz           Cursorzeile zentrieren
zt / zb      Cursorzeile oben/unten
z<Enter>     Cursorzeile oben, Cursor erstes Nichtleerzeichen
```

## Operatoren

| Operator | Zweck | Zeilenform |
|---|---|---|
| `d` | löschen | `dd` |
| `c` | ändern | `cc` |
| `y` | kopieren | `yy` |
| `>` | einrücken | `>>` |
| `<` | ausrücken | `<<` |
| `=` | automatisch einrücken | `==` |
| `gq` | Text formatieren | `gqq` |
| `gu` | klein | `guu` |
| `gU` | groß | `gUU` |
| `g~` | Case umkehren | `g~~` |
| `!` | externer Filter | `!!` |

Operator abbrechen: `Esc`.

## Textobjekte

### Wort bis Absatz

```text
iw aw     word
iW aW     WORD
is as     sentence
ip ap     paragraph
```

### Begrenzungen

```text
i" a"     doppelte Anführungszeichen
i' a'     einfache Anführungszeichen
i` a`     Backticks
i( a(     runde Klammer; ib/ab
i[ a[     eckige Klammer
i{ a{     geschweifte Klammer; iB/aB
i< a<     spitze Klammer
it at     Tag
```

`i` = innerer Inhalt, `a` = inklusive Begrenzung/Umgebung.

### Praktische Kombinationen

```text
ciw       Wort ersetzen
ci"       Stringinhalt ersetzen
da(       Klammerausdruck löschen
yip       Absatzinhalt kopieren
>i{       Block einrücken
=gG       von Cursor bis Dateiende einrücken
gqap      Absatz umbrechen
```

## Einfügen und Bearbeiten

```text
i / a        vor/nach Cursor
gi           Insert an letzter Insertposition
I / A        Zeilenanfang/-ende
o / O        Zeile unter/über
s / S        Zeichen/Zeile ändern
r{c}         Zeichen ersetzen
gr{c}        virtuell ersetzen, je Verhalten
R            Replace-Modus
C            bis Zeilenende ändern
D            bis Zeilenende löschen
Y            Zeile kopieren, je Standard/Version
x / X        Zeichen unter/vor Cursor löschen
J / gJ       Zeilen verbinden mit/ohne Space
~            Case eines Zeichens umkehren
```

### Insertmodus

```text
Ctrl-H        Backspace
Ctrl-W        Wort zurück löschen
Ctrl-U        bis Insertanfang/Zeilenanfang löschen
Ctrl-T/D      Einrückung erhöhen/verringern
Ctrl-N/P      Completion nächster/vorheriger
Ctrl-X ...    Completion-Untermodi
Ctrl-R {reg}  Register einfügen
Ctrl-O {cmd}  einen Normalbefehl
Ctrl-G u      Undo-Grenze setzen
Ctrl-V {key}  Literalzeichen eingeben
```

## Visualmodus

```text
v            zeichenweise
V            zeilenweise
Ctrl-V       Block
```

Während Auswahl:

```text
o            anderes Ende aktivieren
O            andere Ecke im Blockmodus
gv           letzte Auswahl erneut
ao/...?      Textobjektbewegung wie Normalmodus
d c y > < =  Operator anwenden
u / U / ~    klein/groß/umschalten
```

Blockeinfügung:

```text
Ctrl-V → Zeilen markieren → I → Text → Esc
```

Am Ende mehrerer Zeilen:

```text
Ctrl-V → markieren → $ → A → Text → Esc
```

## Undo, Wiederholung und Historie

```text
u            undo
Ctrl-R       redo
U            Änderungen einer Zeile, historisches Verhalten beachten
.            letzte Änderung wiederholen
@:           letzten Ex-Befehl wiederholen
&            letzte Substitute-Operation aktuelle Zeile
:&&          letzte Substitute mit Flags
q:           Ex-Befehlshistorie als Fenster
q/           Suchhistorie als Fenster
```

Zeitbasiert:

```vim
:earlier 5m
:later 2m
:earlier 3f
:undolist
```

## Register

```text
"{reg}{operator/motion}
```

```text
"ayy      Zeile → a
"ap       a einfügen
"Ayy      an a anhängen
"_daw     verwerfen
"0p       letzter Yank
"1p       letzte große Löschung
"+y       Systemclipboard
"+p       Systemclipboard einfügen
```

Register im Insert-/Commandmodus:

```text
Ctrl-R a
Ctrl-R "
Ctrl-R =     Ausdrucksregister
```

## Suche

```text
/pat       vorwärts
?pat       rückwärts
n / N      weiter/umgekehrt
* / #      Wort unter Cursor vor/rückwärts
g* / g#    ohne Wortgrenzen
```

```vim
:nohlsearch
:set ignorecase smartcase incsearch hlsearch
```

Suche am sehr magischen Modus:

```vim
/\v(foo|bar)\d+
```

Escape literal suchen:

```text
/\Vsehr.wörtlich[abc]
```

## Ersetzen

```vim
:s/foo/bar/
:s/foo/bar/g
:%s/foo/bar/gc
:%s/\<foo\>/bar/g
:%s/foo/bar/gi
:%s/\Cfoo/bar/g
```

Flags:

```text
g alle in Zeile
c bestätigen
i ignore case
I case-sensitive
e kein Fehler bei keinem Treffer
n nur zählen
p geänderte Zeile drucken
```

Bestätigung:

```text
y ersetzen
n überspringen
a alle
q beenden
l ersetzen und beenden
Ctrl-E/Y Ansicht scrollen
```

## Marks, Sprünge und Änderungen

```text
ma       lokale Mark a
mA       globale Mark A
'a       Zeile
`a       genaue Position
:marks
```

```text
Ctrl-O / Ctrl-I  Jump zurück/vor
:jumps
g; / g,          Change zurück/vor
:changes
```

Sondermarken:

```text
`.       letzte Änderung
`[ `]    Anfang/Ende letzte Änderung/Yank
'< '>    Visualauswahl
``         Position vor letztem Sprung
`^       letzte Insertposition
```

## Buffer, Fenster und Tabs

### Buffer

```vim
:ls
:b {nummer/name}
:bn
:bp
:b#
:bd
```

```text
Ctrl-^     alternativer Buffer
```

### Fenster

```text
Ctrl-W s/v      teilen
Ctrl-W h/j/k/l  wechseln
Ctrl-W w        zyklisch
Ctrl-W q/c      schließen
Ctrl-W o        nur aktuelles
Ctrl-W =        ausgleichen
Ctrl-W +/-      Höhe
Ctrl-W </>      Breite
Ctrl-W H/J/K/L  verschieben
```

### Tabs

```text
gt / gT     nächster/vorheriger
{n}gt       Tab n
```

```vim
:tabnew
:tabclose
:tabonly
:tabs
```

## Folds

| Taste | Aktion |
|---|---|
| `za` | Fold umschalten |
| `zo` / `zc` | öffnen/schließen |
| `zO` / `zC` | rekursiv öffnen/schließen |
| `zR` / `zM` | alle öffnen/schließen |
| `zj` / `zk` | nächster/vorheriger Fold |
| `zf{motion}` | manuellen Fold erstellen |
| `zd` / `zD` | manuellen Fold löschen/rekursiv |

Methoden:

```vim
:set foldmethod=manual
:set foldmethod=indent
:set foldmethod=expr
:set foldlevel=99
```

## Completion und Kommandozeile

### Insert Completion

```text
Ctrl-N/P       Schlüsselwörter aus Quellen
Ctrl-X Ctrl-L  ganze Zeile
Ctrl-X Ctrl-F  Dateinamen
Ctrl-X Ctrl-]  Tags
Ctrl-X Ctrl-O  Omni-Completion
Ctrl-X Ctrl-K  Wörterbuch
Ctrl-X Ctrl-S  Rechtschreibung
```

### Command-line

```text
Tab/Shift-Tab  Completion
Ctrl-P/N       Historie
Ctrl-A         alles vervollständigen, kontextabhängig
Ctrl-B/E       Anfang/Ende
Ctrl-W/U       Wort/Zeile löschen
Ctrl-R {reg}   Register
Ctrl-F         Kommandozeilenfenster
```

Ranges:

```text
.            aktuelle Zeile
$            letzte Zeile
%            ganze Datei
'<,'>        Visualbereich
' a          Mark a, ohne Leerzeichen: 'a
+3 / -2     Offset
```

Beispiele:

```vim
:.,$delete
:10,20print
:'a,'bs/foo/bar/g
:%normal A;
```

## Quickfix und Location List

```text
:cnext / :cprevious
:cfirst / :clast
:copen / :cclose
:lnext / :lprevious
:lopen / :lclose
```

Mappings werden oft auf `]q`/`[q` gelegt, sind aber nicht in jeder Konfiguration Standard.

## Terminal

```vim
:terminal
```

```text
Ctrl-\ Ctrl-N   Terminal-Normalmodus
i                 zurück zur Eingabe
```

Fensterwechsel aus Terminal kann gemappt werden; Standard sicher über Terminal-Normalmodus + `Ctrl-W h/j/k/l`.

## Mini-Drills

```text
1. ciw → neues Wort → Esc → w → .
2. f, → dt, → ; → .
3. yi" → /ziel → Enter → ci" → Ctrl-R 0 → Esc
4. ma → G → `a
5. qa ... q → 10@a
6. Ctrl-V → markieren → I# → Esc
```

## Quellen
- [Neovim motion help](https://neovim.io/doc/user/motion.html)
- [Neovim change help](https://neovim.io/doc/user/change.html)
- [Neovim windows help](https://neovim.io/doc/user/windows.html)
- [Neovim visual mode](https://neovim.io/doc/user/visual.html)

## Verwandte Notizen
- [[Neovim-Premium-Spickzettel]]
- [[Neovim-Konfiguration-und-Plugins-Premium-Spickzettel]]
- [[Neovim-LSP-Debugging-Premium-Spickzettel]]
