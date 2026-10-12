---
title: "Vim – Cheatsheet"
aliases:
  - "Vim Befehlsreferenz"
  - "Vim Bedienung und Textobjekte"
  - "Vim Spickzettel"
tags:
  - vim
  - editor
  - entwicklung
  - terminal
  - shortcuts
  - regex
  - wiederherstellung
type: reference
status: fertig
date: '2026-10-12'
created: '2026-10-12'
modified: '2026-10-12'
updates:
  - date: '2026-10-12'
    change: "Eigenständige Vim-Referenz mit geprüften Befehlen, Praxisabläufen und offiziellen Quellen erstellt."
source: "https://vimhelp.org/"
---

# Vim – Cheatsheet

> [!abstract] Zweck
> Vim vom sicheren Einstieg bis zur täglichen Arbeit: Modi, Bewegungen, Textobjekte, Register, Suche, Ersetzen, mehrere Dateien, Makros, Quickfix, Diff und Wiederherstellung. Die Beispiele benötigen keine zusätzlichen Plugins.

> [!info] Geltungsbereich
> Grundlage ist reguläres **Vim 9.x** mit den üblichen Funktionen; viele Befehle funktionieren auch in älteren Ausgaben. Kleine Builds können Funktionen auslassen. Eigene Mappings verändern Tastenbelegungen. `:version` und die lokal installierte `:help` zeigen den tatsächlichen Stand. Die Online-Dokumentation wurde am **12. Oktober 2026** geprüft.

Die dauerhafte Einrichtung steht in [[Vimrc-Konfiguration-Cheatsheet|.vimrc – Konfiguration und Praxis]]. Für Neovim gibt es [[Neovim-Cheatsheet|eine eigene Referenz]] und [[Neovim-Konfiguration-und-Plugins-Cheatsheet|eine eigene Konfigurationsseite]].

## Inhalt

- [[#Schnellstart und sicher beenden]]
- [[#Notation und Modi]]
- [[#Bewegungen und Sprungmarken]]
- [[#Operatoren und Textobjekte]]
- [[#Einfügen und visuelle Auswahl]]
- [[#Undo und Wiederholung]]
- [[#Dateien, Buffer, Fenster und Tabs]]
- [[#Suchen und Ersetzen]]
- [[#Register und Zwischenablage]]
- [[#Makros]]
- [[#Quickfix und Projektsuche]]
- [[#Dateien mit vimdiff vergleichen]]
- [[#Externe Befehle und Textfilter]]
- [[#Hilfe, Diagnose und Wiederherstellung]]
- [[#Kleine Praxisübung]]
- [[#Quellen und verwandte Seiten]]

## Schnellstart und sicher beenden

Im Terminal:

```bash
vim notizen.txt
vim +42 programm.py
vim -R protokoll.txt
vim -d alt.txt neu.txt
vimtutor
```

`+42` positioniert den Cursor in Zeile 42. `-R` setzt Vims Schreibschutzoption. `-d` startet den Diffmodus. `vimtutor` öffnet den mitgelieferten Lernkurs, sofern das entsprechende Paket installiert ist. [Startoptionen](https://vimhelp.org/starting.txt.html), [erste Schritte und Tutor](https://vimhelp.org/usr_02.txt.html).

**Erste Änderung:** `i` drücken, Text eingeben, `Esc` drücken, `:wq` eingeben und mit `Enter` bestätigen. Befehle mit Doppelpunkt werden innerhalb von Vim eingegeben.

| Befehl | Wirkung |
|---|---|
| `:w` | Aktuellen Puffer speichern |
| `:update` | Nur speichern, wenn der Puffer geändert wurde |
| `:q` | Aktuelles Fenster schließen; beim letzten Bearbeitungsfenster Vim beenden |
| `:wq` | Aktuellen Puffer schreiben und Fenster schließen |
| `:x` oder `ZZ` | Wie oben, aber nur bei Änderungen schreiben |
| `:q!` oder `ZQ` | Ohne Speichern schließen; ungesicherte Änderungen des aufgegebenen Puffers gehen verloren |
| `:wall` | Alle geänderten Puffer schreiben |
| `:wqall` | Geänderte Puffer schreiben und Vim beenden |
| `:qall!` | Vim beenden und sämtliche ungesicherten Änderungen verwerfen |

`:q` verweigert das Aufgeben ungesicherter Änderungen. `:q!` beendet nicht zwangsläufig die gesamte Sitzung: Weitere Fenster oder geänderte, versteckte Puffer können bleiben. `:wall` und `:wqall` benötigen beschreibbare Ziele; unbenannte Puffer brauchen einen Dateinamen. [Speichern und Beenden](https://vimhelp.org/editing.txt.html).

## Notation und Modi

`Ctrl-W` bedeutet: Strg halten und W drücken. Bei `Ctrl-W v` folgt danach ein gewöhnliches `v`. `gg` sind zwei aufeinanderfolgende Tastendrücke. `<Esc>` und `<Enter>` stehen für die entsprechenden Tasten. Platzhalter wie `{zeichen}` werden durch einen tatsächlichen Wert ersetzt.

| Modus | Eintritt | Aufgabe und Rückweg |
|---|---|---|
| Normal | Beim gewöhnlichen Start, sonst `Esc` | Bewegen, löschen, kopieren, Befehle kombinieren |
| Insert | `i`, `a`, `o` | Text eingeben; `Esc` zurück |
| Replace | `R` | Vorhandene Zeichen überschreiben; `Esc` zurück |
| Visual | `v` | Zeichenweise auswählen |
| Visual Line | `V` | Ganze Zeilen auswählen |
| Visual Block | `Ctrl-V` | Rechteckige Auswahl |
| Command-line | `:`, `/`, `?` | Ex-Befehl oder Suche; `Enter` ausführen, `Esc` abbrechen |
| Operator-pending | Zum Beispiel nach `d` | Auf Bewegung oder Textobjekt warten; `Esc` abbrechen |

**Normalmodus ist die Ausgangsbasis.** `i` wechselt in die Texteingabe; dieselbe Taste innerhalb eines Textobjekts, etwa `diw`, bedeutet „inner“. `Ctrl-[` dient ebenfalls als Escape-Taste. [Modi und Tastennotation](https://vimhelp.org/intro.txt.html).

## Bewegungen und Sprungmarken

### Cursor und Ansicht

| Tasten | Ziel |
|---|---|
| `h`, `j`, `k`, `l` | Links, unten, oben, rechts |
| `w`, `b`, `e` | Nächster Wortanfang, Wortanfang zurück, Wortende |
| `W`, `B`, `E` | Entsprechend für durch Leerraum getrennte WORDs |
| `0`, `^`, `$` | Zeilenanfang, erstes Nichtleerzeichen, Zeilenende |
| `g_` | Letztes Nichtleerzeichen der Zeile |
| `f;`, `F;` | Vorwärts beziehungsweise rückwärts auf ein Semikolon derselben Zeile |
| `t;`, `T;` | Vorwärts davor beziehungsweise rückwärts dahinter |
| `;`, `,` | Letzte `f`-/`t`-Suche wiederholen beziehungsweise umkehren |
| `gg`, `G`, `42G` | Dateianfang, Dateiende, Zeile 42 |
| `%` | Passende Klammer finden |
| `{`, `}` | Absatz zurück beziehungsweise vor |
| `gj`, `gk` | Bei weichem Umbruch eine Bildschirmzeile abwärts beziehungsweise aufwärts |
| `Ctrl-D`, `Ctrl-U` | Etwa eine halbe Fensterhöhe abwärts beziehungsweise aufwärts |
| `Ctrl-F`, `Ctrl-B` | Seitenweise abwärts beziehungsweise aufwärts |
| `zz`, `zt`, `zb` | Cursorzeile mittig, oben beziehungsweise unten anzeigen |

Eine vorangestellte Zahl wiederholt viele Bewegungen: `5j`, `3w`, `2f;`. Bei `w` hängt die Wortzerlegung unter anderem von `'iskeyword'` ab; `W` übergeht Satzzeichen innerhalb eines zusammenhängenden WORDs. [Bewegungen im Handbuch](https://vimhelp.org/usr_03.txt.html).

### Positionen wiederfinden

| Befehl | Wirkung |
|---|---|
| `ma` | Lokale Marke `a` setzen |
| `'a` | Zur ersten Nichtleerstelle der markierten Zeile |
| `` `a `` | Zur exakten markierten Position |
| `mA` | Dateiübergreifende Marke `A` setzen |
| `Ctrl-O`, `Ctrl-I` | Ältere beziehungsweise neuere Sprungposition |
| `g;`, `g,` | Ältere beziehungsweise neuere Änderungsposition |
| `:marks`, `:jumps`, `:changes` | Die jeweiligen Listen anzeigen |

Sprungliste und Änderungsliste haben unterschiedliche Aufgaben: Die erste hilft nach Suchen und Dateisprüngen zurück; die zweite führt zu bearbeiteten Stellen. [Marken und Sprünge](https://vimhelp.org/motion.txt.html).

## Operatoren und Textobjekte

Vims Befehlssprache folgt häufig diesem Muster:

```text
[Anzahl] Operator [Anzahl] Bewegung-oder-Textobjekt
```

| Operator | Aufgabe | Beispiel |
|---|---|---|
| `d` | Löschen und in Register aufnehmen | `d$`: bis Zeilenende löschen |
| `c` | Löschen und Insertmodus beginnen | `ciw`: Wort ersetzen |
| `y` | Kopieren, in Vim „yank“ | `yy`: ganze Zeile kopieren |
| `>`, `<` | Einrückung erhöhen beziehungsweise verringern | `>>`, `<<`: aktuelle Zeile |
| `=` | Einrückung neu berechnen | `gg=G`: gesamte Datei einrücken |
| `gq` | Text entsprechend den Formatoptionen umbrechen | `gqap`: Absatz formatieren |
| `gu`, `gU` | Klein beziehungsweise groß schreiben | `gUiw`: Wort groß schreiben |

`dd`, `cc` und `yy` arbeiten zeilenweise; `3dd` löscht drei Zeilen. Bei `2d3w` werden die Zahlen multipliziert: gelöscht wird über sechs `w`-Bewegungen. Die genauen Grenzen folgen der Bewegung. `=` steuert die Einrückung; `gq` kann zusätzlich Zeilen umbrechen, etwa anhand von `'textwidth'`. [Ändern mit Operatoren](https://vimhelp.org/usr_04.txt.html), [Textformatierung](https://vimhelp.org/usr_25.txt.html).

### Textobjekte

| Innerhalb | Mit Umgebung | Bereich |
|---|---|---|
| `iw` | `aw` | Wort; `aw` erfasst angrenzenden Leerraum |
| `iW` | `aW` | WORD |
| `ip` | `ap` | Absatz; `ap` schließt angrenzende Leerzeilen ein |
| `i"` | `a"` | Doppelte Anführungszeichen |
| `i'` | `a'` | Einfache Anführungszeichen |
| `i(` | `a(` | Runde Klammern; auch `ib` beziehungsweise `ab` |
| `i[` | `a[` | Eckige Klammern |
| `i{` | `a{` | Geschweifte Klammern; auch `iB` beziehungsweise `aB` |
| `it` | `at` | Inhalt eines Tags beziehungsweise Tag samt Inhalt |

Beispiele mit dem Cursor im betreffenden Bereich:

```text
ci"neu<Esc>       Inhalt eines Strings durch neu ersetzen
yi(               Inhalt runder Klammern kopieren
da{               Klammerblock einschließlich Klammern löschen
vip               Absatzinhalt auswählen
```

`cw` beginnt an der Cursorposition und hat eine Sonderbehandlung am Wortende. `ciw` erfasst das ganze Wort auch dann, wenn der Cursor mittendrin steht. Textobjekte wie `iw` folgen einem Operator oder werden im Visualmodus benutzt. [Textobjekte](https://vimhelp.org/motion.txt.html), [Besonderheit von `cw`](https://vimhelp.org/change.txt.html).

## Einfügen und visuelle Auswahl

### Text eingeben

| Taste im Normalmodus | Wirkung |
|---|---|
| `i`, `a` | Vor beziehungsweise nach dem Cursor einfügen |
| `I`, `A` | Vor dem ersten Nichtleerzeichen beziehungsweise am Zeilenende einfügen |
| `o`, `O` | Neue Zeile unterhalb beziehungsweise oberhalb öffnen |
| `rX` | Ein Zeichen durch `X` ersetzen |
| `x`, `D`, `C` | Zeichen löschen, bis Zeilenende löschen beziehungsweise ändern |
| `J` | Mit Folgezeile verbinden und Abstand behandeln |
| `gJ` | Verbinden, vorhandenen Leerraum erhalten, keinen zusätzlichen einfügen |

Im Insertmodus:

```text
Ctrl-W       Vorheriges Wort löschen
Ctrl-N       Nächsten Vervollständigungsvorschlag auswählen
Ctrl-P       Vorherigen Vervollständigungsvorschlag auswählen
Ctrl-R a     Inhalt von Register a einfügen
Ctrl-O       Einen Normalmodusbefehl ausführen, dann weiter einfügen
```

Die Vervollständigung mit `Ctrl-N`/`Ctrl-P` nutzt vorhandene Textquellen gemäß `'complete'`; sie benötigt keinen Sprachserver. [Einfügen und Vervollständigung](https://vimhelp.org/insert.txt.html), [Register beim Einfügen](https://vimhelp.org/usr_24.txt.html).

### Auswahl bearbeiten

Nach `v`, `V` oder `Ctrl-V` mit Bewegungen auswählen und anschließend etwa `y`, `d`, `c`, `>` oder `=` anwenden. `o` wechselt das aktive Auswahlende; `gv` stellt die letzte Auswahl wieder her.

**Mehrere Zeilen gleich beginnen lassen:**

1. Den Cursor auf die erste gewünschte Spalte setzen.
2. Mit `Ctrl-V` und `j` weitere Zeilen markieren.
3. `I` drücken und beispielsweise `# ` eingeben.
4. Mit `Esc` abschließen; erst dabei erscheint die Einfügung auch in den übrigen ausgewählten Zeilen.

Das ist eine rechteckige Auswahl. Bei Tabs und unterschiedlich langen Zeilen den Spaltenbereich prüfen. [Visualmodus und Blockbearbeitung](https://vimhelp.org/visual.txt.html).

## Undo und Wiederholung

| Befehl | Aufgabe |
|---|---|
| `u` | Letzte Änderung rückgängig machen |
| `Ctrl-R` | Rückgängig gemachte Änderung erneut anwenden |
| `.` | Letzte wiederholbare Textänderung an der aktuellen Position ausführen |
| `:earlier 5m` | Zu einem früheren Bearbeitungszustand wechseln |
| `:later 5m` | In der Änderungshistorie wieder vorwärts wechseln |
| `:undolist` | Endpunkte der vorhandenen Undo-Zweige anzeigen |

Beispiel: `ciwName<Esc>` ersetzt ein Wort. Zum nächsten Ziel wechseln und `.` drücken. Cursorbewegungen und das Kopieren mit `y` werden dadurch nicht wiederholt.

Undo besitzt Verzweigungen: Nach `u` neu zu schreiben löscht nicht einfach jeden früheren Bearbeitungsweg. Dauerhafte Undo-Dateien müssen mit `'undofile'` eingerichtet werden; siehe [[Vimrc-Konfiguration-Cheatsheet]]. [Undo und Zeitnavigation](https://vimhelp.org/undo.txt.html), [Wiederholen](https://vimhelp.org/repeat.txt.html).

## Dateien, Buffer, Fenster und Tabs

| Begriff | Bedeutung |
|---|---|
| Datei | Gespeicherter Inhalt im Dateisystem |
| Buffer/Puffer | Von Vim verwalteter Text; kann ungesichert oder unbenannt sein |
| Fenster | Ansicht auf einen Puffer; mehrere Fenster können denselben Puffer zeigen |
| Tabpage | Anordnung mehrerer Fenster; keine zwingende Eins-zu-eins-Zuordnung zu Dateien |

[Puffer und Fenster](https://vimhelp.org/windows.txt.html), [Tabpages](https://vimhelp.org/tabpage.txt.html).

### Dateien und Puffer

```vim
:edit andere.txt
:ls
:bnext
:bprevious
:buffer 3
:buffer #
:bdelete
:pwd
:lcd /pfad/zum/projekt
```

`:ls` zeigt Puffer, `:buffer #` den alternativen Puffer. `:bdelete` nimmt einen Puffer aus der normalen Pufferliste; es löscht keine Datei auf dem Datenträger. `:lcd` setzt das Arbeitsverzeichnis für das aktuelle Fenster. [Pufferbefehle](https://vimhelp.org/windows.txt.html).

| Speichern unter anderem Namen | Ergebnis |
|---|---|
| `:write kopie.txt` | Schreibt eine Kopie; bei einem bereits benannten Puffer bleibt der aktuelle Dateiname erhalten |
| `:saveas neuer-name.txt` | Schreibt unter neuem Namen und bindet den aktuellen Puffer an diesen Namen |

`:saveas` entfernt die vorherige Datei nicht. Bei unbenannten Puffern kann schon `:write name.txt` den Namen setzen. [Mehrere Dateien und Speichern unter neuem Namen](https://vimhelp.org/usr_07.txt.html).

Bei „No write since last change“ zuerst speichern oder bewusst `:set hidden` verwenden. `hidden` erlaubt ungesicherte Puffer ohne sichtbares Fenster; es speichert sie nicht automatisch. Das `+` in `:ls` kennzeichnet Änderungen.

### Fenster und Tabs

| Befehl | Wirkung |
|---|---|
| `:split datei.txt`, `:vsplit datei.txt` | Horizontal beziehungsweise vertikal teilen |
| `Ctrl-W h/j/k/l` | Zum benachbarten Fenster wechseln |
| `Ctrl-W w` | Fenster zyklisch wechseln |
| `Ctrl-W =` | Fenstergrößen ausgleichen |
| `Ctrl-W H/J/K/L` | Fenster an den entsprechenden äußeren Rand verschieben |
| `:close` | Aktuelles Fenster schließen; letztes Fenster bleibt bestehen |
| `:only` | Andere Fenster der Tabpage schließen, sofern Änderungen das zulassen |
| `:tabedit datei.txt` | Neue Tabpage mit Datei öffnen |
| `gt`, `gT`, `3gt` | Nächste, vorherige beziehungsweise dritte Tabpage |
| `:tabs`, `:tabclose` | Tabpages auflisten beziehungsweise aktuelle schließen |

Beispiel: Links Quellcode, rechts Tests als zwei Fenster; eine zweite Tabpage enthält ein Diff. Alle Ansichten können dieselbe Pufferliste nutzen. [Fensterpraxis](https://vimhelp.org/usr_08.txt.html), [Tabpage-Befehle](https://vimhelp.org/tabpage.txt.html).

## Suchen und Ersetzen

### Suche und Groß-/Kleinschreibung

| Eingabe | Wirkung |
|---|---|
| `/fehler` | Vorwärts nach Muster suchen, mit `Enter` starten |
| `?fehler` | Rückwärts suchen |
| `n`, `N` | In der letzten Suchrichtung beziehungsweise entgegengesetzt weitersuchen |
| `*`, `#` | Wort unter dem Cursor vorwärts beziehungsweise rückwärts suchen |
| `:nohlsearch` | Aktuelle Trefferhervorhebung ausblenden |

Mit diesen Optionen werden Treffer während der Eingabe gesucht und anschließend hervorgehoben:

```vim
:set incsearch hlsearch
:set ignorecase smartcase
```

Unter `ignorecase smartcase` gilt für manuell eingegebene Muster:

| Muster | Findet beispielsweise |
|---|---|
| `/fehler` | `fehler`, `Fehler`, `FEHLER` |
| `/Fehler` | `Fehler` mit genau dieser Groß-/Kleinschreibung |
| `/\cFehler` | Alle drei Varianten, unabhängig von den Suchoptionen |
| `/\Cfehler` | Nur `fehler`, unabhängig von den Suchoptionen |

`\c` erzwingt eine Suche ohne Beachtung der Groß-/Kleinschreibung, `\C` eine Suche mit deren Beachtung. Beide wirken auf das ganze Muster. `smartcase` setzt `ignorecase` voraus. `*` und `#` berücksichtigen `smartcase` nicht. [Suchpraxis](https://vimhelp.org/usr_27.txt.html), [Option `'smartcase'`](https://vimhelp.org/options.txt.html#%27smartcase%27).

### Reguläre Ausdrücke

```vim
/\<fehler\>
/\Vdatei[1].txt
/\v(fehler|warnung)+
```

Das erste Muster nutzt Wortgrenzen. `\V` reduziert Sonderzeichen auf ein Minimum; Backslashes und das verwendete Suchtrennzeichen müssen weiterhin passend behandelt werden. `\v` aktiviert „very magic“, sodass beispielsweise Klammern und `|` direkt Regex-Bedeutung haben. Vims Regex-Syntax ist nicht in allen Einzelheiten mit PCRE identisch. [Musterreferenz](https://vimhelp.org/pattern.txt.html).

### Ersetzen mit Kontrolle

```vim
:s/alt/neu/
:s/alt/neu/g
:%s/alt/neu/gc
:10,20s/alt/neu/gc
:'<,'>s/alt/neu/gc
:%s/\<alt\>/neu/gc
:%s#alter/pfad#neuer/pfad#gc
:%s/alt/neu/gn
```

| Bestandteil | Bedeutung |
|---|---|
| Kein Bereich | Aktuelle Zeile |
| `%` | Alle Zeilen |
| `10,20` | Zeilen 10 bis 20 |
| `'<,'>` | Die von der letzten visuellen Auswahl erfassten Zeilen |
| `g` | Alle Treffer je Zeile |
| `c` | Jede Ersetzung bestätigen |
| `n` | Treffer nur zählen |
| `i`, `I` | Groß-/Kleinschreibung ignorieren beziehungsweise beachten |

Die Beispiele setzen `nogdefault` und `noedcompatible` voraus. Mit `gdefault` kehrt das `g`-Flag seine Bedeutung um. Beim Bestätigen heißt `y` ersetzen, `n` überspringen, `a` alle übrigen ersetzen, `q` beenden. Die Auswahlgrenzen `'<,'>` begrenzen **Zeilen**, nicht automatisch einzelne ausgewählte Spalten. [Ersetzungen und Flags](https://vimhelp.org/change.txt.html).

Eine Gruppierung kann Text umstellen:

```vim
:%s/\v([A-Za-z]+), ([A-Za-z]+)/\2 \1/gc
```

Damit wird etwa `Muster, Anna` zu `Anna Muster`. Die Beispielklassen erfassen bewusst nur ASCII-Buchstaben. Im Ersetzungsteil bezeichnet `&` den gesamten Treffer, `\1` die erste Gruppe und `\r` einen neuen Zeilenumbruch. Ein wörtliches `&` wird dort als `\&` geschrieben. [Ersetzungen im Handbuch](https://vimhelp.org/usr_12.txt.html), [komplexe Änderungen](https://vimhelp.org/usr_10.txt.html).

## Register und Zwischenablage

Vim speichert kopierten und gelöschten Text in Registern. Das Präfix `"a` wählt Register `a`; es gehört unmittelbar vor den Befehl.

| Register | Zweck |
|---|---|
| `"` | Standardregister für gewöhnliche Kopier-, Lösch- und Einfügevorgänge |
| `0` | Letzter Yank, sofern kein anderes Register ausdrücklich angegeben war |
| `1`–`9` | Historie größerer Lösch-/Änderungsoperationen |
| `-` | Kleine Löschungen; bestimmte Bewegungen haben Sonderregeln |
| `a`–`z` | Benannte Register; Großbuchstaben beim Schreiben hängen an |
| `_` | Verwerfen, ohne die üblichen Textregister zu überschreiben |
| `+`, `*` | Systemzwischenablage beziehungsweise systemabhängige Auswahl |

```text
"ayy        Zeile nach Register a kopieren
"Ayy        Weitere Zeile an a anhängen
"ap         Register a einfügen
"0p         Letzten gewöhnlichen Yank einfügen
"_dd        Zeile verwerfen, Kopierregister bewahren
```

`:registers` zeigt die Inhalte. `p` setzt zeichenweisen Text nach dem Cursor und zeilenweisen Text unter die aktuelle Zeile; `P` entsprechend davor beziehungsweise darüber. [Kopieren und Register](https://vimhelp.org/change.txt.html).

### Austausch mit anderen Anwendungen

```text
"+yy        Zeile in die Systemzwischenablage kopieren
"+p         Systemzwischenablage einfügen
```

Im Visualmodus kopiert `"+y` die Auswahl. Unter X11 unterscheidet Vim `+` für CLIPBOARD und `*` für PRIMARY; auf anderen Plattformen hängt die Zuordnung von der Integration ab. Die beiden Register sind nicht allgemein austauschbar. [Zwischenablage im Handbuch](https://vimhelp.org/usr_09.txt.html), [X11-Auswahl und Clipboard](https://vimhelp.org/gui_x11.txt.html).

Voraussetzung ist eine funktionierende Clipboard-Anbindung des jeweiligen Builds und der Sitzung. Prüfen:

```vim
:version
:set clipboard?
:help clipboard
```

Neuere Vim-Versionen unterstützen zusätzlich Clipboard-Provider und Wayland-Integration. Deshalb beweist `has('clipboard')` allein nicht für jede Ausgabe die gesamte Verfügbarkeit. Auch eine entfernte SSH-Sitzung erhält nicht automatisch Zugriff auf die Zwischenablage des lokalen Rechners. Konfiguration und Optionen: [[Vimrc-Konfiguration-Cheatsheet]], [Clipboard-Dokumentation](https://vimhelp.org/options.txt.html#%27clipboard%27).

> [!tip] Nach dem Kopieren kommt plötzlich anderer Text
> Gewöhnliches Löschen verändert das Standardregister. Nach `yy` und anschließendem `dd` holt `"0p` den kopierten Text zurück. Für länger benötigten Text ausdrücklich `"ayy` und `"ap` verwenden. Auch das Ersetzen einer visuellen Auswahl mit `p` kann das Standardregister verändern.

## Makros

| Eingabe | Wirkung |
|---|---|
| `qa` | Tastenfolge in Register `a` aufzeichnen |
| `q` | Aufzeichnung beenden |
| `@a` | Makro aus Register `a` ausführen |
| `5@a` | Fünfmal ausführen |
| `@@` | Zuletzt ausgeführtes Makro wiederholen |
| `qA` | Weitere Tasten an Makro `a` anhängen |

Beispiel: Mehreren aufeinanderfolgenden Zeilen `# ` voranstellen. Auf der ersten Zeile beginnen; unter ihr müssen weitere Zielzeilen folgen:

```text
qa0i# <Esc>jq
```

`qa` startet die Aufnahme, `0` geht an den Zeilenanfang, `i# ` fügt den Präfix ein, `Esc` beendet die Eingabe, `j` wechselt zur Folgezeile, `q` stoppt. **Die erste Zeile wurde bereits während der Aufnahme verändert.** Danach mit `@a` die nächste bearbeiten und das Ergebnis prüfen, bevor ein größerer Zähler verwendet wird.

Makros und kopierter Text teilen sich Register. `"ayy` würde Makro `a` überschreiben. Für belastbare Makros Bewegungen wie `0`, `f;` oder Suchen verwenden, deren Ziel klar bestimmt ist. [Makroaufnahme und Wiedergabe](https://vimhelp.org/repeat.txt.html).

## Quickfix und Projektsuche

Quickfix sammelt Positionen aus mehreren Dateien. Diese interne Suche benötigt kein externes `grep`:

```vim
:vimgrep /\cTODO/gj **/*.md
:copen
:cfirst
:cnext
:cprevious
:cclose
```

`**/*.md` durchsucht passende Markdown-Dateien unter dem Arbeitsverzeichnis. `g` nimmt jeden Treffer auf; `j` verhindert den sofortigen Sprung beim Suchen. `:copen` zeigt die Ergebnisliste, `Enter` auf einem Eintrag öffnet dessen Position. `:colder` und `:cnewer` wechseln zwischen älteren Ergebnislisten.

**`:vimgrep` verwendet `ignorecase`, aber kein `smartcase`.** Deshalb steht im Beispiel ausdrücklich `\c`; für exakte Groß-/Kleinschreibung `\C` verwenden.

Die Location List gehört zu einem Fenster: `:lvimgrep`, `:lopen`, `:lnext` und `:lprevious` sind die entsprechenden Befehle. `:make` kann Compilerfehler liefern, wenn `'makeprg'` und `'errorformat'` passen. Die Verfügbarkeit setzt die Quickfix-Funktion des Builds voraus. [Offizielle Quickfix-Referenz](https://vimhelp.org/quickfix.txt.html).

## Dateien mit vimdiff vergleichen

```bash
vimdiff alt.txt neu.txt
```

Alternativ `vim -d alt.txt neu.txt`. Innerhalb einer Sitzung kann `:vert diffsplit andere.txt` die zweite Vergleichsansicht öffnen.

| Befehl | Wirkung |
|---|---|
| `]c`, `[c` | Nächster beziehungsweise vorheriger Unterschied |
| `do` oder `:diffget` | Unterschied aus anderem Puffer in den aktuellen übernehmen |
| `dp` oder `:diffput` | Unterschied aus aktuellem Puffer in den anderen übertragen |
| `:diffget 3` | Puffer Nummer 3 ausdrücklich als Quelle wählen |
| `:diffupdate` | Vergleich neu berechnen |
| `:diffoff!` | Diffmodus in den Fenstern der aktuellen Tabpage ausschalten |

Die Richtung richtet sich immer nach dem **aktuellen Fenster**. Bei mehreren Vergleichspuffern mit `:ls` die Nummern prüfen und Quelle beziehungsweise Ziel ausdrücklich angeben. `diffget` verändert den aktuellen, `diffput` einen anderen Puffer; gespeichert wird anschließend separat mit `:w` oder `:wall`. [Diffmodus und Übernahmerichtung](https://vimhelp.org/diff.txt.html).

## Externe Befehle und Textfilter

| Befehl innerhalb von Vim | Wirkung |
|---|---|
| `:!git status --short` | Externes Git ausführen und Ausgabe anzeigen |
| `:read zusatz.txt` | Datei unterhalb der aktuellen Zeile einfügen |
| `:read !date` | Ausgabe des externen `date`-Programms einfügen |
| `:'<,'>!sort` | Ausgewählte Zeilen durch Ausgabe des externen Sortierprogramms ersetzen |

Shellbefehle laufen mit den Rechten des Vim-Prozesses. Die Programme und ihre Syntax hängen vom Betriebssystem ab; `date` und `sort` sind hier Unix-Beispiele. Ein Filter verändert den Text im Puffer. Rückgängig machen ist mit `u` möglich, externe Nebenwirkungen eines Programms werden dadurch nicht rückgängig gemacht. [Shellbefehle](https://vimhelp.org/usr_20.txt.html), [Filter](https://vimhelp.org/usr_10.txt.html).

## Hilfe, Diagnose und Wiederherstellung

### Die eingebaute Referenz benutzen

```vim
:help
:help user-manual
:help quickref
:help :substitute
:help 'number'
:help text-objects
:help i_CTRL-R
:help E325
```

Optionen stehen in Apostrophen, Ex-Befehle beginnen im Hilfebegriff mit `:`, Insertbefehle haben häufig das Präfix `i_`. Mit `Ctrl-]` einem Hilfelink folgen, mit `Ctrl-T` zurückgehen und mit `:q` das Hilfefenster schließen. [Hilfe im Handbuch](https://vimhelp.org/usr_02.txt.html).

### Auffälliges Verhalten eingrenzen

```vim
:version
:messages
:scriptnames
:verbose set ignorecase? smartcase?
:verbose nmap <C-W>
:setlocal fileformat? fileencoding?
```

`:verbose set` nennt neben dem Wert häufig die Datei, die eine Option zuletzt gesetzt hat. Die ausführliche Mappinganzeige hilft bei überschriebenen Tasten. [Diagnosebefehle](https://vimhelp.org/various.txt.html), [[Vimrc-Konfiguration-Cheatsheet|Konfiguration systematisch prüfen]].

Zum Vergleich ohne eigene Einrichtung eine zusätzliche Sitzung starten:

```bash
vim --clean notizen.txt
vim -Nu NONE -i NONE notizen.txt
```

`--clean` lädt Vims `defaults.vim`, ohne Benutzerkonfiguration, Plugins oder Viminfo. Die zweite Variante lässt auch `defaults.vim` weg; `-N` aktiviert ausdrücklich Vims Verhalten statt Vi-Kompatibilität. Beide Varianten liefern daher nicht dieselben Voreinstellungen. [Sauberer Start](https://vimhelp.org/starting.txt.html).

| Symptom | Erklärung und nächster Schritt |
|---|---|
| `E37: No write since last change` | Puffer geändert: speichern oder bewusst versteckt weiterführen |
| `E45: 'readonly' option is set` | Vim-Schreibschutz aktiv; `:w!` kann diese Option übergehen, aber keine fehlenden Betriebssystemrechte ersetzen |
| `E212: Can't open file for writing` | Zielpfad, Verzeichnis und Schreibrechte prüfen; benötigten Inhalt unter beschreibbarem Namen sichern |
| `n` sucht in die unerwartete Richtung | `n` folgt der zuletzt begonnenen Suchrichtung, also auch einer `?`-Suche |
| Unerwartete Einrückung nach Einfügen | Clipboard- und Terminalverhalten sowie `'paste'` prüfen; Details auf der `.vimrc`-Seite |
| `E325: ATTENTION`, vorhandene Swap-Datei | Prüfen, ob eine andere Sitzung aktiv ist oder eine abgestürzte Sitzung wiederhergestellt werden muss |

### Nach einem Absturz retten

Eine Swap-Datei kann ungesicherte Änderungen enthalten. **Zuerst klären, ob die angegebene Sitzung noch läuft.** Eine aktive Swap-Datei nicht entfernen und denselben Inhalt nicht parallel überschreiben.

Bei einer abgestürzten Sitzung:

1. Im Verzeichnis der betroffenen Datei `vim -r` ausführen, um auffindbare Swap-Dateien aufzulisten.
2. Mit `vim -r notizen.txt` die Wiederherstellung starten.
3. Meldungen lesen und den wiederhergestellten Inhalt prüfen.
4. Mit `:write notizen.gerettet.txt` zunächst separat sichern.
5. Original und gerettete Datei mit `vimdiff notizen.txt notizen.gerettet.txt` vergleichen.
6. Erst nach erfolgreicher Sicherung und Vergleich die tatsächlich verwaiste Swap-Datei entfernen.

Die allerletzten Änderungen können fehlen, wenn Vim sie vor dem Absturz noch nicht in die Swap-Datei geschrieben hatte. Swap, dauerhaftes Undo und Sicherungskopien erfüllen unterschiedliche Aufgaben; ihre Einrichtung steht in [[Vimrc-Konfiguration-Cheatsheet]]. [Wiederherstellung Schritt für Schritt](https://vimhelp.org/usr_11.txt.html), [technische Recovery-Referenz](https://vimhelp.org/recover.txt.html).

## Kleine Praxisübung

Diese Übung verbindet die wichtigsten Handgriffe in einer wegwerfbaren Testdatei:

1. `vim vim-uebung.txt` starten; mit `i` einige Zeilen eingeben, darunter `status = "alt"`, `Esc` und `:w`.
2. Mit `/alt` und `Enter` zum String gehen; `ci"neu<Esc>` ersetzt seinen Inhalt.
3. Mit `yy` die Zeile kopieren, mit `o` eine neue Zeile öffnen, `Esc` und `"0p` zum Einfügen verwenden.
4. Mit `u` rückgängig machen, mit `Ctrl-R` wiederholen.
5. `:%s/\Cneu/aktuell/gc` ausführen und die Ersetzungen einzeln prüfen.
6. Mit `:vsplit` denselben Puffer ein zweites Mal anzeigen; `Ctrl-W w` wechselt die Ansicht.
7. `:wall` speichert den Inhalt; `:qall` beendet die Sitzung.

Als nächste Erweiterung die [[Vimrc-Konfiguration-Cheatsheet|kommentierte `.vimrc`]] ausprobieren und die Bedeutung der übernommenen Optionen prüfen.

## Quellen und verwandte Seiten

Die verlinkten Seiten enthalten die offizielle Vim-Dokumentation. [vim.org verweist auf vimhelp.org](https://www.vim.org/docs.php) als aufbereitete Online-Ausgabe. Maßgeblich für einen installierten Build bleibt dessen lokale Hilfe. **Recherche- und Dokumentstand: 12. Oktober 2026.**

| Thema | Primärquelle und lokaler Einstieg |
|---|---|
| Gesamte Dokumentation | [Vim-Hilfe](https://vimhelp.org/), `:help` |
| Befehlsübersicht | [Quick Reference](https://vimhelp.org/quickref.txt.html), `:help quickref` |
| Bewegungen und Textobjekte | [Motion Reference](https://vimhelp.org/motion.txt.html), `:help motion.txt` |
| Suche und Ersetzen | [Muster](https://vimhelp.org/pattern.txt.html), [Änderungen](https://vimhelp.org/change.txt.html), `:help :substitute` |
| Puffer, Fenster und Tabs | [Fenster](https://vimhelp.org/windows.txt.html), [Tabpages](https://vimhelp.org/tabpage.txt.html), `:help windows.txt` |
| Automatisierung und Trefferlisten | [Makros](https://vimhelp.org/repeat.txt.html), [Quickfix](https://vimhelp.org/quickfix.txt.html) |
| Diff und Rettung | [Diff](https://vimhelp.org/diff.txt.html), [Recovery](https://vimhelp.org/recover.txt.html) |
| Konfiguration und Features | [Start](https://vimhelp.org/starting.txt.html), [Optionen](https://vimhelp.org/options.txt.html), `:version` |
| Offizieller Quellcode und Dokumentation | [vim/vim](https://github.com/vim/vim) |

Verwandte Notizen:

- [[Vimrc-Konfiguration-Cheatsheet|.vimrc – Konfiguration und Praxis]]
- [[Neovim-Cheatsheet|Neovim – Cheatsheet]]
- [[Neovim-Shortcuts-und-Bewegungen|Neovim – Bewegungen und Textobjekte]]
- [[02-Versionierung-Entwicklung/INDEX|Versionierung, Entwicklung und Editoren]]
