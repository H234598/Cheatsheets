---
title: "ext4 – Cheatsheet"
aliases: ["ext4 Cheatsheet", "e2fsck resize2fs tune2fs", "Extended Filesystem"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [ext4, filesystem, linux, e2fsck, storage]
source: "https://docs.kernel.org/filesystems/ext4/"
---

# ext4 – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für ext4-Erstellung, Features, Mounts, Journaling, Wachstum/Shrink, tune2fs, Quotas, e2fsck, Debugfs, Backup und sichere Recovery.

> [!danger] e2fsck nur passend zum Zustand
> Ein beschreibbar gemountetes ext4-Dateisystem nicht mit `e2fsck` reparieren. Für Root ein Rescue-/Recovery-System oder Bootfsck verwenden. Vor Shrink und Reparatur Backup sowie Hardwarezustand prüfen.

## Inhalt

- [[#Inventar]]
- [[#Erstellen]]
- [[#Mounten und Optionen]]
- [[#Wachsen und Schrumpfen]]
- [[#tune2fs und Features]]
- [[#Journaling]]
- [[#Quotas]]
- [[#Prüfen und Reparieren]]
- [[#Backup und Metadaten]]
- [[#Diagnose und Recovery]]

## Inventar

```bash
lsblk -f
findmnt -t ext4
sudo tune2fs -l /dev/mapper/vg-data | less
sudo dumpe2fs -h /dev/mapper/vg-data
```

UUID/Label:

```bash
blkid /dev/mapper/vg-data
sudo e2label /dev/mapper/vg-data
```

Nutzung:

```bash
df -hT /srv/data
df -i /srv/data
```

## Erstellen

> [!danger]
> `mkfs.ext4` überschreibt vorhandene Dateisystemstrukturen.

```bash
sudo mkfs.ext4 /dev/mapper/vg-data
```

Label:

```bash
sudo mkfs.ext4 -L DATA /dev/mapper/vg-data
```

Reserved Blocks für großen reinen Datenträger reduzieren, nicht Root blind:

```bash
sudo mkfs.ext4 -m 1 -L DATA /dev/mapper/vg-data
```

Blockgröße/Inodeverhältnis nur bei bekanntem Workload:

```bash
sudo mkfs.ext4 -b 4096 -i 16384 /dev/mapper/vg-data
```

Viele kleine Dateien benötigen genug Inodes. Inodeanzahl ist nach Erstellung nicht beliebig erweiterbar.

Features anzeigen:

```bash
sudo tune2fs -l /dev/mapper/vg-data | grep 'Filesystem features'
```

## Mounten und Optionen

```bash
sudo mount /dev/mapper/vg-data /srv/data
```

fstab:

```fstab
UUID=... /srv/data ext4 defaults,noatime 0 2
```

Letztes Feld steuert fsck-Reihenfolge traditionell:

- Root `1`
- weitere lokale FS `2`
- `0` nicht automatisch prüfen

Optionen:

| Option | Hinweis |
|---|---|
| `relatime` | meist Default, reduzierte atime |
| `noatime` | keine Access-Time Updates |
| `errors=remount-ro` | bei Fehler read-only, häufig Root |
| `discard` | kontinuierliches TRIM; periodisches fstrim oft besser |
| `data=ordered` | üblicher Journalmodus |
| `data=journal` | Daten und Metadaten journaled, langsam |
| `data=writeback` | schwächere Reihenfolgegarantien |
| `commit=N` | Journalcommitintervall; Haltbarkeit/Performance |

Keine Journal-/Barrier-/Commit-Tuningwerte ohne Stromausfall- und Anwendungskonsistenzanalyse.

## Wachsen und Schrumpfen

### Wachsen

Blockgerät/LV zuerst:

```bash
sudo lvextend -L +100G /dev/vg/data
```

Dateisystem online wachsen:

```bash
sudo resize2fs /dev/vg/data
```

LVM kombiniert:

```bash
sudo lvextend -r -L +100G /dev/vg/data
```

### Schrumpfen

Nur offline:

```bash
sudo umount /srv/data
sudo e2fsck -f /dev/vg/data
sudo resize2fs /dev/vg/data 500G
sudo lvreduce -L 500G /dev/vg/data
```

> [!danger]
> Zielgröße mit Sicherheitsmarge und Einheiten prüfen. Erst Dateisystem, dann LV/Partition. `lvreduce --resizefs` kann automatisieren, ersetzt aber kein Backup.

Minimalgröße schätzen:

```bash
sudo resize2fs -P /dev/vg/data
```

Blockgröße beachten, nicht Wert direkt als Bytes interpretieren.

Nach Shrink:

```bash
sudo e2fsck -f /dev/vg/data
sudo mount /srv/data
```

## tune2fs und Features

Label:

```bash
sudo tune2fs -L DATA /dev/vg/data
```

UUID neu – kann fstab/Boot brechen:

```bash
sudo tune2fs -U random /dev/vg/data
```

Reserved Blocks:

```bash
sudo tune2fs -m 1 /dev/vg/data
```

Prüfintervall/Count, moderne Distributionen nutzen oft andere Strategien:

```bash
sudo tune2fs -c 30 -i 6m /dev/vg/data
sudo tune2fs -c 0 -i 0 /dev/vg/data
```

Nicht ohne Monitoring deaktivieren.

Feature aktivieren:

```bash
sudo tune2fs -O FEATURE /dev/vg/data
```

Danach oft `e2fsck -f`. Features können ältere Kernel/Bootloader/Tools inkompatibel machen. Dokumentation lesen.

## Journaling

Journalstatus:

```bash
sudo tune2fs -l /dev/vg/data | grep -i journal
```

Externes Journal ist Spezialdesign und kann zusätzlichen Single Point of Failure erzeugen.

Journal entfernen/hinzufügen ist datenkritisch:

```bash
sudo tune2fs -O ^has_journal /dev/vg/data
sudo tune2fs -j /dev/vg/data
```

Nicht im normalen Betrieb ändern.

Journaling schützt primär Dateisystemkonsistenz nach Crash, nicht automatisch letzte Anwendungsdaten. Anwendungen müssen `fsync`/Transaktionen korrekt verwenden.

## Quotas

Mountoptionen/Features je Distribution:

```text
usrquota,grpquota,prjquota
```

Aktivieren klassisch:

```bash
sudo tune2fs -O quota /dev/vg/data
sudo e2fsck -f /dev/vg/data
```

fstab entsprechend. Danach:

```bash
sudo quotaon -av
sudo repquota -a
sudo edquota -u alice
sudo setquota -u alice 100G 110G 0 0 /srv/data
```

Project Quota ist versions-/Featureabhängig; xfs-Projektquotas sind in Enterpriseumgebungen oft direkter, aber ext4 unterstützt Projektquota modern ebenfalls.

## Prüfen und Reparieren

Unmounted:

```bash
sudo e2fsck -f /dev/vg/data
```

Nur prüfen, keine Änderungen:

```bash
sudo e2fsck -fn /dev/vg/data
```

Automatisch sichere Korrekturen:

```bash
sudo e2fsck -p /dev/vg/data
```

Alle Fragen ja – nur mit Backup/Plan:

```bash
sudo e2fsck -y /dev/vg/data
```

Alternative Superblocks anzeigen:

```bash
sudo mke2fs -n /dev/vg/data
```

Mit Backup-Superblock:

```bash
sudo e2fsck -b 32768 /dev/vg/data
```

`mke2fs -n` mit gleichen Geometrieoptionen verwenden und **nicht** ohne `-n` auf dem beschädigten FS ausführen.

Badblocks-Scan:

```bash
sudo e2fsck -c /dev/vg/data
sudo e2fsck -cc /dev/vg/data
```

Sehr langsam; bei modernen Disks ersetzt dies keine SMART-/Hardwarediagnose. Wiederkehrende Bad Blocks → Gerät ersetzen.

## Backup und Metadaten

Metadatenimage für Entwickler/Recovery:

```bash
sudo e2image -rap /dev/vg/data metadata.e2i
```

Kann sensible Metadaten/Dateinamen enthalten.

Dateibackup:

```bash
sudo rsync -aHAX --numeric-ids /srv/data/ /backup/data/
```

Image:

```bash
sudo ddrescue -f -n /dev/problem /dev/backup problem.map
```

Bei defekter Hardware zuerst schonende Imagingstrategie, nicht wiederholte aggressive fsck-Läufe.

## Diagnose und Recovery

Kernel:

```bash
journalctl -k -b | grep -Ei 'EXT4-fs|I/O error|buffer error'
```

Mountstatus:

```bash
findmnt /srv/data
sudo tune2fs -l /dev/vg/data | grep -E 'Filesystem state|Errors behavior|Last checked'
```

Read-only:

```bash
sudo mount -o ro,noload /dev/vg/data /mnt/recovery
```

`noload` überspringt Journalreplay und kann inkonsistenten Stand zeigen; nur Recovery.

Debugfs, read-only bevorzugt:

```bash
sudo debugfs -R 'stats' /dev/vg/data
sudo debugfs -R 'ls -l /' /dev/vg/data
```

Recovery-Reihenfolge:

1. Schreiblast stoppen.
2. Hardwarelogs/SMART.
3. Backup/Image.
4. unmount/read-only.
5. `e2fsck -fn`.
6. Reparaturlauf.
7. Lost+found und Anwendung prüfen.
8. Daten aus Backup ergänzen.
9. Ursache beheben/Datenträger ersetzen.

## Quellen
- [ext4 Kernel Documentation](https://docs.kernel.org/filesystems/ext4/)
- [e2fsprogs Documentation](https://e2fsprogs.sourceforge.net/)
- [e2fsck man page](https://man7.org/linux/man-pages/man8/e2fsck.8.html)

## Verwandte Notizen
- [[Dateisysteme – Cheatsheet]]
- [[fdisk – Cheatsheet]]
- [[rsync – Cheatsheet]]
- [[POSIX-ACL – Cheatsheet]]
