---
title: "ls-Familie und Hardwareinventar – Cheatsheet"
aliases: ["lspci lsusb lsblk lshw Cheatsheet", "Linux Hardware anzeigen", "ls Kommandofamilie", "ls-und-Hardware-Tools-Cheatsheet"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, hardware, inventory, lsblk, lspci, lsusb, lshw]
source: "https://www.gnu.org/software/coreutils/manual/html_node/ls-invocation.html"
---

# ls-Familie und Hardwareinventar – Cheatsheet

> [!abstract] Zweck
> Übersicht über `ls` und die wichtigsten Linux-Inventarwerkzeuge: Dateien, PCI, USB, Blockgeräte, CPU, RAM, Module, Namespaces, offene Dateien, Locks, Attribute und sichere Diagnosekombinationen.

> [!note] Interpretation der Themenangabe
> „ls(pur,usb,blk,hw, …)“ wird als Familie aus `ls`, `lspci`, `lsusb`, `lsblk`, `lshw` und verwandten Inventarbefehlen verstanden. Ein verbreitetes Standardwerkzeug `lspur` existiert nicht.

## Inhalt

- [[#Dateien mit ls]]
- [[#PCI mit lspci]]
- [[#USB mit lsusb]]
- [[#Blockgeräte mit lsblk]]
- [[#Gesamthardware mit lshw]]
- [[#CPU und Arbeitsspeicher]]
- [[#Kernelmodule, Namespaces und Prozesse]]
- [[#Offene Dateien, Locks und Attribute]]
- [[#Inventar-Schnelllauf]]
- [[#Diagnose-Matrix]]

## Dateien mit ls

```bash
ls
ls -lah
ls -lA
ls -lt
ls -ltr
ls -lS
ls -li
ls -ld /pfad/verzeichnis
```

Nützliche Optionen:

| Option | Wirkung |
|---|---|
| `-l` | Langformat |
| `-a` | inklusive `.` und `..` |
| `-A` | versteckte Einträge, ohne `.` und `..` |
| `-h` | lesbare Größen |
| `-t` | nach Änderungszeit |
| `-S` | nach Größe |
| `-r` | Reihenfolge umkehren |
| `-d` | Verzeichnis selbst statt Inhalt |
| `-i` | Inode |
| `-n` | numerische UID/GID |
| `-Z` | SELinux-Kontext |
| `--time-style=long-iso` | stabile Zeitdarstellung |

Robuste Skripte sollten `ls` nicht parsen. Stattdessen:

```bash
find . -maxdepth 1 -type f -print0
stat --printf='%n\0' -- *
```

> [!warning]
> Dateinamen können Zeilenumbrüche, Tabs und führende Bindestriche enthalten. Menschlich schöne `ls`-Ausgabe ist kein sicheres Maschinenformat.

## PCI mit lspci

```bash
lspci
lspci -nn
lspci -nnk
sudo lspci -vv
sudo lspci -vvv
lspci -t
```

Nur Grafik:

```bash
lspci -nnk | grep -A3 -Ei 'VGA|3D|Display'
```

Nur Netzwerk:

```bash
lspci -nnk | grep -A3 -Ei 'Ethernet|Network'
```

Treiberzuordnung:

```text
Kernel driver in use: aktuell gebundener Treiber
Kernel modules:        mögliche Module
```

PCI-ID-Datenbank aktualisieren, falls Paket dies unterstützt:

```bash
sudo update-pciids
```

## USB mit lsusb

```bash
lsusb
lsusb -t
sudo lsusb -v
lsusb -d 046d:c534
```

Baumansicht zeigt Geschwindigkeit und Treiber:

```bash
lsusb -t
```

Live-Ereignisse ergänzen:

```bash
sudo dmesg -wH
udevadm monitor --environment --udev
```

Geräteeigenschaften:

```bash
udevadm info --query=all --name=/dev/ttyUSB0
```

> [!tip]
> Bei USB-Problemen `lsusb -t` vor und nach dem Einstecken vergleichen. Hubpfad, USB-Version, Treiber und Geschwindigkeit notieren.

## Blockgeräte mit lsblk

Standard:

```bash
lsblk
lsblk -f
lsblk -o NAME,PATH,TYPE,SIZE,FSTYPE,FSVER,LABEL,UUID,PARTUUID,MOUNTPOINTS
```

Topologie und Alignment:

```bash
lsblk -t
lsblk -o NAME,PHY-SEC,LOG-SEC,MIN-IO,OPT-IO,ALIGNMENT,ROTA,DISC-MAX
```

Nur echte Disks:

```bash
lsblk -d -o NAME,MODEL,SERIAL,SIZE,TRAN,ROTA
```

JSON für Skripte:

```bash
lsblk --json -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS
```

Mounts ergänzen:

```bash
findmnt
findmnt --verify
findmnt -no SOURCE,FSTYPE,OPTIONS /
```

> [!danger]
> Vor `fdisk`, `mkfs`, `wipefs`, `dd` oder ZFS-Kommandos immer `lsblk -o NAME,PATH,MODEL,SERIAL,SIZE,MOUNTPOINTS` prüfen. Gerätenamen können sich nach Neustart ändern; Seriennummer/WWN einbeziehen.

## Gesamthardware mit lshw

Kurz:

```bash
sudo lshw -short
```

Bestimmte Klassen:

```bash
sudo lshw -class system
sudo lshw -class processor
sudo lshw -class memory
sudo lshw -class network
sudo lshw -class storage -class disk
```

HTML/JSON/XML:

```bash
sudo lshw -html > hardware.html
sudo lshw -json > hardware.json
sudo lshw -xml > hardware.xml
```

Seriennummern und Asset-Tags können sensibel sein. Vor Weitergabe anonymisieren.

Alternative DMI-Daten:

```bash
sudo dmidecode -t system
sudo dmidecode -t bios
sudo dmidecode -t memory
```

## CPU und Arbeitsspeicher

CPU:

```bash
lscpu
lscpu -e
lscpu -J
nproc
cat /proc/cpuinfo
```

NUMA:

```bash
numactl --hardware
lscpu | grep -i numa
```

RAM:

```bash
free -h
lsmem
cat /proc/meminfo
sudo dmidecode -t memory
```

Speicherdruck:

```bash
vmstat 1
cat /proc/pressure/memory
```

## Kernelmodule, Namespaces und Prozesse

Module:

```bash
lsmod
modinfo i915
modprobe --show-depends i915
```

Namespaces:

```bash
lsns
lsns -t net
lsns -p 1234
```

Prozesse:

```bash
ps auxf
pstree -ap
systemd-cgls
```

Netzwerkobjekte:

```bash
ip -br link
ip -br address
ss -tulpn
```

## Offene Dateien, Locks und Attribute

Offene Dateien/Ports:

```bash
sudo lsof
sudo lsof /var/lib/app/data.db
sudo lsof -iTCP -sTCP:LISTEN -P -n
sudo lsof +D /mnt/daten
```

`+D` kann auf großen Bäumen teuer sein. Für Mounts oft besser:

```bash
sudo fuser -vm /mnt/daten
```

Locks:

```bash
lslocks
lslocks --json
```

Dateiattribute:

```bash
lsattr datei
sudo chattr +i wichtige.conf
sudo chattr -i wichtige.conf
```

ACL und xattrs:

```bash
getfacl datei
getfattr -d datei
ls -lZ datei
```

## Inventar-Schnelllauf

```bash
hostnamectl
uname -a
cat /etc/os-release
lscpu
free -h
lsblk -f
lspci -nnk
lsusb -t
ip -br address
sudo lshw -short
```

Als Supportpaket, sensible Daten prüfen:

```bash
{
  date -Is
  hostnamectl
  uname -a
  cat /etc/os-release
  lscpu
  free -h
  lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS
  lspci -nnk
  lsusb -t
} > system-inventar.txt
```

## Diagnose-Matrix

| Frage | Primärbefehl | Ergänzung |
|---|---|---|
| Welche GPU und welcher Treiber? | `lspci -nnk` | `dmesg`, `glxinfo -B` |
| Welches USB-Gerät an welchem Hub? | `lsusb -t` | `udevadm`, `dmesg -w` |
| Welches Dateisystem ist wo gemountet? | `lsblk -f` | `findmnt` |
| Welche Disk ist physisch gemeint? | `lsblk -d ...SERIAL` | `/dev/disk/by-id` |
| Welche RAM-Module? | `dmidecode -t memory` | Herstellerdiagnose |
| Welcher Prozess hält Datei/Mount? | `lsof`, `fuser` | `lslocks` |
| Welche Kernelmodule? | `lsmod` | `modinfo` |
| Welche SELinux-/ACL-Metadaten? | `ls -Z`, `getfacl` | `getfattr` |

## Quellen
- [GNU Coreutils ls](https://www.gnu.org/software/coreutils/manual/html_node/ls-invocation.html)
- [util-linux lsblk](https://man7.org/linux/man-pages/man8/lsblk.8.html)
- [pciutils](https://mj.ucw.cz/sw/pciutils/)
- [usbutils](https://github.com/gregkh/usbutils)

## Verwandte Notizen
- [[dmesg – Cheatsheet]]
- [[fdisk – Cheatsheet]]
- [[Linux-Netzwerk – Cheatsheet]]
- [[POSIX-ACL – Cheatsheet]]
