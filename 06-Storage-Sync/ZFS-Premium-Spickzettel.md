---
title: "ZFS – Premium-Spickzettel"
aliases: ["OpenZFS Cheatsheet", "zpool zfs", "ZFS Administration"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [zfs, openzfs, storage, snapshots, raid, backup]
source: "https://openzfs.github.io/openzfs-docs/"
---

# ZFS – Premium-Spickzettel

> [!abstract] Zweck
> Sehr ausführliche OpenZFS-Referenz für Pools, vdevs, Datasets, Properties, Snapshots, Clones, Send/Receive, Scrubs, Replace/Resilver, Quotas, Verschlüsselung, ARC, Performance, Recovery und sichere Betriebsregeln.

> [!danger] Topologie ist dauerhaft prägend
> Vor `zpool create` vdev-Aufbau, Redundanz, Ashift, Erweiterung und Ersatzstrategie planen. Ein falsch gewählter vdev-Typ lässt sich nicht wie ein gewöhnliches Verzeichnis später beliebig umformen. Alle Gerätenamen mit `/dev/disk/by-id` und Seriennummern prüfen.

## Inhalt

- [[#Grundmodell]]
- [[#Inventar und Status]]
- [[#Pool erstellen und importieren]]
- [[#vdev-Topologien]]
- [[#Datasets und Properties]]
- [[#Snapshots, Rollback und Clones]]
- [[#Send und Receive]]
- [[#Scrub, Resilver und Fehler]]
- [[#Gerät ersetzen und erweitern]]
- [[#Quotas und Reservierungen]]
- [[#Kompression, Recordsize und Sync]]
- [[#Verschlüsselung]]
- [[#ARC, L2ARC, SLOG und Special vdev]]
- [[#Kapazität und Fragmentierung]]
- [[#Pool-Features und Upgrades]]
- [[#Recovery und Diagnose]]
- [[#Schnellreferenz]]

## Grundmodell

```text
Pool
├── top-level vdev 1 (Mirror/RAIDZ/Single)
├── top-level vdev 2
├── special/cache/log/spare vdevs
└── Datasets
    ├── Filesystems
    ├── Volumes (zvols)
    └── Snapshots/Clones
```

- Daten werden über top-level data vdevs verteilt.
- Fällt ein nicht redundanter top-level vdev endgültig aus, kann der gesamte Pool verloren sein.
- Datasets teilen Poolkapazität, besitzen aber eigene Properties.
- Checksummen erkennen Korruption; Redundanz ermöglicht Reparatur.

## Inventar und Status

```bash
zpool list
zpool status -v
zpool get all pool
zfs list
zfs list -t all
zfs get all pool/dataset
```

I/O live:

```bash
zpool iostat -v 1
zpool iostat -vy 1
```

Historie:

```bash
zpool history
zpool history -il pool
```

Events:

```bash
zpool events -v
```

Kapazität:

```bash
zfs list -o name,used,avail,refer,mountpoint
zfs list -o space
```

Snapshots:

```bash
zfs list -t snapshot -o name,used,refer,creation
```

## Pool erstellen und importieren

Geräte eindeutig:

```bash
ls -l /dev/disk/by-id/
lsblk -d -o NAME,MODEL,SERIAL,SIZE
```

Mirror:

```bash
sudo zpool create -o ashift=12 tank \
  mirror \
  /dev/disk/by-id/wwn-DISK1 \
  /dev/disk/by-id/wwn-DISK2
```

RAIDZ2:

```bash
sudo zpool create -o ashift=12 tank raidz2 \
  /dev/disk/by-id/wwn-DISK1 \
  /dev/disk/by-id/wwn-DISK2 \
  /dev/disk/by-id/wwn-DISK3 \
  /dev/disk/by-id/wwn-DISK4 \
  /dev/disk/by-id/wwn-DISK5 \
  /dev/disk/by-id/wwn-DISK6
```

Pool mountroot:

```bash
sudo zpool create -o ashift=12 -O mountpoint=/srv/tank tank mirror ...
```

> [!warning] `ashift`
> `ashift=12` entspricht 4-KiB-Sektoren und ist ein häufiger sicherer Wert. Größere physische/optimale Blockgrößen oder spezielle Geräte können anderes erfordern. Ashift lässt sich pro vdev nicht einfach nachträglich verkleinern.

Import finden:

```bash
zpool import
sudo zpool import tank
sudo zpool import -d /dev/disk/by-id tank
```

Read-only für Diagnose:

```bash
sudo zpool import -o readonly=on tank
```

Alternativer Root:

```bash
sudo zpool import -R /mnt/recovery tank
```

Export:

```bash
sudo zpool export tank
```

Nicht einfach Disks abziehen, bevor Pool exportiert/sauber heruntergefahren ist.

## vdev-Topologien

### Mirror

- IOPS skalieren mit Mirrors.
- Resilver liest meist nur belegte Blöcke.
- einfache Erweiterung durch weitere Mirror-vdevs.
- 2-way Mirror toleriert typischerweise einen Ausfall je Mirror.

### RAIDZ1/2/3

- Parität über vdev-Breite.
- Kapazität effizienter als Mirrors.
- Random IOPS ungefähr pro vdev, nicht pro Disk.
- breite vdevs und große Disks verlängern Rekonstruktion.
- RAIDZ2 häufig vernünftige Basis für größere Arrays.

### Stripe/Single Disk

Keine Redundanz. Für Wegwerfdaten/Lab möglich; ein Ausfall gefährdet Pool.

### dRAID

Für große Arrays/Spare-Optimierung; komplexer. Nur nach genauer OpenZFS-/Plattformplanung.

> [!important]
> ZFS-Redundanz schützt nicht vor Controller-/Backplane-/Netzteil-/Standortausfall. Backup auf separatem System.

## Datasets und Properties

Erstellen:

```bash
sudo zfs create tank/data
sudo zfs create tank/data/projects
sudo zfs create -o mountpoint=/srv/backups tank/backups
```

Properties:

```bash
zfs get compression,recordsize,atime,mountpoint tank/data
sudo zfs set compression=zstd tank/data
sudo zfs set atime=off tank/data
sudo zfs set recordsize=1M tank/data/media
```

Vererbung:

```bash
zfs inherit compression tank/data/projects
zfs get -s local,inherited compression tank/data/projects
```

Mount:

```bash
zfs mount
zfs mount tank/data
zfs unmount tank/data
```

Zvol:

```bash
sudo zfs create -V 100G -o volblocksize=16K tank/vm/disk01
```

`volblocksize` vor Befüllung/Workload passend wählen; Änderung bestehender Daten ist nicht trivial.

Nützliche Properties:

| Property | Zweck |
|---|---|
| `compression` | transparente Kompression |
| `recordsize` | max. Record für Filesystem |
| `volblocksize` | Blockgröße zvol |
| `atime` | Zugriffszeitupdates |
| `xattr` | Extended Attributes |
| `acltype`/`aclinherit` | ACL-Semantik |
| `sync` | Sync-Write-Behandlung |
| `primarycache` | ARC-Inhalt |
| `mountpoint` | Mountpfad |
| `canmount` | Mountsteuerung |
| `readonly` | Schreibschutz |

## Snapshots, Rollback und Clones

Snapshot:

```bash
sudo zfs snapshot tank/data@vor-update
sudo zfs snapshot -r tank/data@daily-2026-07-17
```

Liste:

```bash
zfs list -t snapshot
```

Datei aus `.zfs/snapshot` lesen, falls sichtbar:

```bash
ls /srv/data/.zfs/snapshot/vor-update/
```

Sichtbarkeit:

```bash
zfs get snapdir tank/data
sudo zfs set snapdir=visible tank/data
```

Rollback:

```bash
sudo zfs rollback tank/data@vor-update
```

Neuere Snapshots können blockieren; `-r`/`-R` zerstört zusätzliche Abhängigkeiten. Vorher `zfs list -t snapshot,clone`.

Clone:

```bash
sudo zfs clone tank/data@vor-update tank/testclone
```

Promote:

```bash
sudo zfs promote tank/testclone
```

Snapshot löschen:

```bash
sudo zfs destroy tank/data@vor-update
```

Holds:

```bash
sudo zfs hold keep tank/data@important
zfs holds tank/data@important
sudo zfs release keep tank/data@important
```

Snapshots belegen Platz, sobald Live-Daten abweichen. `usedbysnapshots` beobachten.

## Send und Receive

Voll:

```bash
sudo zfs send tank/data@snap1 | sudo zfs receive backup/data
```

Über SSH:

```bash
sudo zfs send tank/data@snap1 |
  ssh backup sudo zfs receive -u backup/tank-data
```

Inkrementell:

```bash
sudo zfs send -i tank/data@snap1 tank/data@snap2 |
  ssh backup sudo zfs receive -u backup/tank-data
```

Rekursiv/Properties:

```bash
sudo zfs send -R tank/data@snap2 |
  ssh backup sudo zfs receive -uF backup/data
```

> [!danger] `zfs receive -F`
> `-F` kann Zieländerungen und neuere Snapshots zurückrollen/zerstören, damit Streambasis passt. Ziel vorher inventarisieren und Backup/Retentiondesign verstehen.

Resume Token:

```bash
zfs get receive_resume_token backup/data
zfs send -t TOKEN | ssh backup zfs receive -s backup/data
```

Größe schätzen:

```bash
zfs send -nPv tank/data@snap1
zfs send -nPv -i tank/data@snap1 tank/data@snap2
```

Raw encrypted send:

```bash
zfs send -w tank/secure@snap | zfs receive backup/secure
```

Feature-/Verschlüsselungskompatibilität prüfen.

## Scrub, Resilver und Fehler

Scrub starten:

```bash
sudo zpool scrub tank
```

Status:

```bash
zpool status tank
```

Pausieren/fortsetzen je Version:

```bash
sudo zpool scrub -p tank
sudo zpool scrub tank
```

Abbrechen:

```bash
sudo zpool scrub -s tank
```

Scrubplan:

- regelmäßig, abhängig von Medien/Workload
- nicht alle großen Pools gleichzeitig
- Ergebnis überwachen, nicht nur Job starten
- SMART und Controllerlogs ergänzen

Fehlerzähler:

```text
READ WRITE CKSUM
```

- `CKSUM` kann durch Redundanz korrigierte Korruption anzeigen.
- Wiederkehrende Fehler → Kabel, HBA, RAM, Backplane, Disk, Stromversorgung untersuchen.

Zähler nur nach Behebung löschen:

```bash
sudo zpool clear tank
```

> [!warning]
> `zpool clear` repariert keine Ursache; es setzt Status/Zähler zurück. Vorher Ereignisse dokumentieren.

## Gerät ersetzen und erweitern

Status mit vollen Pfaden:

```bash
zpool status -P tank
```

Offline:

```bash
sudo zpool offline tank /dev/disk/by-id/OLD
```

Replace:

```bash
sudo zpool replace tank \
  /dev/disk/by-id/OLD \
  /dev/disk/by-id/NEW
```

Resilver beobachten:

```bash
watch -n 10 zpool status tank
zpool iostat -v 5
```

Online:

```bash
sudo zpool online tank /dev/disk/by-id/NEW
```

Größere Ersatzdisks nutzen:

```bash
sudo zpool set autoexpand=on tank
sudo zpool online -e tank /dev/disk/by-id/NEW
```

Bei Mirror erst alle Komponenten auf größere Geräte ersetzen, dann expandieren.

Top-level vdev hinzufügen:

```bash
sudo zpool add tank mirror DISK3 DISK4
```

> [!danger]
> `zpool add` ist nicht „Disk als Ersatz hinzufügen“, sondern erweitert den Pool um einen neuen top-level vdev. Ein versehentliches Single-Disk-vdev kann die Redundanz des gesamten Pools schwächen. `zpool add -n` zur Vorschau verwenden.

```bash
sudo zpool add -n tank mirror DISK3 DISK4
```

## Quotas und Reservierungen

Dataset-Quota:

```bash
sudo zfs set quota=500G tank/data
sudo zfs set refquota=400G tank/data
```

Reservation:

```bash
sudo zfs set reservation=100G tank/data
sudo zfs set refreservation=50G tank/data
```

Unterschied:

- `quota`: Dataset plus Nachkommen/Snapshots je Semantik.
- `refquota`: referenzierter Live-Speicher des Datasets.
- Reservation bindet Poolkapazität.

User-/Groupquota:

```bash
zfs userspace tank/data
sudo zfs set userquota@alice=100G tank/data
sudo zfs set groupquota@team=500G tank/data
```

## Kompression, Recordsize und Sync

Kompression:

```bash
sudo zfs set compression=zstd tank/data
zfs get compressratio tank/data
```

Kompression gilt nur für neu geschriebene Blöcke. Häufig positiv, da weniger I/O.

Recordsize:

- allgemeine Dateien: Default oft gut
- große sequentielle Medien: `1M` kann sinnvoll sein
- Datenbanken/VMs: Workload-/Blockgröße abstimmen
- Änderung wirkt auf neue Schreibvorgänge

```bash
sudo zfs set recordsize=16K tank/db
```

`sync`:

```bash
zfs get sync tank/data
```

- `standard`: Anwendung entscheidet mit fsync/O_SYNC.
- `always`: alles als synchron behandeln, langsamer.
- `disabled`: bestätigt Syncwrites ohne stabile Ablage → Datenverlust bei Crash möglich.

> [!danger]
> `sync=disabled` nicht als Performance-Tipp für produktive Datenbanken/VMs verwenden. Es bricht Haltbarkeitszusagen der Anwendung.

Dedup:

```bash
zfs get dedup tank/data
```

Dedup benötigt große DDT/RAM-/I/O-Ressourcen und ist schwer rückgängig zu machen (Daten müssen neu geschrieben werden). Standard: aus, außer nach Messung und Design.

## Verschlüsselung

Dataset nativ verschlüsselt:

```bash
sudo zfs create \
  -o encryption=aes-256-gcm \
  -o keyformat=passphrase \
  -o keylocation=prompt \
  tank/secure
```

Status:

```bash
zfs get encryption,keyformat,keylocation,keystatus tank/secure
```

Key laden/unladen:

```bash
sudo zfs load-key tank/secure
sudo zfs mount tank/secure
sudo zfs unmount tank/secure
sudo zfs unload-key tank/secure
```

Key ändern:

```bash
sudo zfs change-key tank/secure
```

Verschlüsselung schützt ruhende Daten, nicht kompromittierten laufenden Host. Pool-/Datasetnamen, Größen und manche Metadaten bleiben sichtbar. Schlüsselbackup und Recovery testen.

## ARC, L2ARC, SLOG und Special vdev

### ARC

RAM-Cache. Hohe RAM-Nutzung ist normal, solange reclaimbar. Prüfen je OS:

```bash
arc_summary
arcstat 1
```

ARC-Limits nur nach Messung/Plattformempfehlung tunen.

### L2ARC

Sekundärer Read Cache auf SSD:

- hilft nur bei wiederholten Reads, die ARC nicht hält
- benötigt RAM-Metadaten und erzeugt Schreiblast
- kein Write Cache
- nicht Ersatz für RAM

### SLOG

Separates Log vdev für **synchrone** Writes, nicht allgemeiner Write Cache.

Anforderungen:

- geringe Latenz
- Power-Loss Protection
- ausreichende Endurance
- bei kritischen Daten gespiegelt

SLOG verbessert keine asynchronen Writes und kann mit ungeeignetem Consumer-SSD riskant/langsam sein.

### Special vdev

Kann Metadaten/kleine Blöcke aufnehmen. Verlust eines nicht redundanten Special vdev kann Poolverlust bedeuten. Redundanz mindestens wie Daten-vdevs und Kapazität sorgfältig planen.

## Kapazität und Fragmentierung

```bash
zpool list
zfs list -o space
```

Pool nicht bis an 100 % füllen. COW-Dateisysteme brauchen freien Raum; Performance und Recovery leiden bei hoher Belegung.

Ursachen scheinbar „fehlenden“ Platzes:

- Snapshots
- Reservations
- Metadaten
- Slop Space
- gelöschte, aber offene Dateien
- Child Datasets
- zvols/refreservations

```bash
zfs list -o name,used,usedbysnapshots,usedbydataset,usedbychildren,usedbyrefreservation
```

Fragmentation in `zpool list` ist ein Indikator, nicht alleinige Performanceerklärung.

## Pool-Features und Upgrades

Status:

```bash
zpool get all tank | grep feature@
zpool upgrade
```

Upgrade:

```bash
sudo zpool upgrade tank
```

> [!danger]
> Feature-Upgrades können Import auf älteren Systemen/Recoverymedien unmöglich machen. Erst nach Upgrade von Betriebssystem, Bootumgebung, Replikationsziel und Notfallmedien durchführen.

## Recovery und Diagnose

Basis:

```bash
zpool status -v
zpool events -v
zpool history -il
zpool iostat -v 1
journalctl -k -b | grep -Ei 'zfs|I/O error|nvme|ata|scsi'
```

Importprobleme:

```bash
zpool import
zpool import -d /dev/disk/by-id
zpool import -o readonly=on -R /mnt/recovery tank
```

Rewind-Vorschau:

```bash
zpool import -F -n tank
```

`-F` ohne `-n` kann Transaktionen verwerfen. Nur mit Backup/Expertenplan.

Fehlerhafte Dateien:

```bash
zpool status -v tank
```

Wenn permanente Fehler Dateipfade anzeigen, aus Backup wiederherstellen und Hardwareursache beheben.

Nicht vorschnell:

- `zpool destroy`
- `labelclear`
- `zdb`-Schreiboperationen/Undokumentiertes
- Force-Import auf zwei Hosts
- Geräte neu partitionieren

Pool niemals gleichzeitig auf zwei nicht geclusterten Hosts importieren.

## Schnellreferenz

```bash
zpool list
zpool status -v
zpool iostat -v 1
zfs list -t all
zfs get all pool/dataset
zfs snapshot pool/data@snap
zfs send pool/data@snap | ssh host zfs receive backup/data
zpool scrub pool
zpool replace pool OLD NEW
zpool history -il
zpool events -v
```

## Quellen
- [OpenZFS Documentation](https://openzfs.github.io/openzfs-docs/)
- [OpenZFS Man Pages](https://openzfs.github.io/openzfs-docs/man/master/8/index.html)
- [ZFS Administration Guide](https://openzfs.github.io/openzfs-docs/Project%20and%20Community/FAQ.html)

## Verwandte Notizen
- [[Dateisysteme – Premium-Spickzettel]]
- [[TrueNAS – Premium-Spickzettel]]
- [[rsync – Premium-Spickzettel]]
- [[rclone – Premium-Spickzettel]]
