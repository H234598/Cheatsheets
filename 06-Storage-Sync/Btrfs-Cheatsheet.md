---
title: "Btrfs – Cheatsheet"
aliases: ["Btrfs Cheatsheet", "btrfs subvolume snapshot", "Btrfs Administration"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [btrfs, filesystem, linux, snapshots, cow, raid]
source: "https://btrfs.readthedocs.io/"
---

# Btrfs – Cheatsheet

> [!abstract] Zweck
> Ausführliche Btrfs-Referenz für Subvolumes, Snapshots, Send/Receive, Kompression, Multi-Device-Profile, Scrub, Balance, Replace, Quotas, Rescue, Fedora-Layouts und sichere Reparatur.

> [!danger] `btrfs check --repair` ist keine Routine
> `btrfs check --repair` nur nach aktueller Upstream-Anleitung, Backup/Image und klarer Diagnose verwenden. Es kann Schäden verschlimmern. Zuerst read-only mount, Scrub, Logs und nichtschreibende Checks.

## Inhalt

- [[#Grundmodell]]
- [[#Inventar]]
- [[#Erstellen und Mounten]]
- [[#Subvolumes]]
- [[#Snapshots und Rollback]]
- [[#Send und Receive]]
- [[#Kompression und COW]]
- [[#Multi-Device und Profile]]
- [[#Scrub, Balance und Defrag]]
- [[#Gerät hinzufügen, entfernen und ersetzen]]
- [[#Quotas und Qgroups]]
- [[#Kapazität verstehen]]
- [[#Recovery und Diagnose]]
- [[#Fedora-Layout]]

## Grundmodell

Btrfs integriert:

- Copy-on-Write
- Checksummen für Daten und Metadaten
- Subvolumes
- Snapshots
- transparente Kompression
- Reflinks
- mehrere Geräte/RAIDprofile
- Send/Receive

Subvolume ist kein Blockvolume, sondern eigener Dateibaum mit Snapshotgrenze. Subvolumes teilen dasselbe Dateisystem/Storagepool.

## Inventar

```bash
findmnt -t btrfs
btrfs filesystem show
sudo btrfs filesystem usage -T /mount
sudo btrfs device stats /mount
sudo btrfs subvolume list /mount
sudo btrfs property get /mount
```

Detail:

```bash
sudo btrfs inspect-internal dump-super -f /dev/sdX
```

Nur lesend und korrektes Gerät.

Features:

```bash
sudo btrfs filesystem show --raw
sudo btrfs inspect-internal dump-super /dev/sdX | grep -i incompat
```

## Erstellen und Mounten

> [!danger]
> `mkfs.btrfs` löscht bestehende Dateisystemstruktur. Geräte und Backups prüfen.

Ein Gerät:

```bash
sudo mkfs.btrfs -L DATA /dev/sdX1
```

Mirror über zwei Geräte:

```bash
sudo mkfs.btrfs -L DATA -d raid1 -m raid1 /dev/sdX1 /dev/sdY1
```

Daten- und Metadatenprofil sind getrennt (`-d`, `-m`).

Mount:

```bash
sudo mount /dev/disk/by-label/DATA /srv/data
```

Optionen:

```fstab
LABEL=DATA /srv/data btrfs defaults,compress=zstd:3,noatime 0 0
```

Mountoptionen gelten teilweise dateisystemweit, auch wenn über Subvolume gemountet.

UUID:

```bash
blkid
```

## Subvolumes

Erstellen:

```bash
sudo btrfs subvolume create /srv/data/projects
```

Liste:

```bash
sudo btrfs subvolume list -t /srv/data
sudo btrfs subvolume show /srv/data/projects
```

Default Subvolume:

```bash
sudo btrfs subvolume get-default /srv/data
sudo btrfs subvolume set-default ID /srv/data
```

Mount per Name:

```fstab
UUID=... /home btrfs subvol=@home,compress=zstd:3 0 0
```

Oder ID:

```text
subvolid=256
```

Name ist lesbarer; ID bleibt nach Rename, aber Layoutabhängigkeiten dokumentieren.

Löschen:

```bash
sudo btrfs subvolume delete /srv/data/old
sudo btrfs subvolume sync /srv/data
```

Ein Subvolume kann verschachtelte Subvolumes enthalten, die bei Snapshot nicht rekursiv als Inhalt kopiert werden; sie erscheinen als separate Grenzen/leere Verzeichnispunkte je Zugriff. Layout bewusst planen.

## Snapshots und Rollback

Read-only Snapshot:

```bash
sudo btrfs subvolume snapshot -r /srv/data/projects /srv/data/.snapshots/projects-2026-07-17
```

Beschreibbar:

```bash
sudo btrfs subvolume snapshot /srv/data/projects /srv/data/projects-test
```

Snapshot ist zunächst billig, wächst mit Divergenz.

Rollback ist kein einzelner universeller Befehl. Typisches Boot-/Root-Schema:

1. aktuellen Subvolumezustand sichern.
2. gewünschten read-only Snapshot in neues beschreibbares Subvolume snapshotten.
3. Default-/Bootloader-/fstab-Zuordnung anpassen.
4. reboot/test.

Nie laufendes Root-Subvolume unkoordiniert ersetzen.

Snapshots löschen:

```bash
sudo btrfs subvolume delete /srv/data/.snapshots/alt
```

Freigabe erfolgt verzögert; `subvolume sync`/Usage beobachten.

## Send und Receive

Read-only Snapshot erforderlich:

```bash
sudo btrfs send /srv/data/.snapshots/snap1 |
  sudo btrfs receive /backup/
```

Über SSH:

```bash
sudo btrfs send /srv/data/.snapshots/snap1 |
  ssh backup sudo btrfs receive /backup/data
```

Inkrementell:

```bash
sudo btrfs send -p /srv/data/.snapshots/snap1 \
  /srv/data/.snapshots/snap2 |
  ssh backup sudo btrfs receive /backup/data
```

Parent Snapshot muss auf Quelle/Ziel passend vorhanden und unverändert/read-only sein.

Größe/Fortschritt über `pv`:

```bash
sudo btrfs send snapshot | pv | ssh backup sudo btrfs receive /backup
```

Protokollversion/Features zwischen Kerneln/Tools prüfen.

## Kompression und COW

Mountoption:

```text
compress=zstd:3
```

Erzwungen:

```text
compress-force=zstd:3
```

Property pro Datei/Verzeichnis/Subvolume:

```bash
sudo btrfs property set /srv/data/projects compression zstd
btrfs property get /srv/data/projects compression
```

Nur neu geschriebene Daten werden angepasst. Bestehende Daten neu defragmentieren/komprimieren:

```bash
sudo btrfs filesystem defragment -r -czstd /srv/data/projects
```

> [!warning]
> Defragmentierung bricht Reflink-/Snapshot-Blocksharing für bearbeitete Dateien auf und kann stark zusätzlichen Platz belegen. Nicht pauschal auf snapshotreichen Bäumen ausführen.

NOCOW für spezielle Dateien:

```bash
sudo chattr +C /srv/data/vm
```

`+C` vor Erstellung der Dateien setzen. NOCOW deaktiviert typischerweise Datenchecksummen/Kompression für diese Dateien und beeinflusst Snapshots. Nur nach Workloadabwägung.

Reflink:

```bash
cp --reflink=always quelle.img clone.img
```

## Multi-Device und Profile

Anzeigen:

```bash
sudo btrfs filesystem usage /srv/data
sudo btrfs device usage /srv/data
```

Profile:

| Profil | Prinzip |
|---|---|
| `single` | eine Kopie über Geräte verteilt |
| `dup` | zwei Kopien auf demselben Gerät, häufig Metadaten |
| `raid1` | zwei Kopien auf unterschiedlichen Geräten |
| `raid1c3`/`raid1c4` | drei/vier Kopien |
| `raid10` | Stripe über Mirrors |
| `raid5`/`raid6` | Parität; konservativ und releaseabhängig bewerten |

Btrfs RAID1 bedeutet zwei Kopien, nicht zwingend klassischer Mirror identischer Disks; Kapazität hängt von Gerätegrößen ab.

Konvertieren via Balance:

```bash
sudo btrfs balance start -dconvert=raid1 -mconvert=raid1 /srv/data
```

Vorher freien Platz, Geräte und Backup prüfen. Große Balance kann lange dauern.

## Scrub, Balance und Defrag

### Scrub

```bash
sudo btrfs scrub start -Bd /srv/data
```

Status:

```bash
sudo btrfs scrub status /srv/data
```

Scrub liest Daten und verifiziert Checksummen; bei redundanter guter Kopie repariert er.

### Balance

Balance reorganisiert Chunks, ist **kein** Scrub und keine Defragmentierung von Dateien.

Status:

```bash
sudo btrfs balance status /srv/data
```

Gezielt wenig belegte Chunks:

```bash
sudo btrfs balance start -dusage=10 -musage=10 /srv/data
```

Nicht pauschal Full Balance; erzeugt viel I/O und braucht Workspace.

### Defrag

Einzelne große Datei:

```bash
sudo btrfs filesystem defragment -v /srv/data/file
```

Mit Kompression:

```bash
sudo btrfs filesystem defragment -czstd /srv/data/file
```

Snapshotsharing beachten.

## Gerät hinzufügen, entfernen und ersetzen

Hinzufügen:

```bash
sudo btrfs device add /dev/disk/by-id/NEW /srv/data
```

Danach Daten nicht automatisch passend verteilt. Gezielte Balance/Profilekonvertierung.

Entfernen:

```bash
sudo btrfs device remove /dev/disk/by-id/OLD /srv/data
```

Benötigt genug Platz/Redundanz auf übrigen Geräten.

Replace:

```bash
sudo btrfs replace start -B \
  /dev/disk/by-id/OLD \
  /dev/disk/by-id/NEW \
  /srv/data
```

Status:

```bash
sudo btrfs replace status /srv/data
```

Resize einzelnes Device:

```bash
sudo btrfs filesystem resize max /srv/data
sudo btrfs filesystem resize 1:max /srv/data
```

Verkleinern:

```bash
sudo btrfs filesystem resize -10G /srv/data
```

Vor darunterliegendem Partition/LV-Shrink und mit ausreichend unallokiertem Platz.

## Quotas und Qgroups

Aktivieren:

```bash
sudo btrfs quota enable /srv/data
```

Anzeigen:

```bash
sudo btrfs qgroup show -reF /srv/data
```

Limit:

```bash
sudo btrfs qgroup limit 500G /srv/data/projects
```

Qgroups können bei vielen Snapshots Performance/Accounting-Komplexität erzeugen. Status prüfen, nicht blind aktivieren.

Rescan:

```bash
sudo btrfs quota rescan -w /srv/data
```

Neuere einfache Quota-/Squota-Funktionen sind versionsabhängig; Upstreamdoku des Systems prüfen.

## Kapazität verstehen

`df` allein kann irreführen. Verwenden:

```bash
sudo btrfs filesystem usage -T /srv/data
sudo btrfs filesystem df /srv/data
sudo btrfs device usage /srv/data
```

Unterscheiden:

- Device size
- allocated chunks
- used in chunks
- unallocated
- data/metadata/system profile
- global reserve

ENOSPC kann auftreten, obwohl nominell Platz frei ist, wenn keine passenden Metadata-/Data-Chunks angelegt werden können. Gezielte Balance und Snapshotbereinigung, nicht unüberlegt Vollbalance.

Snapshots/gelöschte offene Dateien:

```bash
sudo btrfs subvolume list /srv/data
sudo lsof +L1
```

## Recovery und Diagnose

Logs:

```bash
journalctl -k -b | grep -i btrfs
sudo btrfs device stats /srv/data
sudo btrfs scrub status /srv/data
```

Read-only Mount:

```bash
sudo mount -o ro,usebackuproot /dev/sdX /mnt/recovery
```

Optionen sind versionsabhängig; `man btrfs`/`mount -t btrfs` prüfen.

Nichtschreibender Check:

```bash
sudo btrfs check --readonly /dev/sdX
```

Rescue-Kommandos:

```bash
btrfs rescue --help
```

`btrfs restore` kann Dateien aus einem unmountbaren FS kopieren, ohne es zu reparieren:

```bash
sudo btrfs restore -vi /dev/sdX /backup/recovered
```

Vorher Ziel auf anderem Dateisystem mit genug Platz.

Recovery-Reihenfolge:

1. I/O stoppen, Hardwareursache prüfen.
2. Logs/Superblocks/Geräte dokumentieren.
3. Image/Backup.
4. read-only mount mit dokumentierten Optionen.
5. `btrfs restore` für Datenrettung.
6. `btrfs check --readonly`.
7. Upstream/Expertenhilfe.
8. `--repair` nur explizit begründet.

## Fedora-Layout

Fedora nutzt häufig Btrfs-Subvolumes für Root/Home, z. B.:

```text
root
home
```

Anzeigen:

```bash
findmnt /
findmnt /home
sudo btrfs subvolume list /
```

Snapshots sind nicht automatisch vollständige System-Rollbacks. `/boot`, EFI, Datenbanken, Container, Flatpak, SELinux und Bootloader müssen berücksichtigt werden.

## Quellen
- [Btrfs Documentation](https://btrfs.readthedocs.io/)
- [Btrfs Kernel Documentation](https://docs.kernel.org/filesystems/btrfs.html)
- [btrfs-progs Manual](https://btrfs.readthedocs.io/en/latest/btrfs.html)

## Verwandte Notizen
- [[Dateisysteme – Cheatsheet]]
- [[Fedora-RHEL – Cheatsheet]]
- [[rsync – Cheatsheet]]
- [[Dateikompression unter Linux – Cheatsheet]]
