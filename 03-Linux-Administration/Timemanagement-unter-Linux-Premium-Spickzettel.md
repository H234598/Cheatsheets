---
title: "Zeitmanagement unter Linux – timedatectl, NTP und RTC"
aliases: ["timedatectl Cheatsheet", "Linux Uhrzeit", "chrony NTP"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [time, timedatectl, ntp, chrony, linux, timezone]
source: "https://www.freedesktop.org/software/systemd/man/latest/timedatectl.html"
---

# Zeitmanagement unter Linux – timedatectl, NTP und RTC

> [!abstract] Zweck
> Praxisreferenz für Systemzeit unter Linux: UTC, Zeitzonen, timedatectl, chrony, systemd-timesyncd, hwclock/RTC, Zeitsprünge, NTP-Diagnose und Virtualisierung.

> [!important]
> Authentisierung, TLS, Kerberos, Logs, Datenbanken und Cluster hängen von korrekter Zeit ab. Große manuelle Zeitsprünge auf produktiven Systemen können Jobs, Leases und Konsistenz stören. NTP-Quelle und Betriebsverfahren definieren.

## Inhalt

- [[#Zeitbegriffe]]
- [[#Status mit timedatectl]]
- [[#Zeitzone]]
- [[#NTP mit chrony]]
- [[#systemd-timesyncd]]
- [[#Hardwareuhr RTC]]
- [[#Manuell setzen]]
- [[#Anwendungen, Container und VMs]]
- [[#Diagnose]]

## Zeitbegriffe

| Begriff | Bedeutung |
|---|---|
| UTC | globale Zeitbasis ohne Sommerzeit |
| Local Time | UTC plus Zeitzonenregeln |
| Zeitzone | IANA-Zone wie `Europe/Berlin`, nicht nur `CET` |
| RTC | Hardware-/Firmware-Uhr |
| System Clock | Kernel-Uhr während Betrieb |
| NTP | Protokoll zur Zeitsynchronisation |
| Step | abrupter Zeitsprung |
| Slew | graduelle Korrektur der Frequenz/Zeit |
| Drift | Abweichung der Uhr über Zeit |

Linux-Systemuhr sollte intern UTC führen. Zeitzone beeinflusst Darstellung.

## Status mit timedatectl

```bash
timedatectl
```

Gezielt:

```bash
timedatectl show
```

Wichtige Felder:

```text
Local time
Universal time
RTC time
Time zone
System clock synchronized
NTP service
RTC in local TZ
```

NTP aktivieren:

```bash
sudo timedatectl set-ntp true
```

Das aktiviert den auf der Distribution vorgesehenen NTP-Dienst, sofern verfügbar. Welcher Dienst tatsächlich läuft:

```bash
systemctl status chronyd systemd-timesyncd 2>/dev/null
```

> [!warning]
> Nicht mehrere Zeitdaemonen gleichzeitig konkurrieren lassen. Chrony, timesyncd, ntpd oder Virtualisierungsagenten koordiniert konfigurieren.

## Zeitzone

Liste:

```bash
timedatectl list-timezones | less
timedatectl list-timezones | grep -i berlin
```

Setzen:

```bash
sudo timedatectl set-timezone Europe/Berlin
```

Prüfen:

```bash
date
date -u
readlink -f /etc/localtime
```

Formatieren:

```bash
date --iso-8601=seconds
date -u +'%Y-%m-%dT%H:%M:%SZ'
date +'%s'
```

> [!tip]
> Für Logs/APIs RFC-3339/ISO-8601 mit Offset oder UTC `Z` verwenden. Abkürzungen wie `CST` sind mehrdeutig.

## NTP mit chrony

Auf Fedora/RHEL ist chrony häufig Standard.

Status:

```bash
systemctl status chronyd
chronyc tracking
chronyc sources -v
chronyc sourcestats -v
chronyc activity
```

### `tracking` lesen

Wichtige Werte:

- Reference ID/Name
- Stratum
- System time offset
- Last offset/RMS offset
- Frequency/Skew
- Leap status

Quellenmarker:

```text
^* ausgewählte Quelle
^+ kombinierbare Quelle
^- verworfene Quelle
^? nicht erreichbar/ungenügende Messungen
^x falseticker
```

Konfiguration häufig:

```text
/etc/chrony.conf
```

Beispiel:

```conf
pool pool.ntp.org iburst
makestep 1.0 3
rtcsync
```

Unternehmen:

```conf
server ntp1.example.org iburst
server ntp2.example.org iburst
```

Nach Änderung:

```bash
sudo chronyc reload sources
# oder falls nötig
sudo systemctl restart chronyd
```

Große Korrektur bewusst:

```bash
sudo chronyc makestep
```

> [!danger]
> `makestep` kann Zeit abrupt springen lassen. Auf Datenbanken/Clustern/Jobservern nur nach Betriebsbewertung.

NTP-Port: UDP 123 ausgehend/je Serverrolle eingehend. DNS und Routing prüfen.

## systemd-timesyncd

Status:

```bash
timedatectl timesync-status
systemctl status systemd-timesyncd
journalctl -u systemd-timesyncd -b
```

Konfiguration:

```text
/etc/systemd/timesyncd.conf
/etc/systemd/timesyncd.conf.d/*.conf
```

Beispiel:

```ini
[Time]
NTP=ntp1.example.org ntp2.example.org
FallbackNTP=
```

```bash
sudo systemctl restart systemd-timesyncd
```

timesyncd ist ein einfacher SNTP/NTP-Client; für komplexere Server-, Hardwaretimestamp- oder anspruchsvolle Driftfälle ist chrony häufig geeigneter.

## Hardwareuhr RTC

Status:

```bash
sudo hwclock --show
sudo hwclock --verbose
```

System → RTC:

```bash
sudo hwclock --systohc --utc
```

RTC → System:

```bash
sudo hwclock --hctosys
```

> [!warning]
> Moderne systemd-Systeme synchronisieren RTC teils automatisch. Nicht ohne Grund manuell in gegensätzliche Richtungen schreiben.

RTC in lokaler Zeit:

```bash
sudo timedatectl set-local-rtc 1
```

Nicht empfohlen auf reinen Linux-Systemen; Sommerzeit und Dual-Boot-Sonderfälle. Besser Betriebssysteme auf UTC-RTC konfigurieren, sofern möglich.

## Manuell setzen

NTP zunächst deaktivieren oder geplanten Ablauf verwenden:

```bash
sudo timedatectl set-ntp false
sudo timedatectl set-time '2026-07-17 10:30:00'
```

Dann NTP wieder aktivieren:

```bash
sudo timedatectl set-ntp true
```

Alternative:

```bash
sudo date --set='2026-07-17 10:30:00'
```

> [!danger]
> Auf Domain-/Kerberos-, Cluster-, Datenbank- und Zertifikatssystemen keine großen Sprünge ohne Plan. Ursache des Synchronisationsfehlers beheben.

## Anwendungen, Container und VMs

### Container

Container teilen normalerweise Kernel-Systemzeit des Hosts; sie können nicht unabhängig eine andere echte Systemuhr führen. Zeitzone kann über `/etc/localtime`, `TZ` oder Imagekonfiguration dargestellt werden.

Nicht untrusted Containern Capability zum Setzen der Systemzeit geben.

### Virtuelle Maschinen

Mögliche Zeitquellen:

- NTP im Gast
- Hypervisor-Timekeeping
- Guest Tools
- TSC/KVM Clock/Hyper-V Clock

Doppelte aggressive Synchronisation kann Sprünge verursachen. Herstellerempfehlung für Hypervisor und Gast-OS befolgen.

### Anwendungen

- Dauer mit monotonic clock messen, nicht Wall Clock.
- Datenbankzeit und Appzeit auf UTC.
- Zeitstempel mit Zeitzone/Offset.
- Cron/systemd Timer bei DST testen.
- Zertifikatsfehler können reine Uhrzeitfehler sein.

Python:

```python
import time
start = time.monotonic()
```

Shell Laufzeit:

```bash
time befehl
```

Das ist Prozesslaufzeit, nicht Systemzeitverwaltung.

## Diagnose

### Uhr nicht synchronisiert

```bash
timedatectl
systemctl status chronyd systemd-timesyncd 2>/dev/null
chronyc tracking 2>/dev/null
chronyc sources -v 2>/dev/null
journalctl -u chronyd -b -n 200 2>/dev/null
journalctl -u systemd-timesyncd -b -n 200 2>/dev/null
```

Dann:

1. genau ein Zeitdaemon aktiv?
2. Quellenname auflösbar?
3. UDP 123 erreichbar?
4. Quellserver antwortet und ist selbst synchron?
5. Offset zu groß/Policy verhindert Step?
6. VM/Hypervisor greift ein?
7. Uhr/RTC nach Boot falsch?

### NTP-Pakete

```bash
sudo tcpdump -ni any udp port 123
```

Nur Metadaten und Datenschutz beachten.

### Kerberos/TLS-Fehler

```bash
date -Is
date -u
chronyc tracking
openssl s_client -connect host:443 -servername host </dev/null 2>/dev/null | openssl x509 -noout -dates
```

Zeit zuerst korrigieren, nicht Zertifikatsprüfung abschalten.

### Zeitzone falsch, UTC korrekt

```bash
timedatectl
readlink -f /etc/localtime
sudo timedatectl set-timezone Europe/Berlin
```

### Zeit springt

```bash
journalctl -b | grep -Ei 'time.*jump|clock.*change|chrony|timesync|rtc'
chronyc tracking
systemd-detect-virt
```

Hypervisor, NTP, manuelle Befehle, Resume aus Suspend und RTC prüfen.

### Universelle Prüfreihenfolge

```bash
date --iso-8601=seconds
date -u --iso-8601=seconds
timedatectl
systemctl --type=service --state=running | grep -E 'chrony|timesync|ntp'
```

## Quellen
- [timedatectl Manual](https://www.freedesktop.org/software/systemd/man/latest/timedatectl.html)
- [chrony Documentation](https://chrony-project.org/documentation.html)
- [hwclock Manual](https://man7.org/linux/man-pages/man8/hwclock.8.html)
- [systemd-timesyncd](https://www.freedesktop.org/software/systemd/man/latest/systemd-timesyncd.service.html)

## Verwandte Notizen
- [[Systemd-Premium-Spickzettel]]
- [[SSH-Premium-Spickzettel]]
- [[MS-RPC-Verbindungen-Premium-Spickzettel]]
