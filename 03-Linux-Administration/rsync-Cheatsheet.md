---
title: "rsync – Cheatsheet"
aliases: ["rsync Cheatsheet", "Linux Dateisynchronisation", "rsync Backup"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [rsync, backup, sync, ssh, linux]
source: "https://download.samba.org/pub/rsync/rsync.1"
---

# rsync – Cheatsheet

> [!abstract] Zweck
> Ausführliche rsync-Referenz für lokale und entfernte Kopien, Trailing-Slash-Semantik, Archive/ACL/xattrs, Delete, Filter, SSH, Snapshots, Resume, Performance, Backupsicherheit und Diagnose.

> [!danger] Synchronisation ist kein automatisches Backup
> `rsync --delete` kann Löschungen und Verschlüsselungsschäden replizieren. Vor destruktiven Läufen `--dry-run`, Quell-/Zielrichtung, Mountpoint und Ausschlüsse prüfen. Versionierte, getrennte und getestete Backups vorsehen.

## Inhalt

- [[#Grundmodell und Trailing Slash]]
- [[#Lokale Kopie]]
- [[#Remote über SSH]]
- [[#Attribute und Archivmodus]]
- [[#Delete und Sicherheitsoptionen]]
- [[#Filter und Excludes]]
- [[#Fortsetzen, Fortschritt und Performance]]
- [[#Snapshots mit Hardlinks]]
- [[#Backup über eingeschränkte Konten]]
- [[#Diagnose]]

## Grundmodell und Trailing Slash

Die wichtigste rsync-Regel:

```text
quelle/   = Inhalt des Verzeichnisses
quelle    = Verzeichnis selbst inklusive Name
```

Beispiel:

```bash
rsync -a quelle/ ziel/
```

Ergebnis:

```text
ziel/datei
```

Ohne Slash:

```bash
rsync -a quelle ziel/
```

Ergebnis:

```text
ziel/quelle/datei
```

> [!tip]
> Vor dem echten Lauf immer beide Pfade laut lesen: „Kopiere den Inhalt von X nach Y“ und mit `--dry-run --itemize-changes` verifizieren.

## Lokale Kopie

Basis:

```bash
rsync -avh --progress quelle/ ziel/
```

Dry Run:

```bash
rsync -avhn --itemize-changes quelle/ ziel/
```

| Option | Wirkung |
|---|---|
| `-a` | archive: rekursiv und viele Metadaten |
| `-v` | verbose |
| `-h` | lesbare Größen |
| `-n` | Dry Run |
| `-i` | itemize changes |
| `--progress` | Fortschritt pro Datei |
| `--info=progress2` | Gesamtfortschritt |

Nur neuere Quellfiles:

```bash
rsync -avu quelle/ ziel/
```

`-u` kann gewollte Wiederherstellung einer älteren Version verhindern; nicht blind für Backups.

## Remote über SSH

Lokale Quelle → Remoteziel:

```bash
rsync -aHAX --info=progress2 \
  ./daten/ \
  backup@server:/srv/backup/daten/
```

Remotequelle → lokal:

```bash
rsync -aHAX \
  backup@server:/srv/backup/daten/ \
  ./restore/
```

SSH-Optionen:

```bash
rsync -a -e 'ssh -p 2222 -i ~/.ssh/id_ed25519' quelle/ user@host:/ziel/
```

Mit SSH-Config besser:

```sshconfig
Host backup-server
    HostName backup.example.org
    User backup
    IdentityFile ~/.ssh/id_backup
    IdentitiesOnly yes
```

```bash
rsync -a quelle/ backup-server:/srv/backup/
```

Remote rsync-Pfad:

```bash
rsync -a --rsync-path='/usr/local/bin/rsync' quelle/ host:/ziel/
```

> [!warning]
> Shellquoting wirkt lokal und remote. Pfade mit Leerzeichen sorgfältig testen; möglichst einfache Pfadnamen und moderne rsync-Versionen nutzen.

## Attribute und Archivmodus

`-a` entspricht ungefähr:

```text
-rlptgoD
```

also rekursiv, Links, Zeiten, Rechte, Gruppen, Owner, Devices/Specials. Nicht automatisch enthalten:

- Hardlinks: `-H`
- ACLs: `-A`
- Extended Attributes: `-X`

Vollständiger Linux-Backupmodus:

```bash
sudo rsync -aHAX --numeric-ids quelle/ ziel/
```

| Option | Hinweis |
|---|---|
| `-H` | Hardlinks; zusätzlicher RAM/CPU |
| `-A` | POSIX ACLs; Ziel-FS muss sie unterstützen |
| `-X` | xattrs inkl. SELinux je Rechte/Version |
| `--numeric-ids` | UID/GID numerisch übertragen, wichtig bei unterschiedlichen NSS-Namen |
| `--fake-super` | Metadaten in xattrs speichern, nützlich ohne Root/auf bestimmten Zielen |

> [!important]
> Quell- und Zielsystem, Dateisystem und rsync-Rechte bestimmen, welche Metadaten wirklich erhalten bleiben. Nach Backup Stichprobe mit `stat`, `getfacl`, `getfattr`, `ls -Z` und Hardlink-Inodes prüfen.

Sparse Files:

```bash
rsync -aS quelle/ ziel/
```

Reflinks/COW werden nicht automatisch als solche erhalten; Ziel-FS-spezifische Snapshotmechanismen können besser sein.

## Delete und Sicherheitsoptionen

Ziel an Quelle spiegeln:

```bash
rsync -a --delete --dry-run quelle/ ziel/
```

Erst nach Prüfung:

```bash
rsync -a --delete quelle/ ziel/
```

Varianten:

| Option | Verhalten |
|---|---|
| `--delete-before` | vor Transfer löschen; Platz, aber riskanter bei Abbruch |
| `--delete-during` | während Lauf, häufig Standardverhalten |
| `--delete-delay` | Löschungen bis Transferende sammeln |
| `--delete-after` | nach Transfer; mehr Platzbedarf |
| `--delete-excluded` | auch ausgeschlossene Zielobjekte löschen; besonders gefährlich |
|max-delete | Löschlimit je Version/Option `--max-delete=N` |

Schutz:

```bash
rsync -a --delete --max-delete=100 --dry-run quelle/ ziel/
```

Mountpoint absichern:

```bash
mountpoint -q /mnt/backup || { echo 'Backup nicht gemountet' >&2; exit 1; }
rsync ... /mnt/backup/
```

Quell-/Zielwurzel mit Sentinel:

```bash
test -f /mnt/backup/.rsync-target-ok || exit 1
```

### Änderungsbackup

Überschriebene/gelöschte Zieldateien sichern:

```bash
rsync -a --delete \
  --backup \
  --backup-dir="../deleted-$(date +%F-%H%M%S)" \
  quelle/ ziel/current/
```

## Filter und Excludes

Einzelne Muster:

```bash
rsync -a \
  --exclude='.cache/' \
  --exclude='*.tmp' \
  quelle/ ziel/
```

Datei:

```bash
rsync -a --exclude-from=rsync-excludes.txt quelle/ ziel/
```

```text
.cache/
*.tmp
/node_modules/
```

Include/Exclude-Reihenfolge ist relevant:

```bash
rsync -a \
  --include='*/' \
  --include='*.pdf' \
  --exclude='*' \
  quelle/ ziel/
```

Nur PDF, Verzeichnisse müssen eingeschlossen bleiben, damit Traversierung möglich ist.

Filter debuggen:

```bash
rsync -ain --debug=FILTER quelle/ ziel/
```

Optionen können je Version variieren.

## Fortsetzen, Fortschritt und Performance

Partials behalten:

```bash
rsync -a --partial --partial-dir=.rsync-partial quelle/ ziel/
```

In-place:

```bash
rsync -a --inplace grosse-datei host:/ziel/
```

> [!warning]
> `--inplace` verändert Zieldatei während Transfer und verschlechtert atomare Sicherheit/Snapshot-Hardlink-Verhalten. Nur bei bewusstem Use Case.

Append:

```bash
rsync --append-verify grosse.log host:/ziel/
```

Nur für Dateien, die tatsächlich append-only wachsen.

Kompression:

```bash
rsync -az quelle/ host:/ziel/
```

Bei bereits komprimierten Daten oder schnellem LAN kostet `-z` oft nur CPU. Moderne rsync-Versionen haben weitere Kompressionsoptionen; beide Enden müssen sie unterstützen.

Bandbreite:

```bash
rsync -a --bwlimit=20m quelle/ host:/ziel/
```

Checksummenvergleich:

```bash
rsync -acn quelle/ ziel/
```

`-c` liest alle Dateiinhalte und ist deutlich teurer. Standard nutzt Größe + mtime.

## Snapshots mit Hardlinks

Einfaches rotierendes Snapshotmuster:

```bash
stamp=$(date +%F-%H%M%S)
latest=/backup/latest
new=/backup/snapshots/$stamp

mkdir -p "$new"
rsync -aHAX --delete \
  --link-dest="$latest" \
  /source/ "$new/"
ln -sfn "$new" "$latest"
```

`--link-dest` muss sinnvoll auf vorhandenen Snapshot zeigen. Unveränderte Dateien werden hart verlinkt.

> [!danger]
> Dateien in Snapshots nie in-place verändern, sonst ändern sich alle hart verlinkten Ansichten. Snapshots read-only behandeln; externe Retention und Offsitekopie vorsehen.

Prüfen:

```bash
stat -c '%i %h %n' snapshot1/datei snapshot2/datei
```

Für große Systeme oft spezialisierte Tools oder ZFS/Btrfs-Snapshots verwenden.

## Backup über eingeschränkte Konten

Prinzipien:

- eigener SSH-Key und Benutzer
- nur benötigter Zielpfad
- keine interaktive Shell, wenn nicht nötig
- serverseitig erzwungener Befehl/rrsync oder Backupdaemon
- Quota und schreibgeschützte ältere Snapshots
- kein Root-Login
- getrenntes Konto pro Quelle

`authorized_keys` kann Einschränkungen enthalten:

```text
restrict,command="/usr/local/bin/rrsync /srv/backup/client1" ssh-ed25519 AAAA...
```

`rrsync`-Verfügbarkeit und Pfad aus rsync-Paket prüfen. Einschränkung testen; Remote-Shell-Funktionen können sonst fehlen.

### Root-Metadaten ohne volles Remote-Root

Möglichkeiten:

- rsync daemon mit Modulrechten
- `--fake-super`
- gezieltes `sudo rsync` via erzwungenem Befehl
- Snapshot auf Quelle, dann nichtprivilegierter Export

Sudoers so eng wie möglich; rsync mit frei wählbaren Argumenten kann sehr mächtig sein.

## Diagnose

### „Permission denied“

```bash
namei -l /ziel/pfad
getfacl /ziel/pfad
ssh -v host
rsync -avvn quelle/ host:/ziel/
```

Owner, ACL, SELinux, Read-only-Mount, Remoteuser und Parentverzeichnisse prüfen.

### Dateien werden immer übertragen

- Uhrzeiten/Zeitzonen und mtime-Auflösung
- Dateisystem rundet Zeitstempel
- Anwendung verändert Datei beim Lauf
- `--checksum`/Attribute
- Ziel kann mtime nicht setzen

```bash
stat quelle/datei ziel/datei
rsync -ain quelle/ ziel/
```

Option `--modify-window` für grobe Zeitauflösung, nur nach Analyse.

### Exitcodes

```bash
rsync ...
code=$?
echo "$code"
```

Häufig:

- `0` Erfolg
- `23` Teiltransfer wegen Fehler
- `24` Quelldateien verschwanden während Lauf
- `12` Protokolldatenstrom
- `30` Timeout

Exakte Bedeutung `man rsync` der Version. Exit 24 kann bei lebenden Bäumen erwartbar sein, muss aber bewertet werden.

### Version/Protokoll

```bash
rsync --version
ssh host rsync --version
```

Featureunterschiede zwischen beiden Enden prüfen.

### Universelle Prüfreihenfolge

```bash
rsync -aHAXnvi --delete quelle/ ziel/
```

Dann:

1. Trailing Slash
2. Quell-/Ziel-Mountpoint
3. Filterausgabe
4. Rechte/UID/GID/ACL/xattrs
5. Platz/Inodes
6. rsync-Versionen
7. Log + Exitcode
8. Restoretest einer Stichprobe

## Quellen
- [rsync Manual](https://download.samba.org/pub/rsync/rsync.1)
- [rsync Project](https://rsync.samba.org/)

## Verwandte Notizen
- [[SSH-Cheatsheet]]
- [[rclone-Cheatsheet]]
- [[POSIX-ACL-Cheatsheet]]
- [[Syncthing-Cheatsheet]]
