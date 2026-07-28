---
title: "dmesg – Cheatsheet"
aliases: ["Kernel Ring Buffer Cheatsheet", "Linux Kernelmeldungen", "dmesg Diagnose"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, kernel, dmesg, diagnose, logs]
source: "https://man7.org/linux/man-pages/man1/dmesg.1.html"
---

# dmesg – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für Kernelmeldungen, Boot- und Hardwarediagnose, Level/Facilities, Live-Ausgabe, Zeitstempel, Journal-Abgleich, Filterung und sichere Fehleranalyse.

> [!warning] Zeitstempel richtig einordnen
> Kernelmeldungen verwenden intern Zeit seit dem Boot. `dmesg -T` rechnet auf Wandzeit um, kann nach Zeitkorrekturen oder Suspend/Resume aber ungenau sein. Für belastbare Zeitbezüge zusätzlich `journalctl -k` verwenden.

## Inhalt

- [[#Grundmodell]]
- [[#Wichtige Aufrufe]]
- [[#Level und Facilities]]
- [[#Boot- und Hardwarediagnose]]
- [[#Live beobachten]]
- [[#Journal und persistente Logs]]
- [[#Berechtigungen]]
- [[#Typische Suchmuster]]
- [[#Diagnose-Reihenfolge]]

## Grundmodell

`dmesg` liest den Kernel-Ringpuffer. Darin landen unter anderem:

- Treiberinitialisierung
- erkannte Hardware
- Dateisystem- und Blockgerätefehler
- OOM-Killer-Ereignisse
- Netzwerklink- und Firmwaremeldungen
- USB-Ereignisse
- ACPI/IOMMU/Suspend-Probleme
- Security- und Audit-Hinweise

Der Ringpuffer ist begrenzt. Alte Meldungen werden überschrieben; `dmesg` ist daher nicht automatisch ein dauerhaftes Logarchiv.

## Wichtige Aufrufe

```bash
dmesg
sudo dmesg --human
dmesg --color=always | less -R
```

Zeitdarstellung:

```bash
dmesg -T             # lesbare Wandzeit, potenziell ungenau
dmesg -t             # ohne Zeitstempel
dmesg --reltime      # relative Zeit mit Delta
dmesg --ctime        # wie -T
```

Nur neue Meldungen live:

```bash
sudo dmesg --follow
sudo dmesg --follow-new
```

Puffergröße und Statistik:

```bash
sudo dmesg --buffer-size 1048576
cat /proc/sys/kernel/printk
```

Puffer leeren – nur bewusst:

```bash
sudo dmesg --clear
```

> [!danger]
> `dmesg --clear` entfernt wichtige Diagnoseinformationen aus dem Ringpuffer. Vorher sichern, etwa mit `dmesg > dmesg-vorher.txt`.

## Level und Facilities

Nur Fehler und kritischer:

```bash
dmesg --level=err,crit,alert,emerg
```

Warnungen plus Fehler:

```bash
dmesg --level=warn,err,crit,alert,emerg
```

Typische Prioritäten:

| Level | Bedeutung |
|---|---|
| `emerg` | System unbenutzbar |
| `alert` | sofortiges Eingreifen |
| `crit` | kritischer Zustand |
| `err` | Fehler |
| `warn` | Warnung |
| `notice` | bemerkenswert, aber normal möglich |
| `info` | Information |
| `debug` | Debugausgabe |

Nach Facility:

```bash
dmesg --facility=kern
dmesg --facility=daemon
```

Rohformat inklusive Facility/Level:

```bash
dmesg --decode
```

## Boot- und Hardwarediagnose

Kernel des aktuellen Boots:

```bash
journalctl -k -b
journalctl -k -b -1      # vorheriger Boot, falls persistent vorhanden
```

Häufige Filter:

```bash
dmesg -T | grep -Ei 'error|fail|warn|timeout|reset'
dmesg -T | grep -Ei 'nvme|ata|scsi|i/o error|blk_update'
dmesg -T | grep -Ei 'usb|xhci|type-c|thunderbolt'
dmesg -T | grep -Ei 'drm|gpu|amdgpu|i915|nouveau|nvidia'
dmesg -T | grep -Ei 'oom|out of memory|killed process'
dmesg -T | grep -Ei 'segfault|general protection|call trace|panic'
dmesg -T | grep -Ei 'acpi|iommu|suspend|resume'
dmesg -T | grep -Ei 'firmware|microcode'
```

Nur aktuelles Gerät nach Einstecken beobachten:

```bash
sudo dmesg -w
# Gerät einstecken oder Fehler reproduzieren
```

Blockgerätebezug ergänzen:

```bash
lsblk -o NAME,MODEL,SERIAL,SIZE,FSTYPE,MOUNTPOINTS
sudo smartctl -a /dev/nvme0
sudo nvme smart-log /dev/nvme0
```

## Live beobachten

```bash
sudo dmesg -wH
```

Mit Filter, wobei Zeilenpufferung wichtig ist:

```bash
sudo dmesg -wH | grep --line-buffered -Ei 'usb|error|reset'
```

Alternativ im Journal:

```bash
sudo journalctl -kf
```

> [!tip]
> Für reproduzierbare Diagnose zuerst Terminal mit Live-Ausgabe starten, dann genau eine Aktion ausführen. So lässt sich Ursache und Folge besser zuordnen.

## Journal und persistente Logs

Aktueller Boot, nur Kernel:

```bash
journalctl --dmesg
journalctl -k -b
journalctl -k -b --priority=warning
```

Zeitfenster:

```bash
journalctl -k --since '2026-07-17 08:00' --until '2026-07-17 08:30'
```

Vorherige Boots:

```bash
journalctl --list-boots
journalctl -k -b -1
```

Persistenz prüfen:

```bash
ls -ld /var/log/journal
journalctl --disk-usage
```

## Berechtigungen

Manche Distributionen beschränken unprivilegierten Zugriff:

```bash
sysctl kernel.dmesg_restrict
```

Temporär ändern:

```bash
sudo sysctl kernel.dmesg_restrict=0
```

Dauerhaft nur nach Sicherheitsabwägung:

```ini
# /etc/sysctl.d/90-dmesg.conf
kernel.dmesg_restrict = 1
```

> [!important]
> Kernelmeldungen können Adressen, Gerätenamen und sicherheitsrelevante Interna offenlegen. Die Beschränkung nicht nur aus Bequemlichkeit deaktivieren.

## Typische Suchmuster

| Symptom | Suchbegriffe |
|---|---|
| Platte verschwindet | `reset`, `I/O error`, `ata`, `nvme`, `timeout` |
| USB trennt sich | `USB disconnect`, `device descriptor`, `xhci` |
| WLAN instabil | Treibername, `firmware`, `deauth`, `timeout` |
| Grafik friert ein | `drm`, `GPU HANG`, `amdgpu`, `i915`, `Xid` |
| RAM knapp | `oom-kill`, `Out of memory`, `Killed process` |
| Boot hängt | letzte Meldungen, `dependency`, `firmware`, `fsck` |
| Suspend scheitert | `PM:`, `suspend`, `resume`, `ACPI` |
| Kernelabsturz | `BUG:`, `Oops`, `Call Trace`, `panic` |

## Diagnose-Reihenfolge

```bash
uname -a
uptime -s
sudo dmesg --level=warn,err,crit,alert,emerg --ctime
journalctl -k -b --priority=warning
lspci -nnk
lsusb -t
lsblk -f
```

Dann:

1. Zeitpunkt und reproduzierbare Aktion bestimmen.
2. Kernel-/Treibernamen identifizieren.
3. Vollständigen Meldungskontext sichern, nicht nur eine einzelne Fehlerzeile.
4. Firmware-, Kernel- und Hardwarestand dokumentieren.
5. Gegen vorherigen Boot oder bekannte funktionierende Version vergleichen.
6. Hardwaretests und SMART/NVMe-Daten ergänzen.
7. Erst danach Treiberparameter oder Blacklists ändern.

## Quellen
- [util-linux dmesg Manual](https://man7.org/linux/man-pages/man1/dmesg.1.html)
- [systemd journalctl](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html)

## Verwandte Notizen
- [[grep – Cheatsheet]]
- [[ls-Familie und Hardwareinventar – Cheatsheet]]
- [[Systemd – Cheatsheet]]
