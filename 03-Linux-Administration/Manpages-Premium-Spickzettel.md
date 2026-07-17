---
title: "Manpages – Premium-Spickzettel"
aliases: ["man Cheatsheet", "Linux Handbuchseiten", "Manual Pages"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, man, documentation, shell, reference]
source: "https://www.kernel.org/doc/man-pages/"
---

# Manpages – Premium-Spickzettel

> [!abstract] Zweck
> Referenz zum Finden, Lesen und Verknüpfen von Manual Pages: Sektionen, Suche, Pager-Shortcuts, apropos/whatis, Querverweise, Formate, Übersetzungen und Dokumentationsstrategie.

## Inhalt

- [[#Grundaufrufe]]
- [[#Sektionen]]
- [[#Suchen und Finden]]
- [[#Navigation im Pager]]
- [[#Syntax lesen]]
- [[#Querverweise und verwandte Dokumentation]]
- [[#Ausgabe und Export]]
- [[#Konfiguration]]
- [[#Fehlerdiagnose]]
- [[#Lernroutine]]

## Grundaufrufe

```bash
man ls
man grep
man ssh_config
man 5 fstab
man 8 mount
```

Kurzbeschreibung:

```bash
whatis rsync
man -f rsync
```

Themensuche:

```bash
apropos 'copy files'
man -k 'regular expression'
```

Alle gleichnamigen Seiten nacheinander:

```bash
man -a passwd
```

Pfad zur Quelldatei:

```bash
man -w ssh
man -wa passwd
```

## Sektionen

| Sektion | Inhalt | Beispiel |
|---:|---|---|
| 1 | Benutzerbefehle | `man 1 grep` |
| 2 | Systemaufrufe | `man 2 open` |
| 3 | Bibliotheksfunktionen | `man 3 printf` |
| 4 | Geräte/Spezialdateien | `man 4 null` |
| 5 | Dateiformate/Konfiguration | `man 5 fstab` |
| 6 | Spiele | `man 6` |
| 7 | Übersichten, Standards, Konventionen | `man 7 regex` |
| 8 | Administration | `man 8 ip` |
| 9 | Kernelroutinen, systemabhängig | Kernelentwicklung |

Gleichnamige Einträge explizit wählen:

```bash
man 1 printf
man 3 printf
man 5 passwd
man 1 passwd
```

> [!tip]
> Schreibweise `name(section)` in Dokumentation bedeutet beispielsweise `open(2)` → `man 2 open`.

## Suchen und Finden

Datenbank aktualisieren:

```bash
sudo mandb
```

Beschreibung und Namen durchsuchen:

```bash
apropos network
apropos -a 'network' 'interface'
apropos -s 5 'configuration'
```

Volltextähnliche Suche im bereits geöffneten Manual erfolgt im Pager mit `/muster`.

Nach Option suchen:

```text
/--delete
```

Bei führendem Bindestrich gegebenenfalls Regex beachten:

```text
/\-\-delete
```

Online-/Projekt-Dokumentation zusätzlich prüfen, wenn:

- Version des Systems neuer/älter als lokale Seite ist
- das Programm eigene `--help`-Ausgabe oder Subcommands hat
- Distribution Patches einsetzt
- Beispiele oder Architekturübersichten fehlen

## Navigation im Pager

Meist wird `less` verwendet.

| Taste | Aktion |
|---|---|
| `Space`, `PgDn` | Seite vor |
| `b`, `PgUp` | Seite zurück |
| `j`/`k`, Pfeile | Zeile runter/hoch |
| `g` | Anfang |
| `G` | Ende |
| `/text` | vorwärts suchen |
| `?text` | rückwärts suchen |
| `n` / `N` | nächster/vorheriger Treffer |
| `h` | Hilfe |
| `q` | beenden |

Zeilennummern in `less`:

```bash
MANPAGER='less -R -N' man rsync
```

## Syntax lesen

Typische Notation:

```text
Befehl [OPTION]... DATEI...
```

| Notation | Bedeutung |
|---|---|
| `[x]` | optional |
| `x...` | wiederholbar |
| `a|b` | Alternative |
| fett | literal einzugeben |
| kursiv/unterstrichen | Platzhalter |

> [!warning]
> Eckige Klammern aus der SYNOPSIS werden normalerweise **nicht** mitgetippt. Sie markieren optionale Bestandteile.

Manuals systematisch lesen:

1. `NAME` – Einzeiler.
2. `SYNOPSIS` – Form und Argumente.
3. `DESCRIPTION` – Grundsemantik.
4. `OPTIONS` – Detailoptionen.
5. `EXAMPLES` – falls vorhanden.
6. `FILES`, `ENVIRONMENT`, `EXIT STATUS` – für Betrieb/Skripte.
7. `SECURITY`, `BUGS`, `SEE ALSO` – Fallstricke und Vertiefung.

## Querverweise und verwandte Dokumentation

```bash
info coreutils 'ls invocation'
command --help
help cd                 # Shell-Builtin
help source
```

Shell-Builtin oder extern?

```bash
type -a printf
type -a time
command -V source
```

Paketdokumentation:

```bash
rpm -qd paketname
dpkg -L paketname | grep -E '/(doc|man)/'
```

Systemd besitzt viele thematische Seiten:

```bash
man systemd.unit
man systemd.service
man systemd.exec
man systemd.time
```

OpenSSH:

```bash
man ssh
man ssh_config
man sshd
man sshd_config
man authorized_keys
```

## Ausgabe und Export

Plaintext:

```bash
MANPAGER=cat man rsync > rsync-man.txt
man rsync | col -b > rsync-man.txt
```

PostScript/PDF, abhängig von Installation:

```bash
man -Tps rsync > rsync.ps
man -Tpdf rsync > rsync.pdf
```

HTML über passende Implementierung:

```bash
man --html=firefox rsync
```

Nicht jede `man`-Version unterstützt jedes Ausgabeformat.

## Konfiguration

Wichtige Variablen:

```bash
export MANPAGER='less -R'
export PAGER='less -R'
export MANWIDTH=100
```

Suchpfad:

```bash
manpath
man --path
```

Sprache:

```bash
LANG=de_DE.UTF-8 man man
LANG=C man man
```

> [!tip]
> Bei unklarer Übersetzung die englische Originalseite mit `LANG=C` lesen. Technische Begriffe und Aktualität sind dort häufig eindeutiger.

## Fehlerdiagnose

| Problem | Prüfen |
|---|---|
| `No manual entry` | Paket installiert? Sektion? `mandb`? `manpath`? |
| falsche Seite | Sektion explizit angeben |
| Seite veraltet | `command --version`, Upstream-Doku |
| Sonderzeichen kaputt | Locale und Pageroptionen |
| Suche findet nichts | `apropos`, englische Begriffe, Datenbank aktualisieren |
| Befehl ist Shell-Builtin | `help befehl` statt nur `man` |

```bash
command -v rsync
rsync --version
man -w rsync
man --debug rsync 2>&1 | less
```

## Lernroutine

Für einen neuen Befehl:

```bash
befehl --help
man befehl
apropos begriff
```

Dann eine sichere Probe:

- Testverzeichnis verwenden.
- Dry-Run suchen.
- Exitcodes prüfen.
- Änderungen mit `diff`, `stat`, Logs oder Statusbefehl validieren.
- Nützliche Beispiele in den eigenen Spickzettel übernehmen, aber Version und Kontext notieren.

## Quellen
- [man-pages project](https://www.kernel.org/doc/man-pages/)
- [man-db](https://man-db.gitlab.io/man-db/)

## Verwandte Notizen
- [[grep – Premium-Spickzettel]]
- [[Fedora-RHEL – Premium-Spickzettel]]
- [[Make und Source-Builds – Premium-Spickzettel]]
