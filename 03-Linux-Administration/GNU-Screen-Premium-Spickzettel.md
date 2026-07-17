---
title: "GNU Screen – Premium-Spickzettel"
aliases: ["GNU Screen Cheatsheet", "Screen Terminal Multiplexer", "screen Spickzettel"]
created: 2026-07-16
modified: 2026-07-17
type: reference
status: fertig
origin: "Premium Spickzettel I – vollständig überarbeitet"
reviewed: 2026-07-17
tags: [gnu, screen, terminal, multiplexer, ssh, linux, shell, administration]
source: "https://www.gnu.org/software/screen/manual/screen.html"
---

# GNU Screen – Premium-Spickzettel

> [!abstract] Zweck
> Praxisreferenz für persistente Terminalsitzungen: Start, Attach/Detach, Fenster, Splits, Copy-Mode, Scrollback, Logging, Hardcopy, Befehlssteuerung, Multiuser, `.screenrc`, Automatisierung, Sicherheit und Diagnose.

## Grundprinzip

Screen läuft zwischen Terminal und Shell. Bricht eine SSH-Verbindung ab, bleiben Prozesse in der Screen-Sitzung aktiv. Später lässt sich die Sitzung erneut verbinden.

Standardpräfix:

```text
Ctrl+a
```

Notation:

```text
C-a c = Ctrl+a drücken, loslassen, danach c
```

> [!warning]
> Screen schützt gegen Terminal- oder SSH-Abbruch, **nicht** gegen Reboot, OOM-Killer, Prozessabsturz oder einen ausgeschalteten Host. Für echte Dienste `systemd`, Supervisor, Container oder einen Scheduler verwenden.

## Inhalt

- [[#Installation und Version]]
- [[#Sitzungen starten und verbinden]]
- [[#Fenster verwalten]]
- [[#Detach und Beenden]]
- [[#Scrollback und Copy-Mode]]
- [[#Splits und Regionen]]
- [[#Logging und Hardcopy]]
- [[#Befehle an Sitzungen senden]]
- [[#Multiuser]]
- [[#screenrc konfigurieren]]
- [[#Automationsmuster]]
- [[#Sicherheit]]
- [[#Fehlerdiagnose]]
- [[#Schnellreferenz]]

## Installation und Version

Fedora/RHEL:

```bash
sudo dnf install screen
```

Debian/Ubuntu:

```bash
sudo apt install screen
```

FreeBSD:

```sh
pkg install screen
```

Version und Hilfe:

```bash
screen --version
screen --help
man screen
info screen
```

Installationsmodus prüfen:

```bash
command -v screen
ls -l "$(command -v screen)"
```

Multiuser-Funktionen können je Distribution, Build und setuid-Konfiguration eingeschränkt sein.

## Sitzungen starten und verbinden

Neue Sitzung:

```bash
screen
```

Benannt:

```bash
screen -S wartung
```

Mit Startfenstername:

```bash
screen -S wartung -t shell
```

Befehl direkt starten:

```bash
screen -S backup rsync -a /quelle/ /ziel/
```

Detached starten:

```bash
screen -DmS monitoring watch -n 5 'systemctl --failed'
```

Sitzungen anzeigen:

```bash
screen -ls
```

Wieder verbinden:

```bash
screen -r wartung
screen -r              # wenn eindeutig
```

Anderes Attach trennen und hier übernehmen:

```bash
screen -d -r wartung
```

Unabhängig vom Status übernehmen:

```bash
screen -D -r wartung
```

Parallel verbinden:

```bash
screen -x wartung
```

> [!warning]
> `screen -x` ermöglicht parallele Anzeige und Eingaben. Mehrere Schreibende können Befehle vermischen oder unbeabsichtigt Aktionen auslösen.

Sitzung anhand PID/Name auswählen:

```bash
screen -r 12345.wartung
```

## Fenster verwalten

| Tastenkürzel | Funktion |
|---|---|
| `C-a c` | neues Fenster |
| `C-a n` | nächstes Fenster |
| `C-a p` | vorheriges Fenster |
| `C-a Space` | nächstes Fenster |
| `C-a Backspace` | vorheriges Fenster |
| `C-a 0` … `C-a 9` | Fenster 0–9 |
| `C-a '` | Auswahl per Nummer/Name |
| `C-a "` | interaktive Fensterliste |
| `C-a A` | Fenster umbenennen |
| `C-a k` | aktuelles Fenster beenden |
| `C-a w` | Fensterliste anzeigen |
| `C-a C-a` | zum vorherigen Fenster wechseln |

Screen-Kommandozeile:

```text
C-a :
```

Beispiele:

```text
title logs
screen -t monitoring
select 2
number 5
```

Direkt benannte Fenster beim Start:

```bash
screen -S arbeit -t logs
```

Fenster von außen anlegen:

```bash
screen -S wartung -X screen -t logs tail -F /var/log/messages
```

> [!tip]
> Aussagekräftige Sitzungs- und Fensternamen sparen Fehlbedienungen. Namen wie `prod-db-migration`, `logs-api` oder `backup-nas` sind besser als `screen1`.

## Detach und Beenden

Sicher trennen:

```text
C-a d
```

Von außen trennen:

```bash
screen -S wartung -X detach
```

Nur aktuelle Shell beenden:

```bash
exit
```

Aktuelles Fenster beenden:

```text
C-a k
```

Gesamte Sitzung beenden:

```bash
screen -S wartung -X quit
```

Innerhalb Screen:

```text
C-a :quit
```

> [!danger]
> `-X quit` beziehungsweise `:quit` beendet die komplette Sitzung und die darin laufenden Prozesse. Nicht mit Detach verwechseln.

## Scrollback und Copy-Mode

Copy-/Scrollback-Modus:

```text
C-a [
```

Alternativ:

```text
C-a Esc
```

Typische Navigation:

| Taste | Funktion |
|---|---|
| Pfeile oder `h j k l` | bewegen |
| `PageUp`, `PageDown` | seitenweise |
| `g` | Anfang |
| `G` | Ende |
| `/text` | vorwärts suchen |
| `?text` | rückwärts suchen |
| `n`, `N` | nächster/vorheriger Treffer |
| `Space` | Kopierbereich starten/beenden |
| `Enter` | Auswahl abschließen |
| `Esc` | Modus verlassen |

Screen-Puffer einfügen:

```text
C-a ]
```

Scrollback für aktuelles Fenster erhöhen:

```text
C-a :scrollback 100000
```

In `.screenrc` global:

```screen
defscrollback 100000
```

> [!warning]
> Screen-Puffer und Zwischenablage können Passwörter, Tokens oder personenbezogene Daten enthalten. Bei gemeinsam genutzten Sitzungen besonders vorsichtig sein.

## Splits und Regionen

Horizontal teilen:

```text
C-a S
```

Vertikal, falls Build unterstützt:

```text
C-a |
```

Region wechseln:

```text
C-a Tab
```

Fenster in aktiver Region auswählen oder neu anlegen:

```text
C-a n
C-a c
```

Aktuelle Region schließen:

```text
C-a X
```

Alle anderen Regionen schließen:

```text
C-a Q
```

Layout speichern/wiederherstellen, je Version/Build:

```text
C-a :layout save arbeit
C-a :layout select arbeit
```

> [!note]
> Ein Split erzeugt zunächst nur eine Region. Eine neue Shell entsteht erst mit `C-a c` oder durch Auswahl eines vorhandenen Fensters.

## Logging und Hardcopy

Logging ein-/ausschalten:

```text
C-a H
```

Standarddatei ist häufig `screenlog.0` im aktuellen Verzeichnis.

Von außen:

```bash
screen -S wartung -p 0 -X logfile /var/log/wartung-screen.log
screen -S wartung -p 0 -X log on
screen -S wartung -p 0 -X log off
```

Hardcopy des sichtbaren Fensters:

```text
C-a h
```

Gesamten Scrollback schreiben:

```text
C-a :hardcopy -h ausgabe.txt
```

Von außen:

```bash
screen -S wartung -p 0 -X hardcopy -h /tmp/wartung.txt
```

Zeitstempel in Logausgaben lassen sich je Konfiguration ergänzen; für belastbare Audit-Logs ist Screen aber kein Ersatz für zentrale Prozess- und Anwendungstelemetrie.

> [!danger]
> Logs können Geheimnisse enthalten. Zielpfad, Rechte, Rotation, Aufbewahrung und Löschung vorher festlegen.

## Befehle an Sitzungen senden

Screen-Kommando:

```bash
screen -S wartung -X windows
screen -S wartung -X info
screen -S wartung -X screen -t uptime watch -n 10 uptime
```

Tastenfolge an Fenster senden:

```bash
screen -S wartung -p 0 -X stuff $'uptime\n'
```

Literal `Ctrl+c` senden:

```bash
screen -S wartung -p 0 -X stuff $'\003'
```

> [!danger]
> `stuff` simuliert Tastatureingaben. Ziel-Sitzung, Fenster und aktueller Prompt müssen exakt bekannt sein. Ein falscher Shell-Kontext kann gefährliche Befehle auslösen. Für Automatisierung lieber APIs, Signale, systemd oder ein explizites Steuerprotokoll nutzen.

## Multiuser

Innerhalb einer Sitzung:

```text
C-a :multiuser on
C-a :acladd benutzername
```

Rechte ändern:

```text
C-a :aclchg benutzername -rwx "#?"
```

Verbindung:

```bash
screen -x eigentuemer/sitzung
```

Multiuser hängt von Systemrechten und Build ab. Häufig sind besondere Installationsrechte erforderlich.

> [!warning]
> Multiuser-Screen erweitert den Angriffsraum und erlaubt je nach ACL Einsicht oder Eingaben in Shells. Für Zusammenarbeit besser getrennte Konten, `sudo`, Auditierung und explizite Pairing-Werkzeuge erwägen.

## `.screenrc` konfigurieren

Benutzerdatei:

```text
~/.screenrc
```

Beispiel:

```screen
startup_message off
defscrollback 100000
defutf8 on
utf8 on
vbell on
shelltitle "$ |bash"

# Statuszeile
hardstatus alwayslastline
hardstatus string '%{= kG}[%H] %{= kw}%?%-Lw%?%{r}(%n*%f %t)%?%+Lw%? %= %Y-%m-%d %c'

# Logdatei
logfile "$HOME/.local/state/screen/screenlog.%S.%n.%Y%m%d-%0c:%s"

# Keine automatische Logaktivierung; bewusst pro Sitzung einschalten
```

Alternative Escape-Taste, etwa `Ctrl+b`:

```screen
escape ^Bb
```

Neu einlesen:

```text
C-a :source ~/.screenrc
```

Systemweite Konfiguration liegt je Distribution häufig unter `/etc/screenrc`.

> [!tip]
> Änderungen zuerst in einer Test-Sitzung prüfen. Eine fehlerhafte Escape-Konfiguration kann die Bedienung scheinbar „blockieren“.

## Automationsmuster

### Langläufer mit Statusdatei

```bash
mkdir -p "$HOME/.local/state/jobs"
screen -DmS backup bash -lc '
  set -Eeuo pipefail
  trap "printf \"%s failed\\n\" \"$(date -Is)\" >> "$HOME/.local/state/jobs/backup.status"" ERR
  printf "%s start\n" "$(date -Is)" >> "$HOME/.local/state/jobs/backup.status"
  rsync -a --delete /quelle/ /ziel/
  printf "%s done\n" "$(date -Is)" >> "$HOME/.local/state/jobs/backup.status"
'
```

### Healthcheck

```bash
screen -ls | grep -q '[.]backup' && echo läuft || echo fehlt
```

> [!note]
> Für geplante oder kritische Jobs sind systemd-Timer, Cron/Scheduler und Monitoring robuster. Screen eignet sich vor allem für interaktive Wartung und bewusst beobachtete Langläufer.

## Sicherheit

- Sitzungen nur unter dem vorgesehenen Unix-Konto betreiben;
- keine Secrets per `stuff`, Kommandozeile oder ungeschütztem Log;
- Multiuser nur mit dokumentierter ACL;
- Socket-Verzeichnisse und `/run/screen`-Rechte prüfen;
- Sessions vor Wartungsende inventarisieren;
- nicht als versteckten Dienstmanager missbrauchen;
- Terminalausgabe vor Supportweitergabe redigieren;
- bei Root-Sitzungen besonders klare Namen und minimale Dauer.

Sitzungen anderer Nutzer nicht mit pauschalem Rootzugriff „übernehmen“, wenn ein sauberer Betriebsweg möglich ist.

## Fehlerdiagnose

### Keine Sitzung gefunden

```bash
screen -ls
ps -ef | grep '[s]creen'
```

Prüfen: Benutzer, Sitzungsname, Host, Container/Namespace und Socketpfad.

### Sitzung ist `Attached`

```bash
screen -d -r sitzungsname
```

### Tote Einträge

```bash
screen -wipe
```

Vorher sicherstellen, dass es wirklich verwaiste Sockets und keine noch relevante Sitzung sind.

### Terminaldarstellung kaputt

```bash
reset
stty sane
printf '\033c'
```

Terminaltyp:

```bash
printf '%s\n' "$TERM"
infocmp "$TERM" | head
```

### Nach SSH-Abbruch

```bash
screen -ls
screen -d -r wartung
```

### Präfix funktioniert nicht

- alternative `escape`-Direktive in `.screenrc`?
- Terminal fängt Tastenkombination ab?
- verschachteltes Screen/Terminalmultiplexer?
- `C-a a` sendet ein literales `Ctrl+a` an die Anwendung.

### Anwendung reagiert nach Detach anders

Prüfen:

```bash
tty
stty -a
printf 'TERM=%s\n' "$TERM"
```

Manche Programme benötigen passende Terminalgröße oder reagieren auf SIGHUP/TTY-Verlust. Screen hält die PTY normalerweise, aber Wrapper oder Shellskripte können anders arbeiten.

## Schnellreferenz

| Aktion | Kommando |
|---|---|
| benannte Sitzung | `screen -S name` |
| detached starten | `screen -DmS name befehl` |
| Sitzungen | `screen -ls` |
| verbinden | `screen -r name` |
| Attach übernehmen | `screen -d -r name` |
| Detach | `C-a d` |
| neues Fenster | `C-a c` |
| nächstes/vorheriges | `C-a n` / `C-a p` |
| Fensterliste | `C-a "` |
| Copy-Mode | `C-a [` |
| Einfügen | `C-a ]` |
| horizontaler Split | `C-a S` |
| Region wechseln | `C-a Tab` |
| Logging | `C-a H` |
| Sitzung beenden | `screen -S name -X quit` |

Goldene Regeln:

```text
Detach statt Quit.
Benannte Sitzungen und Fenster verwenden.
Screen ist kein Dienstmanager.
Logs und Copy-Puffer als sensibel behandeln.
stuff nur in vollständig kontrolliertem Kontext.
```

## Quellen

- [GNU Screen Manual](https://www.gnu.org/software/screen/manual/screen.html)
- [GNU Screen project](https://www.gnu.org/software/screen/)

## Verwandte Notizen

- [[SSH-Premium-Spickzettel]]
- [[Termux-Premium-Spickzettel]]
- [[Systemd-Premium-Spickzettel]]
- [[Windows-Terminal-Premium-Spickzettel]]
