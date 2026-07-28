---
title: "systemd – Cheatsheet"
aliases: ["systemctl Cheatsheet", "journalctl Cheatsheet", "systemd Units"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [systemd, systemctl, journalctl, linux, services, timers]
source: "https://www.freedesktop.org/software/systemd/man/latest/"
---

# systemd – Cheatsheet

> [!abstract] Zweck
> Ausführliche Referenz für systemd: Units, Abhängigkeiten, Overrides, Dienste, Targets, Timer, Journal, Bootanalyse, Ressourcen, Credentials, coredump und Diagnose.

## Inhalt

- [[#Unittypen und Pfade]]
- [[#Status und Lifecycle]]
- [[#Enable versus Start]]
- [[#Unitdateien und Overrides]]
- [[#Abhängigkeiten und Reihenfolge]]
- [[#Service-Typen und Neustarts]]
- [[#Umgebung, Benutzer und Sicherheit]]
- [[#Timer]]
- [[#Targets und Boot]]
- [[#Journal]]
- [[#Ressourcen und Cgroups]]
- [[#User-Units]]
- [[#Diagnose]]

## Unittypen und Pfade

| Suffix | Zweck |
|---|---|
| `.service` | Dienst/Prozess |
| `.socket` | Socketaktivierung |
| `.timer` | Zeitsteuerung |
| `.path` | Dateisystemereignisse |
| `.mount` / `.automount` | Mounts |
| `.target` | Gruppierungs-/Synchronisationspunkt |
| `.device` | Gerät |
| `.scope` | extern gestartete Prozessgruppe |
| `.slice` | Cgroup-Hierarchie |

Suchpfade/Prio typischerweise:

```text
/etc/systemd/system            lokale Adminunits/Overrides
/run/systemd/system            flüchtige Runtimeunits
/usr/lib/systemd/system        Vendorunits auf Fedora/RHEL
/lib/systemd/system            Vendorpfad auf manchen Distributionen
```

Anzeigen:

```bash
systemctl cat name.service
systemctl show name.service -p FragmentPath,DropInPaths
systemd-delta
```

## Status und Lifecycle

```bash
systemctl status name.service --no-pager -l
systemctl is-active name.service
systemctl is-enabled name.service
systemctl is-failed name.service
systemctl list-units --type=service --state=running
systemctl --failed
```

Steuern:

```bash
sudo systemctl start name
sudo systemctl stop name
sudo systemctl restart name
sudo systemctl reload name
sudo systemctl reload-or-restart name
sudo systemctl try-restart name
sudo systemctl reset-failed name
```

> [!note]
> `reload` funktioniert nur, wenn die Unit `ExecReload` definiert beziehungsweise der Dienst Reload unterstützt. `daemon-reload` lädt systemd-Unitdefinitionen neu, nicht die Anwendungskonfiguration.

## Enable versus Start

```text
start     jetzt starten
enable    Startverknüpfung für künftigen Boot/Trigger anlegen
disable   Verknüpfung entfernen, laufenden Dienst nicht stoppen
mask      jeden Start über Symlink auf /dev/null verhindern
```

```bash
sudo systemctl enable --now name
sudo systemctl disable --now name
sudo systemctl mask name
sudo systemctl unmask name
```

Presets:

```bash
systemctl preset-status name
sudo systemctl preset name
```

## Unitdateien und Overrides

Eigene Unit:

```ini
[Unit]
Description=Beispieldienst
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=app
Group=app
WorkingDirectory=/srv/app
ExecStart=/srv/app/bin/server --config /etc/app/config.toml
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Installieren:

```bash
sudo install -m 0644 app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now app.service
```

### Override

```bash
sudo systemctl edit app.service
```

```ini
[Service]
Environment=LOG_LEVEL=debug
RestartSec=10s
```

Eine Liste wie `ExecStart=` zurücksetzen:

```ini
[Service]
ExecStart=
ExecStart=/srv/app/bin/server --new-option
```

> [!danger]
> Vendor-Unit in `/usr/lib/systemd/system` nicht direkt bearbeiten. Update würde Änderung überschreiben. `systemctl edit` beziehungsweise vollständige lokale Unit unter `/etc` verwenden.

Prüfen:

```bash
systemd-analyze verify /etc/systemd/system/app.service
```

## Abhängigkeiten und Reihenfolge

| Direktive | Bedeutung |
|---|---|
| `Requires=` | harte Aktivierungsabhängigkeit; Stop/Fehlerbeziehung begrenzt kontextabhängig |
| `Wants=` | schwächere Aktivierungsabhängigkeit |
| `After=` | nur Startreihenfolge, zieht Unit nicht automatisch ein |
| `Before=` | umgekehrte Reihenfolge |
| `BindsTo=` | starke Lebenszyklusbindung |
| `PartOf=` | Stop/Restart kann mit übergeordneter Unit gekoppelt werden |
| `Conflicts=` | Units sollen nicht gleichzeitig aktiv sein |

> [!important]
> `After=network.target` bedeutet nicht, dass Internet/DNS verfügbar ist. Netzwerkbereitschaft ist dienst- und NetworkManager-Konfiguration abhängig. Anwendungen sollten Retries und Timeouts besitzen.

Abhängigkeiten:

```bash
systemctl list-dependencies app.service
systemctl list-dependencies --reverse app.service
systemctl show app.service -p Wants,Requires,After,Before
```

## Service-Typen und Neustarts

| Type | Verwendung |
|---|---|
| `simple` | Prozess aus `ExecStart` gilt direkt als Hauptprozess |
| `exec` | Start gilt nach erfolgreichem `execve` |
| `notify` | Dienst signalisiert Bereitschaft via sd_notify |
| `forking` | klassischer daemonisiert/forkt; PIDFile häufig nötig |
| `oneshot` | einmalige Aufgabe, ggf. `RemainAfterExit=yes` |
| `dbus` | Bereitschaft über D-Bus-Name |

Neustart:

```ini
Restart=on-failure
RestartSec=5s
StartLimitIntervalSec=60s
StartLimitBurst=5
```

Nicht unendlich schnell neustarten; sonst Log-/Ressourcensturm. Für erwartetes sauberes Ende `on-failure` meist besser als `always`.

Exitstatus:

```bash
systemctl show app -p ExecMainCode,ExecMainStatus,Result,NRestarts
```

## Umgebung, Benutzer und Sicherheit

Environment:

```ini
[Service]
Environment=MODE=production
EnvironmentFile=-/etc/app/app.env
```

Environment ist kein idealer Secret Store; Werte können für privilegierte Beobachter sichtbar sein. systemd Credentials oder externen Secret Manager erwägen.

### Hardening

```ini
[Service]
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/lib/app /var/log/app
CapabilityBoundingSet=
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
LockPersonality=yes
MemoryDenyWriteExecute=yes
```

Nicht blind aktivieren; Anwendung systematisch testen.

Analyse:

```bash
systemd-analyze security app.service
```

Dynamischer Benutzer:

```ini
DynamicUser=yes
StateDirectory=app
CacheDirectory=app
LogsDirectory=app
```

systemd erstellt verwaltete Verzeichnisse mit passender Identität.

## Timer

Service:

```ini
# backup.service
[Unit]
Description=Backup ausführen

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/backup.sh
```

Timer:

```ini
# backup.timer
[Unit]
Description=Tägliches Backup

[Timer]
OnCalendar=*-*-* 02:15:00
Persistent=true
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now backup.timer
systemctl list-timers --all
```

Kalender testen:

```bash
systemd-analyze calendar '*-*-* 02:15:00'
```

Monotone Timer:

```ini
OnBootSec=10min
OnUnitActiveSec=1h
```

> [!tip]
> `Persistent=true` holt verpasste Kalenderausführungen nach. Für nicht idempotente Jobs bewusst entscheiden.

## Targets und Boot

```bash
systemctl get-default
sudo systemctl set-default multi-user.target
systemctl list-units --type=target
```

Isolieren:

```bash
sudo systemctl isolate rescue.target
```

Das stoppt möglicherweise viele Dienste und kann Remotezugriff trennen.

Bootanalyse:

```bash
systemd-analyze
systemd-analyze blame
systemd-analyze critical-chain
systemd-analyze plot > boot.svg
```

`blame` zeigt Aktivierungszeit, nicht zwingend Ursache der kritischen Bootkette.

## Journal

### Filtern

```bash
journalctl -b
journalctl -b -1
journalctl -u app.service
journalctl -u app.service -f
journalctl --since '2026-07-17 08:00' --until '09:00'
journalctl -p warning..alert -b
journalctl _PID=1234
journalctl _UID=1000
journalctl _COMM=sshd
journalctl -k -b
```

JSON:

```bash
journalctl -u app -o json-pretty -n 1
journalctl -u app -o json-seq
```

Boots:

```bash
journalctl --list-boots
```

Größe:

```bash
journalctl --disk-usage
sudo journalctl --vacuum-size=1G
sudo journalctl --vacuum-time=30d
```

Persistenz über `/var/log/journal` beziehungsweise journald-Konfiguration; Datenschutz und Retention abstimmen.

## Ressourcen und Cgroups

Live:

```bash
systemd-cgtop
systemctl status app
systemctl show app -p MemoryCurrent,CPUUsageNSec,TasksCurrent
```

Limits:

```ini
[Service]
MemoryMax=1G
CPUQuota=150%
TasksMax=256
IOWeight=100
```

Temporär:

```bash
sudo systemctl set-property --runtime app.service MemoryMax=1G
```

Dauerhaft ohne `--runtime`; erzeugt Drop-in. Limits unter realer Last testen.

Transient:

```bash
systemd-run --unit=testjob --property=MemoryMax=512M /usr/local/bin/job
systemd-run --user --scope -p CPUWeight=50 make -j8
```

## User-Units

```bash
systemctl --user status
systemctl --user daemon-reload
systemctl --user enable --now my-agent.service
journalctl --user -u my-agent.service
```

Pfad:

```text
~/.config/systemd/user/
```

Linger für Start ohne aktive Login-Sitzung:

```bash
loginctl show-user "$USER" -p Linger
sudo loginctl enable-linger "$USER"
```

Sicherheits- und Ressourcenfolgen bedenken.

## Diagnose

### Unit nicht gefunden

```bash
systemctl list-unit-files | grep name
systemctl show name -p LoadState,FragmentPath
systemctl daemon-reload
```

### Startlimit erreicht

```bash
systemctl status app
journalctl -u app -b
systemctl show app -p NRestarts,Result
sudo systemctl reset-failed app
```

Erst Ursache beheben, dann resetten.

### Prozess läuft manuell, nicht als Service

Unterschiede prüfen:

- Benutzer/Gruppe
- WorkingDirectory
- PATH/Environment
- HOME
- SELinux-Kontext
- Dateirechte
- Capability/Hardening
- Netzwerk-/Mount-Reihenfolge
- TTY/Interaktivität

```bash
systemctl show app -p User,Group,WorkingDirectory,Environment,ExecStart
```

### Universelle Prüfreihenfolge

```bash
systemctl status app --no-pager -l
journalctl -u app -b --no-pager -n 200
systemctl cat app
systemctl show app
systemd-analyze verify /pfad/app.service
```

Dann Dienstkonfiguration mit dessen eigenem Validator, Pfade/Rechte/SELinux, Port und Abhängigkeiten prüfen.

## Quellen
- [systemd Manual Pages](https://www.freedesktop.org/software/systemd/man/latest/)
- [systemctl](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
- [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- [journalctl](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html)

## Verwandte Notizen
- [[Fedora-RHEL-Cheatsheet]]
- [[Timemanagement-unter-Linux-Cheatsheet]]
- [[dmesg-Cheatsheet]]
- [[SELinux-Cheatsheet]]
