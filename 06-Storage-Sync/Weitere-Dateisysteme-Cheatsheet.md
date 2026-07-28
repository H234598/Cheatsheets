---
title: "Weitere Dateisysteme – Cheatsheet"
aliases: ["FAT exFAT NTFS UFS F2FS tmpfs OverlayFS", "Filesysteme etc.", "Andere Dateisysteme"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [filesystem, fat32, exfat, ntfs, ufs, f2fs, tmpfs, overlayfs]
source: "https://docs.kernel.org/filesystems/"
---

# Weitere Dateisysteme – Cheatsheet

> [!abstract] Zweck
> Kompakte, aber ausführliche Ergänzung zu FAT32, exFAT, NTFS, UFS/FFS, F2FS, tmpfs, OverlayFS, NFS, SMB, CephFS und optischen Dateisystemen – Einsatz, Werkzeuge, Grenzen und Diagnose.

## Inhalt

- [[#FAT32]]
- [[#exFAT]]
- [[#NTFS]]
- [[#UFS und FFS]]
- [[#F2FS]]
- [[#tmpfs]]
- [[#OverlayFS]]
- [[#NFS]]
- [[#SMB/CIFS]]
- [[#CephFS und verteilte Dateisysteme]]
- [[#ISO9660 und UDF]]
- [[#Auswahlmatrix]]

## FAT32

Einsatz:

- UEFI-Systempartition
- Kameras/Embedded
- maximale Kompatibilität

Grenzen:

- einzelne Datei maximal knapp 4 GiB
- keine Unix-ACLs/Ownership
- kein Journaling
- kurze/alte Semantik neben VFAT-LFN

Erstellen:

```bash
sudo mkfs.fat -F 32 -n USB /dev/sdX1
```

Prüfen:

```bash
sudo fsck.fat -n /dev/sdX1
sudo fsck.fat -a /dev/sdX1
```

Mount mit festen Rechten:

```bash
sudo mount -t vfat -o uid=1000,gid=1000,umask=022 /dev/sdX1 /mnt/usb
```

FAT speichert keine echten Unix-Besitzer; Mountoptionen simulieren sie.

## exFAT

Für große Dateien auf Wechselmedien zwischen Windows/macOS/Linux.

```bash
sudo mkfs.exfat -n MEDIA /dev/sdX1
sudo fsck.exfat /dev/sdX1
sudo mount -t exfat /dev/sdX1 /mnt/media
```

Keine Unix-ACLs/Journaling wie lokale Serverdateisysteme. Sicher auswerfen, besonders bei Flashmedien.

## NTFS

Linux nutzt moderne Kernel-/Userspace-Treiber je Distribution (`ntfs3`, historisch `ntfs-3g`).

```bash
lsblk -f
sudo mount -t ntfs3 /dev/sdX1 /mnt/windows
```

Windows Fast Startup/Hibernation kann Volume „dirty/hibernated“ hinterlassen. Nicht schreibend mounten und Windows sauber herunterfahren:

```bash
sudo mount -t ntfs3 -o ro /dev/sdX1 /mnt/windows
```

Linux-Tools:

```bash
ntfsfix /dev/sdX1
```

`ntfsfix` ersetzt **nicht** Windows `chkdsk`; es behebt begrenzte Probleme/markiert Prüfung.

Windows:

```cmd
chkdsk X: /scan
chkdsk X: /f
```

NTFS-ACLs und Linux-UID/GID-Mapping sorgfältig planen; für produktive Linux-Server meist natives Dateisystem bevorzugen.

## UFS und FFS

Klassische BSD-Dateisystemfamilie.

FreeBSD UFS2:

```sh
newfs -U /dev/ada1p2
mount -t ufs /dev/ada1p2 /data
fsck -y /dev/ada1p2
```

Soft Updates/Journalingoptionen sind FreeBSD-spezifisch. OpenBSD FFS2 hat eigene `newfs`, `fsck`, `tunefs`-Semantik.

Keine Befehle zwischen BSDs blind übertragen. Lokale Manpages:

```sh
man newfs
man tunefs
man fsck_ffs
```

## F2FS

Flash-Friendly File System für NAND/Flash-orientierte Workloads, u. a. Android/Linux.

```bash
sudo mkfs.f2fs -l DATA /dev/sdX1
sudo fsck.f2fs /dev/sdX1
sudo dump.f2fs /dev/sdX1
```

Features/Kompression/Checkpoint je Kernel und Tools. Vor Servereinsatz Recovery-, Distribution- und Backupunterstützung prüfen.

## tmpfs

RAM-/Swap-backed, flüchtig:

```bash
sudo mount -t tmpfs -o size=2G,mode=1777 tmpfs /mnt/tmp
```

fstab:

```fstab
tmpfs /mnt/tmp tmpfs size=2G,mode=1777,nosuid,nodev 0 0
```

Nutzung zählt gegen Speicher und kann Swapdruck erzeugen. `size` ist Obergrenze, nicht sofort reservierter RAM.

```bash
df -hT /dev/shm
findmnt -t tmpfs
```

Geeignet für temporäre Daten, nicht dauerhafte Backups.

## OverlayFS

Kombiniert Lower (read-only), Upper (Änderungen) und Workdir:

```bash
mkdir lower upper work merged
sudo mount -t overlay overlay \
  -o lowerdir=$PWD/lower,upperdir=$PWD/upper,workdir=$PWD/work \
  $PWD/merged
```

Verwendung in Container-Storage. Einschränkungen:

- Upper/Work müssen kompatibel und meist auf demselben FS liegen
- Whiteouts
- Rename/Hardlink/xattr-Semantik
- keine normalen Backups nur des Merged Views ohne Container-/Layerverständnis

Docker/Podman-Storage nicht manuell im laufenden Betrieb manipulieren.

## NFS

Serverexports:

```text
/etc/exports
```

Beispiel:

```exports
/srv/nfs/projects 192.0.2.0/24(rw,sync,root_squash,subtree_check)
```

Aktivieren:

```bash
sudo exportfs -rav
sudo exportfs -v
```

Client:

```bash
sudo mount -t nfs4 server:/projects /mnt/projects
```

Diagnose:

```bash
nfsstat -m
showmount -e server
rpcinfo -p server
ss -tulpn | grep 2049
```

NFSv4 nutzt Identitätsmapping/Domain und typischerweise Port 2049; NFSv3 benötigt zusätzliche RPC-Dienste/Ports.

Sicherheit:

- `root_squash`
- Kerberos `sec=krb5p` für starke Auth/Privacy
- Firewall/Netzsegment
- UID/GID-Konsistenz
- keine unsicheren Wildcardexports

## SMB/CIFS

Client:

```bash
sudo mount -t cifs //server/share /mnt/share \
  -o credentials=/root/.smbcred,vers=3.1.1,seal
```

Credentials:

```ini
username=alice
password=...
domain=EXAMPLE
```

```bash
sudo chmod 600 /root/.smbcred
```

Entdecken/Test:

```bash
smbclient -L //server -U alice
smbclient //server/share -U alice
```

Server Samba:

```bash
testparm
smbstatus
journalctl -u smb -b
```

SMB-ACLs und POSIX-ACLs müssen zusammenpassen. Multiprotocol SMB+NFS auf demselben Dataset ist komplex wegen Locking/ACL/Identity und sollte nur nach Appliance-/Samba-Dokumentation erfolgen.

## CephFS und verteilte Dateisysteme

CephFS:

```text
Clients → MDS → RADOS Cluster
```

Eigenschaften:

- verteilte Metadaten/Daten
- Scale-out
- Redundanz im Cluster
- Snapshots/Quotas je Version

Betrieb erfordert Quorum, Netzwerk, CRUSH, Recovery- und Kapazitätsverständnis. Kein Ersatz durch einzelne Mountbefehle.

Mount Kernelclient:

```bash
sudo mount -t ceph mon1,mon2,mon3:/ /mnt/ceph -o name=client.user,secretfile=/etc/ceph/user.secret
```

CephFS/FUSE/Kernelversionen kompatibel halten.

GlusterFS und andere Projekte nach aktuellem Produkt-/Communitystatus und Workload bewerten; keine neue Plattform nur wegen einfacher Demo wählen.

## ISO9660 und UDF

ISO:

```bash
sudo mount -o loop,ro image.iso /mnt/iso
```

Erstellen:

```bash
xorriso -as mkisofs -o image.iso verzeichnis/
```

UDF unterstützt größere Dateien und rewritable Medien, teils auch plattformübergreifende Datenträger.

```bash
sudo mkfs.udf /dev/sdX1
```

Optische/immutable Images vor Ausführung verifizieren:

```bash
sha256sum image.iso
```

## Auswahlmatrix

| Bedarf | Geeignet |
|---|---|
| UEFI Boot | FAT32 |
| großer USB-Stick plattformübergreifend | exFAT |
| Windows-Systemvolume | NTFS |
| FreeBSD klassisch | UFS2 oder ZFS |
| Flash/Android-Spezial | F2FS |
| flüchtige schnelle Daten | tmpfs |
| Containerlayer | OverlayFS |
| Unix-Netzfreigabe | NFSv4 |
| Windows-/AD-Freigabe | SMB 3.x |
| verteiltes Scale-out | CephFS |
| schreibgeschütztes Image | ISO9660/UDF |

## Quellen
- [Linux Filesystems Documentation](https://docs.kernel.org/filesystems/)
- [FreeBSD Handbook Filesystems](https://docs.freebsd.org/en/books/handbook/)
- [Samba Documentation](https://www.samba.org/samba/docs/)
- [NFS Linux Documentation](https://docs.kernel.org/filesystems/nfs/)

## Verwandte Notizen
- [[Dateisysteme – Cheatsheet]]
- [[TrueNAS – Cheatsheet]]
- [[Linux-Netzwerk – Cheatsheet]]
- [[Dateikompression unter Linux – Cheatsheet]]
