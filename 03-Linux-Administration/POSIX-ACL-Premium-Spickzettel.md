---
title: "POSIX ACL – getfacl und setfacl Premium-Spickzettel"
aliases: ["facl", "getfacl setfacl", "Linux ACL", "POSIX-ACL – Premium-Spickzettel"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [acl, facl, permissions, linux, getfacl, setfacl]
source: "https://man7.org/linux/man-pages/man1/getfacl.1.html"
---

# POSIX ACL – getfacl und setfacl Premium-Spickzettel

> [!abstract] Zweck
> Ausführliche Referenz für POSIX Access Control Lists: getfacl/setfacl, ACL-Maske, Default ACLs, Backup/Restore, rekursive Änderungen, effektive Rechte, Interaktion mit chmod und Diagnose.

> [!abstract] Zweck
> POSIX ACLs erweitern die klassischen Owner/Group/Other-Rechte um zusätzliche Benutzer- und Gruppeneinträge. Sie ersetzen weder SELinux noch Anwendungsberechtigungen und müssen mit der ACL-Maske verstanden werden.

## Inhalt

- [[#Grundmodell]]
- [[#ACL anzeigen]]
- [[#Benutzer- und Gruppenrechte setzen]]
- [[#Maske und effektive Rechte]]
- [[#Default ACLs]]
- [[#ACLs entfernen]]
- [[#Backup und Restore]]
- [[#Rekursiv und sicher arbeiten]]
- [[#Interaktion mit chmod, cp und rsync]]
- [[#Diagnose]]

## Grundmodell

Klassische Rechte:

```text
owner::rwx
group::r-x
other::---
```

Erweiterte ACL:

```text
user::rwx
user:alice:r-x
group::r-x
group:developers:rwx
mask::rwx
other::---
```

| Eintrag | Bedeutung |
|---|---|
| `user::` | Dateieigentümer |
| `user:name:` | benannter Benutzer |
| `group::` | besitzende Gruppe |
| `group:name:` | benannte Gruppe |
| `mask::` | maximale effektive Rechte für benannte User, owning group und benannte Gruppen |
| `other::` | alle übrigen |
| `default:` | Vererbungs-ACL auf Verzeichnis |

## ACL anzeigen

```bash
getfacl datei
getfacl -p /absoluter/pfad
getfacl -e datei
```

Nur effektive Rechte/ohne Kommentare je Optionen:

```bash
getfacl --absolute-names datei
```

`ls -l` zeigt `+` bei zusätzlicher ACL:

```text
-rw-rwx---+ 1 alice team ... datei
```

ACL-Unterstützung des Dateisystems/Mounts prüfen:

```bash
findmnt -no FSTYPE,OPTIONS -T datei
```

Moderne Linux-Dateisysteme unterstützen ACL meist standardmäßig; NFS/CIFS/Container/Objektspeicher können abweichende Semantik haben.

## Benutzer- und Gruppenrechte setzen

Benannter Benutzer:

```bash
setfacl -m u:alice:rw datei
```

Benannte Gruppe:

```bash
setfacl -m g:developers:rwx /srv/project
```

Mehrere Einträge:

```bash
setfacl -m u:alice:rw,g:auditors:r /srv/report.csv
```

Rechte entfernen:

```bash
setfacl -x u:alice datei
setfacl -x g:auditors datei
```

Eigentümer-/Gruppeneintrag:

```bash
setfacl -m u::rw,g::r,o::--- datei
```

Numerische IDs:

```bash
setfacl -m u:1500:rw datei
```

Namensauflösung bei Migration beachten.

## Maske und effektive Rechte

Beispiel:

```text
user:alice:rwx                 #effective:r-x
mask::r-x
```

Obwohl Alice `rwx` eingetragen hat, begrenzt `mask` auf `r-x`.

Maske setzen:

```bash
setfacl -m m::rwx datei
```

Automatische Maskenneuberechnung ist häufig Standard. Unterdrücken:

```bash
setfacl -n -m u:alice:rwx datei
```

> [!warning]
> `-n`/`--no-mask` kann bewusst gesetzte effektive Rechte anders belassen als erwartet. Nach jeder Änderung `getfacl` prüfen.

`chmod`-Gruppenbits repräsentieren bei erweiterter ACL häufig die ACL-Maske:

```bash
chmod g-w datei
```

kann effektive Rechte aller benannten User/Gruppen reduzieren.

## Default ACLs

Default ACL nur auf Verzeichnis; sie wird als Ausgangspunkt für neu erstellte Kinder verwendet.

```bash
setfacl -m d:u::rwx,d:g::rwx,d:o::--- /srv/project
setfacl -m d:g:developers:rwx /srv/project
setfacl -m d:m::rwx /srv/project
```

Zugriffs-ACL des Verzeichnisses ebenfalls setzen:

```bash
setfacl -m g:developers:rwx,m::rwx /srv/project
```

Anzeigen:

```bash
getfacl /srv/project
```

Test:

```bash
sudo -u alice touch /srv/project/test
getfacl /srv/project/test
```

> [!important]
> Default ACL ist keine dynamische Vererbung auf bestehende Dateien. Sie wirkt beim Erstellen, zusätzlich beeinflusst die angeforderte Mode/Umask die resultierenden Rechte.

### Gemeinsames Teamverzeichnis

```bash
sudo install -d -o root -g developers -m 2770 /srv/project
sudo setfacl -m g:developers:rwx,m::rwx /srv/project
sudo setfacl -m d:u::rwx,d:g::rwx,d:g:developers:rwx,d:m::rwx,d:o::--- /srv/project
```

Setgid hält die besitzende Gruppe konsistent; Default ACL steuert zusätzliche Rechte.

## ACLs entfernen

Alle erweiterten Access ACLs entfernen:

```bash
setfacl -b datei
```

Default ACL entfernen:

```bash
setfacl -k verzeichnis
```

Rekursiv:

```bash
setfacl -Rb /srv/tree
```

> [!danger]
> Rekursives Entfernen kann legitime differenzierte Rechte zerstören. Vorher Backup mit `getfacl -R`.

## Backup und Restore

Backup:

```bash
getfacl -R -p /srv/project > project.acl
```

Restore, möglichst aus passender Wurzel:

```bash
setfacl --restore=project.acl
```

Testkopie und Pfade prüfen. Backup enthält Owner/Group-Kommentare und ACL-Einträge; Nutzer/Gruppen müssen auf Ziel sinnvoll existieren.

Nur ACL spiegeln:

```bash
getfacl datei1 | setfacl --set-file=- datei2
```

Oder:

```bash
getfacl --access datei1 | setfacl --set-file=- datei2
```

## Rekursiv und sicher arbeiten

```bash
setfacl -R -m g:developers:rX /srv/data
```

`X` setzt Execute nur auf Verzeichnissen oder wenn bereits irgendein Execute-Bit gesetzt ist. Für Bäume meist sicherer als `x` auf allen Dateien.

Dateien und Verzeichnisse getrennt:

```bash
find /srv/data -type d -exec setfacl -m g:developers:rwx {} +
find /srv/data -type f -exec setfacl -m g:developers:rw- {} +
```

Symlinkverhalten und Dateisystemgrenzen mit `setfacl --help`/`find -xdev` beachten.

Dry Run gibt es nicht universell. Vorher:

```bash
getfacl -R -p /srv/data > before.acl
find /srv/data -maxdepth 2 -printf '%M %u %g %p\n' | head -100
```

## Interaktion mit chmod, cp und rsync

### chmod

Bei erweiterter ACL ändern Gruppenbits häufig die Maske. Deshalb nach `chmod`:

```bash
getfacl datei
```

### cp

Metadaten erhalten:

```bash
cp -a quelle ziel
```

ACL-Verhalten hängt von Dateisystem und cp-Version. Prüfen.

### rsync

```bash
rsync -aA quelle/ ziel/
```

Mit xattrs/Hardlinks:

```bash
rsync -aHAX quelle/ ziel/
```

Ziel-FS muss ACL abbilden; CIFS/NFS/Windows ACL können Übersetzung besitzen.

### tar

GNU tar:

```bash
tar --acls --xattrs -cpf backup.tar /srv/project
sudo tar --acls --xattrs -xpf backup.tar -C /restore
```

Optionen/Dateisystem testen; Owner/IDs und SELinux getrennt bedenken.

## Diagnose

### Benutzer hat weniger Rechte als Eintrag

```bash
id alice
getfacl /pfad/datei
namei -l /pfad/datei
```

Mask, Parent-X-Rechte, neue Login-Sitzung, besitzende Gruppen und ACL-Reihenfolge.

### `Operation not supported`

```bash
findmnt -T /pfad
tune2fs -l /dev/DEVICE 2>/dev/null | grep -i feature
```

Dateisystem/Mount/Netzwerkprotokoll unterstützt ACL nicht oder Serverexport/Clientmount nicht passend.

### ACL geht beim Kopieren verloren

- Kopiertool/Optionen
- Ziel-FS
- Mountprotokoll
- Benutzerrechte zum Setzen von ACL
- UID/GID-Namensauflösung

```bash
getfacl quelle
getfacl ziel
```

### Permission denied trotz ACL

```bash
namei -l /pfad/datei
getfacl /pfad /pfad/datei
ls -lZ /pfad/datei
findmnt -T /pfad/datei
```

SELinux, Read-only-Mount, immutable Flag (`lsattr`), NFS root squash und Anwendungsrechte prüfen.

### Effektive Rechte berechnen

```text
Wenn Benutzer Owner → user::
sonst wenn benannter user → user:name & mask
sonst passende Gruppen vereinigen → (group:: + group:name...) & mask
sonst → other::
```

DAC-Verzeichnisdurchquerung auf jedem Parent bleibt nötig.

## Quellen
- [getfacl Manual](https://man7.org/linux/man-pages/man1/getfacl.1.html)
- [setfacl Manual](https://man7.org/linux/man-pages/man1/setfacl.1.html)
- [acl Manual](https://man7.org/linux/man-pages/man5/acl.5.html)

## Verwandte Notizen
- [[Linux-Benutzer-und-Gruppenmanagement-Premium-Spickzettel]]
- [[SELinux-Premium-Spickzettel]]
- [[rsync-Premium-Spickzettel]]
- [[File-Compression-Linux-Premium-Spickzettel]]
