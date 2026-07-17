---
title: "Dateisysteme – Premium-Spickzettel"
aliases: ["Filesysteme Übersicht", "Linux Dateisystemvergleich", "ZFS XFS Btrfs ext4", "Linux-Dateisysteme-Premium-Spickzettel"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [filesystem, storage, linux, zfs, xfs, btrfs, ext4]
source: "https://docs.kernel.org/filesystems/"
---

# Dateisysteme – Premium-Spickzettel

> [!abstract] Zweck
> Entscheidungs- und Diagnoseübersicht für ZFS, XFS, Btrfs, ext4 und weitere Dateisysteme: Integrität, Snapshots, RAID, Wachstum, Shrink, Quotas, Recovery, Workloads und Auswahlkriterien.

> [!danger] Dateisystemoperationen sind datenkritisch
> Vor `mkfs`, Poolerstellung, Repartitionierung, Shrink, RAID-Umbau oder Reparatur Gerätenamen, Mounts, Seriennummern und Backups prüfen. Ein Snapshot ist kein Ersatz für ein getrenntes Backup.

## Inhalt

- [[#Begriffe und Schichten]]
- [[#Vergleich]]
- [[#Auswahl nach Workload]]
- [[#Integrität und Prüfsummen]]
- [[#Snapshots, Clones und Backups]]
- [[#RAID und Redundanz]]
- [[#Wachstum und Verkleinerung]]
- [[#Mountoptionen]]
- [[#Quotas und Reservierungen]]
- [[#Diagnosewerkzeuge]]
- [[#Weitere Dateisysteme]]
- [[#Entscheidungscheckliste]]

## Begriffe und Schichten

```text
Anwendung
  ↓
Dateisystem / Dataset
  ↓
Volume Manager / Pool / RAID
  ↓
Partition / Blockgerät
  ↓
Controller / Disk / SSD
```

Nicht jedes System trennt diese Ebenen:

- ZFS integriert Pool, RAID, Volume Manager und Dateisystem.
- Btrfs integriert mehrere Geräte und RAIDprofile.
- XFS/ext4 liegen häufig auf LVM/MD RAID.
- TrueNAS verwaltet ZFS über eine Appliance-Schicht.

Wichtige Eigenschaften:

| Begriff | Bedeutung |
|---|---|
| Journaling | protokolliert Metadaten/teils Daten für Crash-Recovery |
| Copy-on-Write | überschreibt Blöcke nicht in place, sondern schreibt neue |
| Checksumming | erkennt Daten-/Metadatenkorruption je Umfang |
| Scrub | liest Daten und prüft Checksummen/Redundanz |
| Snapshot | Point-in-Time-Referenz, meist Copy-on-Write |
| Clone | beschreibbare Ableitung eines Snapshots |
| Reflink | mehrere Dateien teilen Blöcke bis zur Änderung |
| Quota | maximale Nutzung |
| Reservation | garantierter/gebundener Speicher |
| TRIM/Discard | informiert SSD über freie Blöcke |

## Vergleich

| Merkmal | ZFS | XFS | Btrfs | ext4 |
|---|---|---|---|---|
| Datenchecksummen | ja | nein für Nutzdaten | ja | nein für Nutzdaten |
| Metadatenchecksummen | ja | ja | ja | Journal/Metadatenmechanismen, keine End-to-End-Datenchecksummen |
| COW | ja | Metadaten/Reflink, nicht generell Daten-COW wie ZFS/Btrfs | ja | nein |
| Snapshots nativ | ja | nein; LVM/Storage darunter | ja | nein; LVM/Storage darunter |
| integriertes Multi-Device/RAID | ja | nein | ja | nein |
| Online wachsen | ja | ja | ja | ja |
| Shrink | Dataset logisch; vdev/pool komplex, kein klassischer Shrink | nein | ja | offline möglich |
| Reflink | Clones/Blocks via ZFS-Semantik | ja | ja | je Kernel/Feature nicht Standardbasis |
| typischer Fokus | Integrität, NAS, Snapshots | große Dateien, Enterprise, Performance | flexible COW-Snapshots | konservativ, universell |

> [!note]
> Eigenschaften hängen von Kernel-, Tool- und On-Disk-Featureversion ab. Vor Migration die konkrete Distribution und Wiederherstellungswerkzeuge prüfen.

## Auswahl nach Workload

### ZFS

Gut für:

- NAS/Backupserver
- starke Datenintegrität
- Snapshot/Replication
- große Storagepools
- Datasets mit getrennten Properties/Quotas

Beachten:

- RAM/ARC-Planung
- Topologie vor Poolerstellung
- Pool nicht zu voll
- dedup meist vermeiden
- Feature-Upgrades beeinflussen Rückwärtskompatibilität

### XFS

Gut für:

- RHEL/Fedora-Server
- große Dateien und parallele I/O
- große, wachsende Dateisysteme
- Reflink-basierte Kopien

Beachten:

- kein Shrink
- Snapshots über LVM/Storage
- `xfs_repair` offline

### Btrfs

Gut für:

- Snapshots/Rollbacks auf Linux
- Subvolumes
- transparente Kompression
- Desktop/Workstation
- Send/Receive

Beachten:

- Profile und freie Chunk-Struktur verstehen
- RAID5/6 konservativ bewerten
- Balance/Scrub nicht verwechseln
- Backup vor Reparatur

### ext4

Gut für:

- allgemeine Linux-Systeme
- einfache, bewährte Administration
- breite Recovery-/Boot-Unterstützung
- kleine bis große Standardworkloads

Beachten:

- keine nativen Snapshots/Datenchecksummen
- Shrink offline
- LVM/MD für flexible Storagefunktionen

## Integrität und Prüfsummen

End-to-End-Frage:

```text
Kann das System erkennen, dass gelesene Nutzdaten nicht mehr den ursprünglich geschriebenen Daten entsprechen?
```

- ZFS/Btrfs: Datenchecksummen; mit Redundanz kann Scrub oft selbst reparieren.
- XFS/ext4: Hardwarefehler können über Laufwerk/Controller erkannt werden, aber keine vollständige Nutzdaten-End-to-End-Prüfsumme im Dateisystem.
- Anwendungschecksummen und Backupverifikation bleiben wichtig.

SMART ist kein Dateisystemcheck:

```bash
smartctl -a /dev/sda
nvme smart-log /dev/nvme0
```

Scrub ist kein Backup: Er bestätigt/repariert vorhandene Blöcke, schützt nicht vor Löschen, Ransomware oder Fehlbedienung.

## Snapshots, Clones und Backups

Snapshot-Eigenschaften:

- zunächst platzsparend
- halten alte Blöcke fest
- wachsen mit Änderungen
- liegen meist auf demselben Fehlerdomänen-/Pool
- können bei vollem Pool problematisch werden

3-2-1-orientiert:

```text
3 Kopien
2 unterschiedliche Medien/Systeme
1 Kopie extern/offline/immutable
```

Replikation:

- ZFS `send/receive`
- Btrfs `send/receive`
- LVM Snapshot + Backupwerkzeug
- Dateibasiert `rsync`, `rclone`, Borg/Restic/Kopia

Anwendungskonsistenz:

- Crash-konsistent: Snapshot wie Stromausfallzeitpunkt.
- Applikationskonsistent: Datenbank/VM quiesced oder integriert.

## RAID und Redundanz

RAID schützt primär gegen Geräteausfall, nicht gegen:

- versehentliches Löschen
- logische Korruption
- Malware/Ransomware
- Brand/Diebstahl
- Controller-/Firmwarefehler
- falsche Administration

Topologien:

| Typ | Toleranz | Eigenschaften |
|---|---|---|
| Mirror | meist 1 Gerät je Mirror | schnelle Reads, einfache Resilver, 50 % Kapazität bei 2-way |
| RAIDZ1/RAID5 | 1 Gerät | bei großen Pools/Rebuildrisiko abwägen |
| RAIDZ2/RAID6 | 2 Geräte | häufig solide für breite Arrays |
| RAIDZ3 | 3 Geräte | große/risikoreiche Arrays |
| Stripe | 0 | Ausfall eines Geräts zerstört Verbund |

Btrfs-Profile haben andere Semantik als klassisches RAID; Metadaten- und Datenprofil separat anzeigen.

Hardware RAID unter ZFS meist vermeiden, weil ZFS direkte Disktransparenz und Fehlerdaten benötigt. HBA/JBOD bevorzugen.

## Wachstum und Verkleinerung

Vor jeder Größenänderung:

```bash
lsblk -f
findmnt
blockdev --getsize64 /dev/...
```

Reihenfolge beim Wachsen:

```text
Blockgerät/Partition/LV vergrößern → Dateisystem wachsen
```

Beim Shrink umgekehrt:

```text
Dateisystem verkleinern → darunterliegendes Volume/Partition verkleinern
```

Aber:

- XFS kann nicht schrumpfen.
- ext4-Shrink offline.
- Btrfs kann online resizen, aber freie Chunks/Balance beachten.
- ZFS-Pooltopologie hat eigene Regeln, kein generisches Partitions-Shrink-Modell.

> [!danger]
> Unterliegendes Blockgerät niemals zuerst verkleinern, wenn das Dateisystem die alten Blöcke noch adressiert.

## Mountoptionen

Anzeigen:

```bash
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS
cat /proc/mounts
```

Häufig:

| Option | Wirkung/Kommentar |
|---|---|
| `noatime` | keine klassischen Access-Time-Updates |
| `relatime` | reduzierte atime-Updates, oft Default |
| `nodev` | Device Nodes nicht interpretieren |
| `nosuid` | SUID/SGID nicht wirken lassen |
| `noexec` | direkte Ausführung blockieren; keine vollständige Sicherheitsgrenze |
| `discard` | kontinuierliches TRIM; oft periodisches `fstrim` bevorzugt |
| `ro` | read-only |
| `nofail` | Boot darf bei Fehlen fortfahren |
| `x-systemd.automount` | systemd-Automount |

`noexec` verhindert nicht, dass Interpreter eine lesbare Skriptdatei ausführt. Defense in Depth.

fstab prüfen:

```bash
findmnt --verify
sudo mount -a
```

Remote nicht mit einem Fehler in `/etc/fstab` rebooten.

## Quotas und Reservierungen

Varianten:

- Benutzer-/Gruppenquota
- Project Quota
- Dataset/Subvolume Quota
- ZFS `quota`, `refquota`, `reservation`, `refreservation`
- Btrfs qgroups
- XFS project quota
- ext4 usrquota/grpquota/project quota je Features

Quotas verhindern Poolvollstand nicht automatisch, wenn Snapshots, Metadaten oder andere Datasets Platz verbrauchen. Kapazitätsalarm separat.

## Diagnosewerkzeuge

Allgemein:

```bash
lsblk -f
findmnt
df -hT
df -ih
du -xhd1 /
stat -f /pfad
mount | column -t
```

Offene gelöschte Dateien:

```bash
sudo lsof +L1
```

I/O:

```bash
iostat -xz 1
vmstat 1
pidstat -d 1
```

Kernel:

```bash
journalctl -k -b | grep -Ei 'I/O error|filesystem|xfs|ext4|btrfs|zfs|nvme|ata'
```

Mount-/Prozessbezug:

```bash
sudo fuser -vm /mnt/daten
sudo lsof +f -- /mnt/daten
```

Inodes:

```bash
df -i
find /pfad -xdev -printf '%h\n' | sort | uniq -c | sort -nr | head
```

## Weitere Dateisysteme

| Dateisystem | Einsatz |
|---|---|
| FAT32 | Firmware/Wechselmedien, 4-GiB-Dateilimit |
| exFAT | große Dateien auf Wechselmedien, plattformübergreifend |
| NTFS | Windows-System/Datenträger, Linux-Treiber je Kernel |
| UFS/FFS | klassische BSD-Systeme |
| F2FS | Flash-orientiert, Android/Embedded/Linux |
| tmpfs | RAM/Swap-backed temporär |
| overlayfs | Container-/Overlay-Layer |
| NFS | Netzwerkdateisystem Unix/Linux |
| SMB | Windows-kompatible Netzwerkfreigaben |
| CephFS | verteiltes Scale-out-Dateisystem |
| GlusterFS | verteiltes Dateisystem, Produktstatus/Use Case prüfen |
| ISO9660/UDF | optische/immutable Medien |

Netzwerkdateisysteme erfordern zusätzliche Semantik für Locking, Cache, UID/GID, ACLs, Offlineverhalten und Split-Brain.

## Entscheidungscheckliste

```text
[ ] Einzelhost, NAS oder Cluster?
[ ] Datenintegrität/Checksummen erforderlich?
[ ] Native Snapshots/Replication?
[ ] Shrink jemals nötig?
[ ] viele kleine oder große Dateien?
[ ] Datenbank/VM/Container?
[ ] Kompression/Dedup?
[ ] OS-/Boot-/Recovery-Unterstützung?
[ ] RAIDtopologie und Ausfalltoleranz?
[ ] Backup/Restore-Ziel getestet?
[ ] Monitoring für Kapazität, Fehler und Scrubs?
[ ] Personal kann das Dateisystem sicher betreiben?
```

## Quellen
- [Linux Filesystems Documentation](https://docs.kernel.org/filesystems/)
- [OpenZFS Documentation](https://openzfs.github.io/openzfs-docs/)
- [XFS Documentation](https://docs.kernel.org/filesystems/xfs.html)
- [Btrfs Documentation](https://btrfs.readthedocs.io/)

## Verwandte Notizen
- [[ZFS – Premium-Spickzettel]]
- [[XFS – Premium-Spickzettel]]
- [[Btrfs – Premium-Spickzettel]]
- [[ext4 – Premium-Spickzettel]]
- [[Weitere Dateisysteme – Premium-Spickzettel]]
- [[TrueNAS – Premium-Spickzettel]]
