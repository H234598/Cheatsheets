---
title: "fdisk und Partitionierung – Premium-Spickzettel"
aliases: ["fdisk Cheatsheet", "Linux Partitionieren", "sfdisk", "fdisk – Premium-Spickzettel"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [fdisk, partitions, storage, linux, gpt, mbr]
source: "https://man7.org/linux/man-pages/man8/fdisk.8.html"
---

# fdisk und Partitionierung – Premium-Spickzettel

> [!abstract] Zweck
> Sichere Praxisreferenz für fdisk/sfdisk: Blockgeräte erkennen, GPT/MBR, Tabellen sichern, Partitionen anlegen/ändern, Kernel neu einlesen, Dateisysteme erweitern und Fehlerdiagnose.

> [!danger] Destruktives Werkzeug
> Ein falsches Gerät oder Schreibbefehl kann Partitionstabellen und Daten sofort unzugänglich machen. Vorher Backup, exakte Geräte-ID, Mounts, LVM/RAID/Verschlüsselung und Rettungsweg prüfen. Beispiele zuerst mit Loop-Devices oder Test-VM üben.

## Inhalt

- [[#Schichtenmodell]]
- [[#Gerät sicher identifizieren]]
- [[#Partitionstabellen]]
- [[#fdisk interaktiv]]
- [[#sfdisk sichern und automatisieren]]
- [[#Neue Partition formatieren und mounten]]
- [[#Partition und Dateisystem vergrößern]]
- [[#Löschen und Wiederherstellung]]
- [[#Diagnose]]

## Schichtenmodell

```text
Blockgerät /dev/sda oder /dev/nvme0n1
└── Partitionstabelle GPT/MBR
    ├── Partition /dev/sda1
    │   └── Dateisystem / LUKS / LVM PV / RAID Member
    └── Partition /dev/sda2
```

Partition vergrößern ist nicht dasselbe wie Dateisystem/LVM vergrößern.

## Gerät sicher identifizieren

```bash
lsblk -e7 -o NAME,PATH,SIZE,MODEL,SERIAL,TYPE,FSTYPE,FSVER,LABEL,UUID,MOUNTPOINTS
blkid
findmnt
sudo fdisk -l
```

Udev-ID:

```bash
ls -l /dev/disk/by-id/
udevadm info --query=all --name=/dev/sdX
```

> [!important]
> `/dev/sdX` kann sich zwischen Boots ändern. Für Dokumentation und Automatisierung stabile IDs/UUIDs verwenden. Trotzdem zeigt `fdisk` auf das konkrete Blockgerät.

Vor Schreibzugriff:

```bash
findmnt /dev/sdX1
swapon --show
sudo pvs
sudo mdadm --examine /dev/sdX* 2>/dev/null
sudo cryptsetup isLuks /dev/sdX1 && echo LUKS
```

## Partitionstabellen

| Typ | Eigenschaften |
|---|---|
| GPT | modern, viele Partitionen, redundante Header, große Datenträger, GUID-Typen |
| DOS/MBR | Legacy, vier primäre Einträge bzw. Extended, Größen-/Bootgrenzen |

Anzeigen:

```bash
sudo fdisk -l /dev/sdX
sudo fdisk -l -o Device,Start,End,Sectors,Size,Type /dev/sdX
```

GPT-Details alternativ:

```bash
sudo sgdisk -p /dev/sdX
sudo gdisk -l /dev/sdX
```

Tools können Zusatzpakete benötigen.

### Backup der Partitionstabelle

Mit sfdisk:

```bash
sudo sfdisk --dump /dev/sdX > sdX-partitions.sfdisk
sudo sfdisk --backup /dev/sdX
```

GPT zusätzlich:

```bash
sudo sgdisk --backup=sdX-gpt.bin /dev/sdX
```

Backup außerhalb des betroffenen Datenträgers speichern und Gerätekennung dokumentieren.

## fdisk interaktiv

Start:

```bash
sudo fdisk /dev/sdX
```

Wichtige Tasten:

| Taste | Aktion |
|---|---|
| `m` | Hilfe |
| `p` | Tabelle anzeigen |
| `g` | neue leere GPT-Tabelle |
| `o` | neue leere DOS/MBR-Tabelle |
| `n` | Partition anlegen |
| `d` | Partition löschen |
| `t` | Partitionstyp ändern |
| `l` | Typen listen |
| `v` | Tabelle prüfen |
| `i` | Partitionsdetails, je Version |
| `w` | schreiben und beenden |
| `q` | ohne Schreiben beenden |

> [!danger]
> `g` oder `o` erstellt eine neue leere Partitionstabelle. Nicht auf Datenträger mit benötigten Daten verwenden.

### Neue GPT-Partition – Ablauf im Lab

```text
p          aktuellen Zustand ansehen
n          neue Partition
<Enter>    Standardnummer
<Enter>    Standard erster Sektor, ausgerichtet
+20G       Größe
t          Typ setzen, falls nötig
p          Ergebnis prüfen
v          Konsistenz prüfen
w          erst jetzt schreiben
```

Partitionstyp beschreibt Zweck, formatiert aber nichts.

### Alignment

Moderne fdisk-Versionen wählen üblicherweise ausgerichtete Sektoren. Sektoreinheiten nicht unnötig manuell ändern. Prüfen:

```bash
sudo fdisk -l /dev/sdX
```

Startsektoren sollten sinnvoll ausgerichtet sein; 2048 ist häufig der erste Standardsektor bei 512-Byte-logischen Sektoren.

## sfdisk sichern und automatisieren

Dump:

```bash
sudo sfdisk --dump /dev/sdX
```

Wiederherstellung **nur auf richtigem Zielgerät**:

```bash
sudo sfdisk /dev/sdX < sdX-partitions.sfdisk
```

Neue Tabelle aus Datei:

```text
label: gpt
unit: sectors

/dev/sdX1 : start=2048, size=2097152, type=uefi-guid
/dev/sdX2 : start=2099200, size=41943040, type=linux-guid
```

Tatsächliche GUID-Aliase/Syntax mit `sfdisk --list-types` und Version prüfen.

Dry/No-act je Toolversion:

```bash
sfdisk --help
```

> [!warning]
> Automatisierung muss Modell, Seriennummer, Größe und leeren/erwarteten Zustand assertieren. Nie nur `/dev/sdb` annehmen.

Kernel neu einlesen:

```bash
sudo partprobe /dev/sdX
sudo partx -u /dev/sdX
udevadm settle
lsblk /dev/sdX
```

Bei belegten Partitionen kann Reboot nötig sein.

## Neue Partition formatieren und mounten

Beispiel XFS:

```bash
sudo mkfs.xfs -L DATA /dev/sdX1
```

Beispiel ext4:

```bash
sudo mkfs.ext4 -L DATA /dev/sdX1
```

> [!danger]
> `mkfs` zerstört vorhandene Dateisystemstrukturen. Gerät unmittelbar vorher mit `lsblk -f` und `wipefs -n` prüfen.

Signaturen nur anzeigen:

```bash
sudo wipefs -n /dev/sdX1
```

Mount:

```bash
sudo mkdir -p /srv/data
sudo mount /dev/disk/by-uuid/UUID /srv/data
findmnt /srv/data
```

`/etc/fstab` mit UUID:

```fstab
UUID=<uuid> /srv/data xfs defaults,nofail 0 0
```

Test:

```bash
sudo mount -a
findmnt --verify
```

`nofail` nur wenn Boot ohne Volume akzeptabel; Sicherheits-/Datenabhängigkeit beachten.

## Partition und Dateisystem vergrößern

Vorher:

- Backup/Snapshot
- Layout und freien nachfolgenden Platz prüfen
- Layer identifizieren: Partition → LUKS → PV → LV → FS
- Shrink/Expand-Fähigkeit des Dateisystems kennen

### Letzte Partition bis Datenträgerende

Mit `growpart`, wenn verfügbar:

```bash
sudo growpart /dev/sdX 2
```

Oder fdisk: Partition löschen und mit **identischem Startsektor**, größerem Endsektor neu anlegen. Das ändert bei korrektem Start nicht automatisch Daten, ist aber riskant und braucht Backup.

> [!danger]
> Startsektor darf sich nicht ändern. Bei LUKS/LVM/RAID und GPT-Backupheader weitere Schritte beachten.

Kernel neu einlesen:

```bash
sudo partprobe /dev/sdX
lsblk
```

Dann Layer:

LUKS, je Setup:

```bash
sudo cryptsetup resize mappername
```

LVM PV:

```bash
sudo pvresize /dev/sdX2
```

LV:

```bash
sudo lvextend -l +100%FREE /dev/vg/lv
```

Dateisystem:

```bash
sudo xfs_growfs /mountpoint
sudo resize2fs /dev/vg/lv
```

Btrfs:

```bash
sudo btrfs filesystem resize max /mountpoint
```

Reihenfolge und Befehle vom konkreten Stack abhängig.

## Löschen und Wiederherstellung

Partitionseintrag löschen entfernt nicht sofort jeden Datenblock, aber macht Zugriff schwieriger und Überschreiben wahrscheinlich. Bei Fehler:

1. sofort keine weiteren Schreibvorgänge
2. Datenträger read-only oder Image
3. ursprüngliche Start-/Endsektoren aus Backup/Logs
4. professionelle Recovery bei wichtigen Daten
5. Tools wie TestDisk nur auf Kopie und mit Kenntnis

Partition mit identischem Start/Ende wieder anlegen kann Zugriff wiederherstellen, ist aber nicht garantiert.

Signaturen löschen:

```bash
sudo wipefs -n /dev/sdX
sudo wipefs -a /dev/sdX
```

> [!danger]
> `wipefs -a` entfernt Signaturen. Es ist destruktiv und kein sicheres Datenlöschverfahren.

## Diagnose

### Kernel sieht neue Tabelle nicht

```bash
sudo partprobe /dev/sdX
sudo partx -u /dev/sdX
lsblk
journalctl -k -n 100
```

Partition in Benutzung? Reboot oder Offlinewartung.

### „Device or resource busy“

```bash
findmnt -S /dev/sdX1
swapon --show
sudo lsof /dev/sdX1
sudo fuser -vm /dev/sdX1
sudo pvs
```

Nicht mit Gewalt fortfahren.

### GPT-Warnung Backupheader

Datenträger wurde vergrößert/gekloont. Mit `sgdisk -v` prüfen und nach Backup ggf. Backupheader ans Ende verschieben:

```bash
sudo sgdisk -e /dev/sdX
```

Nur nach exakter Geräteprüfung.

### Universelle Vor-Schreib-Checkliste

```bash
lsblk -e7 -o NAME,PATH,SIZE,MODEL,SERIAL,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINTS
sudo fdisk -l /dev/sdX
sudo sfdisk --dump /dev/sdX > backup.sfdisk
findmnt
swapon --show
sudo pvs; sudo vgs; sudo lvs
```

Dann `fdisk`, mehrfach `p`, und nur bei eindeutig korrektem Ergebnis `w`.

## Quellen
- [fdisk Manual](https://man7.org/linux/man-pages/man8/fdisk.8.html)
- [sfdisk Manual](https://man7.org/linux/man-pages/man8/sfdisk.8.html)
- [lsblk Manual](https://man7.org/linux/man-pages/man8/lsblk.8.html)

## Verwandte Notizen
- [[Dateisysteme-Premium-Spickzettel]]
- [[ls-und-Hardware-Tools-Premium-Spickzettel]]
- [[File-Compression-Linux-Premium-Spickzettel]]
