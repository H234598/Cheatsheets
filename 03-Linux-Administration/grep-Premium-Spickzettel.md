---
title: "grep – Premium-Spickzettel"
aliases: ["grep Cheatsheet", "Textsuche Linux", "Regex grep"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, grep, regex, shell, textverarbeitung]
source: "https://www.gnu.org/software/grep/manual/grep.html"
---

# grep – Premium-Spickzettel

> [!abstract] Zweck
> Ausführliche Referenz für grep, reguläre Ausdrücke, rekursive und binärsichere Suche, Kontext, Dateifilter, Nullterminierung, Performance, Pipelines und robuste Skripte.

> [!abstract] Merksatz
> `grep` beantwortet drei Fragen: **wo** wird gesucht, **welches Muster** gilt und **welche Ausgabeform** wird benötigt. Erst diese drei Punkte explizit machen, dann Optionen ergänzen.

## Inhalt

- [[#Grundsyntax]]
- [[#BRE, ERE und PCRE]]
- [[#Wichtige Optionen]]
- [[#Rekursive Suche]]
- [[#Kontext und Ausgabe]]
- [[#Nullterminierte Daten]]
- [[#Pipelines und Skripte]]
- [[#Performance und Alternativen]]
- [[#Typische Fehler]]
- [[#Schnellrezepte]]

## Grundsyntax

```bash
grep [OPTIONEN] MUSTER [DATEI...]
```

Beispiele:

```bash
grep 'error' app.log
grep -i 'error' app.log
grep -n 'error' app.log
grep -v '^#' config.conf
```

Mehrere Muster:

```bash
grep -e 'ERROR' -e 'WARN' app.log
grep -f muster.txt app.log
```

Exakter String statt Regex:

```bash
grep -F 'a[b]*c' datei.txt
```

Ganzes Wort oder ganze Zeile:

```bash
grep -w 'root' /etc/passwd
grep -x 'READY' status.txt
```

## BRE, ERE und PCRE

| Modus | Option | Einsatz |
|---|---|---|
| Basic Regular Expression | Standard | POSIX-Basis, einige Zeichen müssen escaped werden |
| Extended Regular Expression | `-E` | `+`, `?`, `|`, Gruppen ohne Backslash |
| Fixed Strings | `-F` | keine Regex, schnell und sicher für Literale |
| Perl-kompatibel | `-P` | Lookarounds und weitere Features; Portabilität eingeschränkt |

ERE-Beispiel:

```bash
grep -E '^(ERROR|WARN)[[:space:]]+[0-9]+' app.log
```

PCRE-Beispiel:

```bash
grep -P '(?<=user=)[^ ]+' app.log
```

> [!warning]
> Shellquoting und Regexescaping sind zwei getrennte Ebenen. Reguläre Ausdrücke fast immer in **einfachen Anführungszeichen** schreiben, damit die Shell `$`, `*`, `\` und Backticks nicht verändert.

Nützliche Klassen:

```text
[[:alpha:]]  Buchstaben
[[:digit:]]  Ziffern
[[:alnum:]]  Buchstaben/Ziffern
[[:space:]]  Whitespace
[[:blank:]]  Leerzeichen/Tab
[[:xdigit:]] Hexziffern
```

Anker:

```text
^   Zeilenanfang
$   Zeilenende
.   beliebiges Zeichen
*   null oder mehr
```

## Wichtige Optionen

| Option | Wirkung |
|---|---|
| `-i` | Groß-/Kleinschreibung ignorieren |
| `-n` | Zeilennummer |
| `-H` / `-h` | Dateiname zeigen / unterdrücken |
| `-c` | Trefferzeilen zählen |
| `-l` / `-L` | Dateien mit / ohne Treffer |
| `-o` | nur passenden Teil ausgeben |
| `-q` | keine Ausgabe, nur Exitcode |
| `-v` | Auswahl invertieren |
| `-m N` | nach N Treffern pro Datei stoppen |
| `--color=auto` | Treffer markieren |
| `-s` | Fehlermeldungen unterdrücken – vorsichtig |

Exitcodes:

| Code | Bedeutung |
|---:|---|
| `0` | mindestens ein Treffer |
| `1` | kein Treffer |
| `2` | Fehler |

Robustes Skript:

```bash
if grep -qF 'READY' status.txt; then
  echo 'bereit'
else
  rc=$?
  if [ "$rc" -eq 1 ]; then
    echo 'nicht bereit'
  else
    echo 'grep-Fehler' >&2
    exit "$rc"
  fi
fi
```

## Rekursive Suche

```bash
grep -RIn 'TODO' .
```

`-r` folgt symbolischen Links typischerweise nicht vollständig, `-R` dereferenziert alle. Symlink-Schleifen und fremde Mounts bedenken.

Dateitypen begrenzen:

```bash
grep -RIn --include='*.py' 'TODO' src/
grep -RIn --include='*.{c,h}' 'deprecated' .
grep -RIn --exclude='*.min.js' 'token' web/
grep -RIn --exclude-dir={.git,node_modules,.venv} 'password' .
```

Binärdateien behandeln:

```bash
grep -I -R 'text' .              # Binärdateien ignorieren
grep -a 'text' unbekannt.bin     # als Text behandeln
grep --binary-files=without-match 'text' datei
```

> [!tip]
> Für Quellcode-Repositories ist `rg`/ripgrep meist schneller und respektiert standardmäßig `.gitignore`. `grep` bleibt jedoch universeller und nahezu überall verfügbar.

## Kontext und Ausgabe

```bash
grep -n -C 3 'panic' log.txt     # 3 davor und danach
grep -n -B 5 'panic' log.txt     # davor
grep -n -A 10 'panic' log.txt    # danach
```

Nur Trefferteile:

```bash
grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' access.log
```

Eindeutig zählen:

```bash
grep -oE 'status=[0-9]+' app.log | sort | uniq -c | sort -nr
```

Dateinamen sicher ausgeben:

```bash
grep -lZ 'needle' -- *.txt
```

## Nullterminierte Daten

Dateinamen können Leerzeichen, Tabs und Zeilenumbrüche enthalten. Für robuste Verarbeitung Nullbytes verwenden:

```bash
find . -type f -print0 |
  xargs -0 grep -HnF 'MUSTER'
```

GNU grep kann Nullterminierung ausgeben:

```bash
grep -rlZ 'MUSTER' . |
  xargs -0 -r chmod 0640
```

> [!danger]
> Destruktive Befehle niemals direkt an eine ungeprüfte Trefferpipeline hängen. Erst Ausgabe prüfen, dann `printf`/Dry-Run, danach gezielt ausführen.

## Pipelines und Skripte

Journal durchsuchen:

```bash
journalctl -u nginx --since today --no-pager |
  grep -Ei 'error|critical|timeout'
```

Prozessausgabe ohne `grep grep`:

```bash
pgrep -af nginx
```

Konfigurationszeilen ohne Kommentare/Leerzeilen:

```bash
grep -Ev '^[[:space:]]*($|#)' /etc/ssh/sshd_config
```

CSV ist kein simples Textformat. Für gequotete Felder mit Kommas nicht `grep`/`cut` als Parser missbrauchen; Python, Miller, csvkit oder passende Bibliothek verwenden.

Mit `set -o pipefail`:

```bash
set -o pipefail
producer | grep -q 'READY'
```

Beachten: `grep -q` beendet früh, wodurch der Producer SIGPIPE bekommen kann. In strikten Skripten diesen Effekt bewusst behandeln.

## Performance und Alternativen

- Literale mit `-F` statt Regex suchen.
- Suchbaum mit `--include`, `--exclude-dir` und Startpfad begrenzen.
- Binärdateien mit `-I` überspringen.
- Keine unnötige `cat datei | grep`; direkt `grep muster datei`.
- Für sehr große Codebäume `rg`, für interaktive fuzzy Auswahl `fzf`.
- Locale kann beeinflussen: für byteorientierte schnelle Suche gegebenenfalls `LC_ALL=C`, aber Unicode-Semantik ändert sich.

```bash
LC_ALL=C grep -F 'literal' riesig.log
```

## Typische Fehler

| Problem | Ursache | Lösung |
|---|---|---|
| Muster beginnt mit `-` | als Option interpretiert | `grep -- '-foo' datei` |
| Stern expandiert durch Shell | Muster nicht gequotet | `'a.*b'` |
| kein Treffer beendet Skript | Exitcode 1 bei `set -e` | explizit behandeln |
| „Binary file matches“ | Binärerkennung | `-I`, `-a` oder passendes Werkzeug |
| Umlaute/Klassen unerwartet | Locale | Locale prüfen, POSIX-Klassen nutzen |
| falsche Treffer in JSON/XML | Textsuche statt Parser | `jq`, `xmllint`, `yq` verwenden |
| Rekursion extrem langsam | riesige Vendor-/Mount-Verzeichnisse | ausschließen oder `rg` |

## Schnellrezepte

```bash
# Fehler mit Kontext
grep -nEi -C 2 'error|fail|panic' app.log

# Exakter Schlüssel in Konfiguration
grep -nE '^[[:space:]]*PermitRootLogin[[:space:]]+' /etc/ssh/sshd_config

# Dateien mit Geheimnisverdacht, ohne VCS/Dependencies
grep -RIlE --exclude-dir={.git,node_modules,.venv} \
  'api[_-]?key|secret|password' .

# IPs extrahieren – nur syntaktisch, keine 0–255-Prüfung
grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' access.log | sort -u

# Letzte Kernelwarnungen
journalctl -k -b --priority=warning --no-pager | grep -Ei 'error|fail|timeout|reset'
```

## Quellen
- [GNU grep Manual](https://www.gnu.org/software/grep/manual/grep.html)
- [grep man page](https://man7.org/linux/man-pages/man1/grep.1.html)

## Verwandte Notizen
- [[dmesg – Premium-Spickzettel]]
- [[Manpages – Premium-Spickzettel]]
- [[Neovim – Premium-Spickzettel]]
