---
title: "XFS – Cheatsheet"
aliases: ["XFS Cheatsheet", "xfs_growfs xfs_repair", "XFS Administration"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [xfs, filesystem, linux, rhel, storage]
source: "https://docs.kernel.org/filesystems/xfs.html"
---

# XFS – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für XFS-Erstellung, Mounts, Wachstum, Reflinks, Quotas, xfsdump/xfsrestore, Scrub, Repair, Metadatenanalyse, Performance und sichere Recovery auf Fedora/RHEL/Linux.

> [!danger] XFS kann nicht schrumpfen
> Ein XFS-Dateisystem kann regulär wachsen, aber nicht verkleinert werden. Für kleinere Zielgröße Daten sichern, neues Dateisystem anlegen und wiederherstellen.

## Inhalt

- [[#Inventar und Features]]
- [[#Erstellen und Mounten]]
- [[#Wachsen]]
- [[#Reflinks und Kopien]]
- [[#Quotas]]
- [[#Backup mit xfsdump]]
- [[#Scrub und Reparatur]]
- [[#Performance und Mountoptionen]]
- [[#Metadaten und Diagnose]]
- [[#Recovery-Playbook]]

## Inventar und Features

```bash
lsblk -f
findmnt -t xfs
xfs_info /mountpoint
xfs_info /dev/mapper/vg-lv
```

Geometrie:

```text
meta-data, data, naming, log, realtime
```

Wichtige Features je Version:

- CRC/Metadata checksums
- reflink
- rmapbt
- bigtime
- inobtcount
- sparse inodes

Features sind bei Erstellung festgelegt und beeinflussen ältere Kernel/Tools. Toolversion:

```bash
xfs_db -V
xfs_repair -V
```

## Erstellen und Mounten

> [!danger]
> `mkfs.xfs` zerstört vorhandene Dateisystemsignaturen. Gerät über Seriennummer, Mounts und Backup verifizieren.

```bash
sudo mkfs.xfs /dev/mapper/vg-data
```

Label:

```bash
sudo mkfs.xfs -L DATA /dev/mapper/vg-data
```

Reflink ist auf modernen xfsprogs häufig Standard. Explizite Featurewahl nur nach Zielkompatibilität:

```bash
sudo mkfs.xfs -m reflink=1,crc=1 /dev/mapper/vg-data
```

Anzeigen:

```bash
sudo xfs_admin -l /dev/mapper/vg-data
sudo xfs_admin -u /dev/mapper/vg-data
```

Label ändern, unmounted bzw. nach Toolvorgabe:

```bash
sudo xfs_admin -L NEWLABEL /dev/mapper/vg-data
```

Mount:

```bash
sudo mount /dev/mapper/vg-data /srv/data
```

fstab per UUID:

```bash
blkid /dev/mapper/vg-data
```

```fstab
UUID=... /srv/data xfs defaults,noatime 0 0
```

XFS verwendet kein klassisches `fsck.xfs`; Bootfsck ist nicht wie ext4. `xfs_repair` gezielt offline.

## Wachsen

Unterliegendes LV zuerst:

```bash
sudo lvextend -L +100G /dev/vg/data
```

Dann gemountetes XFS wachsen:

```bash
sudo xfs_growfs /srv/data
```

Maximal verfügbaren Platz:

```bash
sudo xfs_growfs -d /srv/data
```

Nur Datenbereich auf Größe in Blöcken:

```bash
sudo xfs_growfs -D BLOCKS /srv/data
```

Prüfen:

```bash
xfs_info /srv/data
df -hT /srv/data
```

LVM kann beides kombinieren:

```bash
sudo lvextend -r -L +100G /dev/vg/data
```

Vor Automatik Sicherung und freien Extent-/Devicezustand prüfen.

## Reflinks und Kopien

Reflink-Kopie:

```bash
cp --reflink=always große-datei.img clone.img
```

Automatisch, mit normaler Kopie als Fallback:

```bash
cp --reflink=auto quelle ziel
```

Blockteilung prüfen, je Tools:

```bash
filefrag -v quelle ziel
```

Reflink ist kein Backup: beide Dateien liegen im selben Dateisystem/Fehlerbereich. Änderungen lösen COW für betroffene Bereiche aus.

Deduplizieren über `xfs_fsr`? `xfs_fsr` reorganisiert/defragmentiert, dedupliziert nicht allgemein. Externe `duperemove`/ioctl-Lösungen nur nach Tests.

## Quotas

Mountoptionen:

```text
uquota / usrquota
gquota / grpquota
pquota / prjquota
```

fstab:

```fstab
UUID=... /srv/data xfs defaults,pquota 0 0
```

Project Quota ist besonders für Verzeichnisse/Dienste geeignet.

Projekt definieren:

```text
# /etc/projects
100:/srv/data/team-a

# /etc/projid
team-a:100
```

Initialisieren:

```bash
sudo xfs_quota -x -c 'project -s team-a' /srv/data
```

Limit:

```bash
sudo xfs_quota -x -c 'limit -p bhard=500g bsoft=450g team-a' /srv/data
```

Report:

```bash
sudo xfs_quota -x -c 'report -h' /srv/data
sudo xfs_quota -x -c 'state' /srv/data
```

Inode Limits:

```bash
sudo xfs_quota -x -c 'limit -p ihard=1000000 team-a' /srv/data
```

## Backup mit xfsdump

Vollbackup:

```bash
sudo xfsdump -l 0 -L 'full-2026-07-17' -M 'backup-disk' \
  -f /backup/data-level0.xfsdump /srv/data
```

Inkrementell Level 1:

```bash
sudo xfsdump -l 1 -L 'inc-2026-07-18' \
  -f /backup/data-level1.xfsdump /srv/data
```

Inventar:

```bash
sudo xfsdump -I
```

Restore:

```bash
sudo xfsrestore -f /backup/data-level0.xfsdump /restore/data
sudo xfsrestore -f /backup/data-level1.xfsdump /restore/data
```

Testrestore durchführen. Dumpfiles schützen; ACLs/xattrs/Ownership werden je Optionen/Version unterstützt.

Dateibasierte Alternativen: rsync, Borg, Restic, Tar. Anwendungskonsistenz separat.

## Scrub und Reparatur

Online prüfen, falls `xfs_scrub` verfügbar:

```bash
sudo xfs_scrub /srv/data
```

Alle Mounts per Timer/Distribution:

```bash
systemctl list-timers | grep xfs
```

Dry Run Repair offline:

```bash
sudo umount /srv/data
sudo xfs_repair -n /dev/mapper/vg-data
```

Echte Reparatur:

```bash
sudo xfs_repair /dev/mapper/vg-data
```

> [!danger] `xfs_repair -L`
> `-L` setzt/zerstört das Log und kann aktuelle Metadatenänderungen verlieren. Nur wenn normales Mounten/Repair wegen beschädigtem Log nicht möglich ist und Backup/Recoveryplan besteht.

Vor Repair:

- Hardware-/I/O-Fehler beheben.
- Image/Backup erwägen.
- korrektes Gerät bestimmen.
- Dateisystem aushängen.
- Ausgabe sichern.

Bei sauberem, aber nicht replaytem Log kann ein Mount/Unmount auf funktionierender Hardware erforderlich sein; Recoverydoku der Version beachten.

## Performance und Mountoptionen

XFS skaliert gut bei parallelen I/O und großen Dateien. Keine universellen Tuningwerte.

Nützlich:

```bash
xfs_info /srv/data
iostat -xz 1
xfs_db -r -c sb -c p /dev/mapper/vg-data | less
```

Mountoptionen:

- `noatime` falls Access Times unnötig
- `inode64` auf modernen großen FS meist Default/geeignet
- `discard` versus periodisches `fstrim`
- `logbufs`, `logbsize` nur nach Messung
- `allocsize` kann Workload beeinflussen

TRIM:

```bash
systemctl status fstrim.timer
sudo fstrim -v /srv/data
```

Log separat bei Spezialdesign möglich, erhöht aber Komplexität und ist pool-/hardwarekritisch.

## Metadaten und Diagnose

Filesystemstatistik:

```bash
xfs_info /srv/data
xfs_spaceman -c 'freesp -s' /srv/data
```

Fragmentierung schätzen:

```bash
sudo xfs_db -r -c frag -c quit /dev/mapper/vg-data
```

Defragmentieren einzelner Datei:

```bash
sudo xfs_fsr /srv/data/grosse-datei
```

Ganzes Mount:

```bash
sudo xfs_fsr /srv/data
```

Nicht blind auf SSD/komplettem produktiven FS; I/O-Last messen.

Logs:

```bash
journalctl -k -b | grep -i xfs
```

Shutdown/Corruption-Meldungen ernst nehmen. XFS kann sich bei schweren Fehlern „shutdown“ setzen, um weiteren Schaden zu vermeiden.

Kapazität:

```bash
df -hT /srv/data
df -i /srv/data
sudo du -xhd1 /srv/data | sort -h
sudo lsof +L1
```

## Recovery-Playbook

1. Schreibzugriff stoppen.
2. Hardware-/Controller-/Kernelmeldungen sichern.
3. SMART/NVMe prüfen.
4. Backup/Blockimage erwägen.
5. `xfs_repair -n` offline.
6. Ausgabe bewerten.
7. normale Reparatur.
8. `-L` nur letzte dokumentierte Stufe.
9. Mount read-only/Test.
10. Daten/Anwendung validieren und aus Backup ergänzen.

```bash
sudo mount -o ro,norecovery /dev/mapper/vg-data /mnt/recovery
```

`norecovery` zeigt nur konsistent auf Disk vorhandenen Stand und setzt read-only voraus; nicht als normaler Betrieb.

## Quellen
- [XFS Documentation](https://docs.kernel.org/filesystems/xfs.html)
- [xfsprogs man pages](https://man7.org/linux/man-pages/man8/xfs_repair.8.html)
- [RHEL Managing XFS](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/managing_file_systems/)

## Verwandte Notizen
- [[Dateisysteme – Cheatsheet]]
- [[Fedora-RHEL – Cheatsheet]]
- [[fdisk – Cheatsheet]]
- [[rsync – Cheatsheet]]
