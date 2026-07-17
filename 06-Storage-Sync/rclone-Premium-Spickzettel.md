---
title: "rclone – Premium-Spickzettel"
aliases: ["rclone Cheatsheet", "Cloud Sync CLI", "rclone crypt mount bisync"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [rclone, cloud, sync, backup, encryption, mount]
source: "https://rclone.org/docs/"
---

# rclone – Premium-Spickzettel

> [!abstract] Zweck
> Sehr ausführliche rclone-Referenz für Remotes, copy/sync/move, Dry Runs, Filter, Checks, Cloud-Backends, Crypt, Mount, Serve, Bisync, Bandbreite, Transfers, systemd, Logging, Sicherheit und Recovery.

> [!danger] `sync` spiegelt Löschungen
> `rclone sync QUELLE ZIEL` verändert das Ziel so, dass es der Quelle entspricht, und kann überschüssige Zieldateien löschen. Vor jedem neuen oder geänderten Lauf `--dry-run`, `--interactive` und einen getrennten Backup-/Versionierungsmechanismus verwenden.

## Inhalt

- [[#Grundmodell]]
- [[#Installation und Version]]
- [[#Remotes konfigurieren]]
- [[#ls, copy, sync und move]]
- [[#Trailing Slashes und Pfade]]
- [[#Dry Run, Interaktivität und Backup-Dir]]
- [[#Filter und Excludes]]
- [[#Prüfen und Integrität]]
- [[#Performance und Bandbreite]]
- [[#Crypt Remote]]
- [[#Mount]]
- [[#Bisync]]
- [[#Serve und Netzwerkdienste]]
- [[#Systemd und Automatisierung]]
- [[#Logs, Exitcodes und Statistik]]
- [[#Sicherheit]]
- [[#Diagnose und Recovery]]
- [[#Schnellrezepte]]

## Grundmodell

Syntax:

```bash
rclone command source:path dest:path [flags]
```

Begriffe:

| Begriff | Bedeutung |
|---|---|
| Remote | konfigurierter Backendname, z. B. `drive:` |
| Backend | Anbieter/Protokoll wie S3, WebDAV, SFTP, OneDrive |
| Local | lokales Dateisystem, ohne Remote-Präfix |
| Object | Cloudobjekt, Semantik kann von Datei abweichen |
| Server-side copy | Kopie im Backend ohne Download, wenn unterstützt |
| Crypt | clientseitige Verschlüsselung über einem Remote |
| VFS Cache | lokaler Cache für `rclone mount` |

> [!important]
> Cloudbackends unterscheiden sich bei Hashes, ModTime, Case-Sensitivity, Unicode, leeren Verzeichnissen, Symlinks und atomaren Renames. Ein Befehl kann je Backend andere Grenzen haben.

## Installation und Version

```bash
rclone version
rclone help
rclone help flags
rclone help backends
```

Paketmanager oder offizielles Release verwenden. Nach Upgrade:

```bash
rclone version
rclone config show | sed -E 's/(pass|secret|token).*/REDACTED/I'
```

Automatisierte Installation aus dem Internet nur mit verifizierter Quelle/Checksumme und Changeprozess.

Selfupdate, falls Installationsart passt:

```bash
rclone selfupdate --check
rclone selfupdate
```

Distributionspakete nicht unkoordiniert mit Selfupdate überschreiben.

## Remotes konfigurieren

Interaktiv:

```bash
rclone config
```

Liste:

```bash
rclone listremotes
rclone config file
rclone config show remote
```

Konfigurationsdatei typischerweise:

```text
~/.config/rclone/rclone.conf
```

Rechte:

```bash
chmod 600 ~/.config/rclone/rclone.conf
```

Remote testen:

```bash
rclone lsd remote:
rclone about remote:
rclone backend features remote:
```

Nichtinteraktiv:

```bash
rclone config create myremote s3 provider Minio env_auth true endpoint https://s3.example.org
```

Secrets bevorzugt über Environment, Secret Store oder stdin/obscured Parameter gemäß Backenddoku; CLI-Argumente können in History/Prozessliste erscheinen.

Konfigurationspasswort:

```bash
rclone config encryption set
```

Bei automatischem Betrieb `RCLONE_CONFIG_PASS` ist selbst ein Secret und muss geschützt bereitgestellt werden.

## ls, copy, sync und move

Auflisten:

```bash
rclone lsd remote:
rclone lsl remote:path
rclone lsjson remote:path
rclone size remote:path
rclone tree remote:path
```

`lsjson` für Skripte:

```bash
rclone lsjson --recursive remote:path | jq .
```

Copy:

```bash
rclone copy ./daten remote:backup/daten --progress
```

- kopiert neue/geänderte Dateien
- löscht keine zusätzlichen Zieldateien
- kopiert Inhalt des Quellpfads in Zielpfad gemäß rclone-Semantik

Copyto für exakt ein Objekt/einen Zielnamen:

```bash
rclone copyto ./report.pdf remote:reports/report-2026-07.pdf
```

Sync:

```bash
rclone sync ./daten remote:mirror/daten --progress
```

Zusätzliche Dateien am Ziel werden gelöscht.

Move:

```bash
rclone move ./inbox remote:archive/inbox --progress
```

Quelle wird nach erfolgreicher Übertragung entfernt. Nicht als erstes mit ungetestetem Backend.

Moveto:

```bash
rclone moveto remote:inbox/a.txt remote:archive/a.txt
```

Delete/Purge:

```bash
rclone delete remote:path
rclone purge remote:path
```

- `delete` entfernt Dateien nach Filtern, leere Verzeichnisse können bleiben.
- `purge` entfernt gesamten Pfad inklusive Inhalt.

> [!danger]
> `purge` und `delete` nur nach `--dry-run`, genauer Remote-/Pfadprüfung und vorhandenem Restorepfad.

## Trailing Slashes und Pfade

rclone verhält sich nicht in jedem Detail wie rsync. Grundsätzlich bezieht sich `copy source:path dest:path` auf den **Inhalt** des Quellpfads; der letzte Quellverzeichnisname wird nicht automatisch als zusätzliche Ebene erzeugt.

Beispiel:

```bash
rclone copy /srv/photos remote:backup/photos
```

Ergebnis:

```text
remote:backup/photos/<Inhalt von /srv/photos>
```

Remote-Pfade mit Leerzeichen quoten:

```bash
rclone copy './Meine Daten' 'remote:Backups/Meine Daten'
```

Shellglobbing vermeiden:

```bash
rclone ls 'remote:bucket/*.txt'        # Backendpfad, nicht zwingend Glob
rclone ls remote:bucket --include '*.txt'
```

Filteroptionen sind verlässlicher als Shellglobs auf Remotes.

## Dry Run, Interaktivität und Backup-Dir

Dry Run:

```bash
rclone sync ./daten remote:mirror --dry-run -vv
```

Interaktiv:

```bash
rclone sync ./daten remote:mirror --interactive
```

Änderungen auflisten:

```bash
rclone sync ./daten remote:mirror \
  --dry-run \
  --combined changes.txt \
  --create-empty-src-dirs
```

Gelöschte/ersetzte Dateien versionieren:

```bash
stamp=$(date +%F-%H%M%S)
rclone sync ./daten remote:mirror \
  --backup-dir "remote:versions/$stamp" \
  --suffix ".old-$stamp" \
  --progress
```

Backend muss serverseitige Move/Copy-Semantik passend unterstützen; sonst Kosten/Traffic beachten.

Löschzeitpunkt:

```bash
--delete-before
--delete-during
--delete-after
```

Default/Backendverhalten prüfen. `--delete-after` ist häufig risikoärmer bei Transferfehlern, benötigt aber Platz.

Maximale Löschungen:

```bash
--max-delete 100
--max-delete-size 10G
```

Sicherheitsgurt für automatisierte Jobs.

## Filter und Excludes

Excludes:

```bash
rclone copy . remote:backup \
  --exclude '.git/**' \
  --exclude '*.tmp' \
  --exclude '/cache/**'
```

Include:

```bash
rclone copy . remote:reports --include '*.pdf'
```

Filterdatei:

```text
# filters.txt
- /.git/**
- /node_modules/**
- *.tmp
+ /docs/**
- **
```

```bash
rclone copy . remote:backup --filter-from filters.txt
```

Reihenfolge der Regeln ist wichtig. Test:

```bash
rclone ls . --filter-from filters.txt
rclone copy . remote:backup --filter-from filters.txt --dry-run -vv
```

Alter/Größe:

```bash
--min-age 24h
--max-age 30d
--min-size 1M
--max-size 10G
```

Neuere Dateien ausschließen kann Dateien dauerhaft verpassen, wenn Zeitfenster/Jobausfall nicht bedacht wird.

## Prüfen und Integrität

Quelle/Ziel vergleichen:

```bash
rclone check ./daten remote:backup/daten
```

Nur Größe, schneller aber schwächer:

```bash
rclone check ./daten remote:backup/daten --size-only
```

One-way:

```bash
rclone check ./daten remote:backup/daten --one-way
```

Checksums, falls Backend unterstützt:

```bash
rclone check ./daten remote:backup/daten --checksum
rclone hashsum SHA-256 remote:path
```

Fehlerlisten:

```bash
rclone check source:path dest:path \
  --differ differ.txt \
  --missing-on-dst missing-dst.txt \
  --missing-on-src missing-src.txt \
  --error errors.txt
```

`cryptcheck` für Crypt-Remote, wenn Backend-Hashes/Nonce-Semantik unterstützt:

```bash
rclone cryptcheck local:path cryptremote:path
```

Test-Restore bleibt wichtiger als ein reiner Vergleich.

## Performance und Bandbreite

Transfers/Checker:

```bash
rclone copy source: dest: --transfers 8 --checkers 16
```

Mehr ist nicht immer schneller; API-Limits, RAM, Disk und WAN berücksichtigen.

Bandbreite:

```bash
rclone copy source: dest: --bwlimit 20M
```

Zeitplan:

```bash
--bwlimit '08:00,5M 18:00,off'
```

TPS/API-Limit:

```bash
--tpslimit 10 --tpslimit-burst 20
```

Retries:

```bash
--retries 5 --low-level-retries 20 --retries-sleep 10s
```

Große Dateien/Chunking backendabhängig. S3:

```bash
--s3-chunk-size 64M
--s3-upload-concurrency 4
```

RAM steigt grob mit Chunkgröße × Concurrency.

Server-side Copy:

```bash
rclone copy remote:path remote:other --server-side-across-configs
```

Nur für kompatible Accounts/Backends und nach Berechtigungs-/Kostenprüfung.

## Crypt Remote

Zuerst Basisremote, dann `crypt` darüber:

```bash
rclone config
```

Beispielkonzept:

```text
cloud:             Klartext-Backend
cloudcrypt:        crypt über cloud:encrypted
```

Test:

```bash
rclone mkdir cloudcrypt:test
rclone copy test.txt cloudcrypt:test
rclone lsl cloudcrypt:test
rclone lsl cloud:encrypted
```

Crypt verschlüsselt:

- Dateiinhalte
- optional Dateinamen
- optional Verzeichnisnamen

Nicht zwingend verborgen:

- Anzahl/Größenmuster
- Zeitpunkte
- Zugriffsmuster
- Kontometadaten

Passwörter sichern:

```bash
rclone config show cloudcrypt
```

Ausgabe enthält obscured Werte, die für rclone praktisch Secretmaterial darstellen. Konfiguration und Passwörter getrennt/offline sichern.

> [!danger]
> Ohne Crypt-Passwort/Salt/Config sind Daten nicht wiederherstellbar. Restore auf einem zweiten System testen.

Dateinamen entschlüsseln zur Diagnose:

```bash
rclone cryptdecode cloudcrypt: ENCRYPTED_NAME
```

## Mount

FUSE-Mount:

```bash
mkdir -p ~/mnt/cloud
rclone mount remote:path ~/mnt/cloud --vfs-cache-mode full
```

Hintergrund besser über systemd statt `&`.

Wichtige Optionen:

```bash
--vfs-cache-mode off|minimal|writes|full
--vfs-cache-max-size 20G
--vfs-cache-max-age 24h
--dir-cache-time 5m
--poll-interval 1m
--buffer-size 16M
--read-only
--allow-other
```

`--allow-other` benötigt FUSE-Konfiguration und erweitert Zugriff. UID/GID/Masken prüfen.

Unmount:

```bash
fusermount3 -u ~/mnt/cloud
# oder
umount ~/mnt/cloud
```

> [!important]
> Cloudobjektstorage ist kein vollwertiges POSIX-Dateisystem. Locking, atomare Renames, Hardlinks, Sparse Files, xattrs, Symlinks und Datenbanken können ungeeignet sein. Keine VM-/Datenbankdateien ungetestet direkt auf rclone mount betreiben.

VFS-Status/RC:

```bash
rclone mount ... --rc --rc-addr 127.0.0.1:5572
rclone rc vfs/stats
rclone rc vfs/refresh recursive=true
```

RC nicht ungeschützt im Netz exponieren.

## Bisync

Bidirektionale Synchronisierung:

```bash
rclone bisync local:path remote:path --resync --dry-run
```

Initialisierung:

```bash
rclone bisync local:path remote:path --resync
```

Danach regulär:

```bash
rclone bisync local:path remote:path
```

> [!danger]
> `--resync` bestimmt Baseline und kann bei falscher Richtung/Conflict-Strategie unerwartet überschreiben. Dokumentation der installierten Version lesen und mit Testdaten beginnen.

Konflikte, Listings und Lockfiles verstehen. Bisync ist kein Multi-Writer-Distributed-Filesystem. Gleichzeitige Änderungen, Clock/ModTime, Backendsemantik und Jobabbrüche testen.

Sicherheitsoptionen:

```bash
--max-delete 50
--check-access
--conflict-resolve newer
```

Conflict-Strategie nur mit verlässlichen Zeiten. Versionierung/Backups zusätzlich.

## Serve und Netzwerkdienste

rclone kann Backends bereitstellen:

```bash
rclone serve http remote:path --addr 127.0.0.1:8080
rclone serve webdav remote:path --addr 127.0.0.1:8080
rclone serve sftp remote:path --addr 127.0.0.1:2022
```

> [!danger]
> Standardmäßig nur Loopback. Für Netzwerkfreigabe TLS, starke Authentisierung, Firewall und Least Privilege konfigurieren. Viele Serve-Modi sind keine Ersatzlösung für einen gehärteten Produktivserver.

Optionen je Protokoll über:

```bash
rclone serve webdav --help
```

## Systemd und Automatisierung

### Copy-/Sync-Service

```ini
# /etc/systemd/system/rclone-backup.service
[Unit]
Description=Rclone Backup
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=backup
Group=backup
EnvironmentFile=/etc/rclone/backup.env
ExecStart=/usr/bin/rclone copy /srv/data cloudcrypt:server/data \
  --config /etc/rclone/rclone.conf \
  --log-file /var/log/rclone/backup.log \
  --log-level INFO \
  --transfers 4 \
  --checkers 8 \
  --max-delete 0
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
```

Timer:

```ini
[Unit]
Description=Daily Rclone Backup

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rclone-backup.timer
systemctl list-timers rclone-backup.timer
```

### Mount-Service

```ini
[Unit]
Description=Rclone Mount
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=alice
ExecStart=/usr/bin/rclone mount remote:path /home/alice/mnt/cloud \
  --config=/home/alice/.config/rclone/rclone.conf \
  --vfs-cache-mode=full \
  --vfs-cache-max-size=20G
ExecStop=/bin/fusermount3 -u /home/alice/mnt/cloud
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

Pfade/Permissions/FUSE je User prüfen. Secrets nicht direkt in Unit.

## Logs, Exitcodes und Statistik

Live Statistik:

```bash
rclone copy source: dest: --progress
rclone copy source: dest: --stats 10s --stats-one-line
```

Logs:

```bash
--log-level INFO
--log-file /var/log/rclone/job.log
--use-json-log
```

Verbose nur temporär:

```bash
-v
-vv
```

Debuglogs können Tokens, Pfade und Metadaten enthalten; redigieren.

Exitcode:

```bash
rclone copy ...
rc=$?
echo "$rc"
```

Automatisierung soll Nonzero melden und Erfolg nur nach `check`/Jobstatistik bestätigen.

RC/Prometheus:

```bash
rclone rcd --rc-addr 127.0.0.1:5572 --rc-enable-metrics
```

Zugriff absichern.

## Sicherheit

- `rclone.conf` als Secret.
- OAuth Tokens minimal berechtigen, getrennte Serviceaccounts.
- Crypt für untrusted Cloud, aber Schlüssel separat sichern.
- TLS validieren; `--no-check-certificate` nicht dauerhaft.
- Remote-Control nur Loopback/Auth/TLS.
- Sync-Delete mit `--max-delete`, `--backup-dir`, Versioning.
- Logs und PC/Cloudmetadaten schützen.
- Keine Passwörter in CLI/History.
- Backendversionierung/Object Lock für wichtige Backups.
- Ransomware kann erreichbare Remotes verändern; immutable/offline Kopie.
- Restore regelmäßig testen.

## Diagnose und Recovery

Effektive Version/Config:

```bash
rclone version
rclone config file
rclone listremotes
rclone backend features remote:
```

Connectivity:

```bash
rclone lsd remote: -vv
rclone about remote:
```

Ein Objekt:

```bash
rclone copyto test.txt remote:test/test.txt -vv
rclone cat remote:test/test.txt
```

Vergleich:

```bash
rclone check local:path remote:path -vv
```

Häufige Probleme:

| Symptom | Ursache |
|---|---|
| ModTime-Daueränderungen | Backend speichert Zeit nicht exakt |
| Hash fehlt | Backend unterstützt keinen kompatiblen Hash |
| 429/Rate limit | zu viele Transfers/TPS |
| Mount hängt | Backend/Netz/VFS Cache/Daemon |
| Dateinamenfehler | Encoding/Case/Backendrestriktion |
| Sync löscht unerwartet | Quelle/Ziel vertauscht, Filter, leere Mountquelle |
| Auth abgelaufen | OAuth Token/Clock/Serviceaccount |
| Crypt nicht lesbar | falsches Passwort/Salt/Remotepfad |

> [!danger] Leere Quelle
> Wenn ein lokaler Mount nicht vorhanden ist, kann ein erwarteter Quellpfad leer erscheinen und `sync` das Ziel leeren. Vor Sync Mountpoint mit `findmnt`, Sentinel-Datei und `--check-first`/Access-Check verifizieren.

Beispiel Guard:

```bash
mountpoint -q /srv/data || exit 1
test -f /srv/data/.backup-source-ok || exit 1
rclone sync /srv/data cloudcrypt:mirror --max-delete 100 --backup-dir cloudcrypt:versions/$(date +%F)
```

## Schnellrezepte

Sichere neue Kopie:

```bash
rclone copy /srv/data cloudcrypt:backup/data \
  --dry-run -vv
```

Dann echt:

```bash
rclone copy /srv/data cloudcrypt:backup/data \
  --progress --transfers 4 --checkers 8
rclone check /srv/data cloudcrypt:backup/data
```

Versionierter Mirror:

```bash
stamp=$(date +%F-%H%M%S)
rclone sync /srv/data cloudcrypt:mirror/data \
  --backup-dir "cloudcrypt:versions/data/$stamp" \
  --max-delete 100 \
  --check-first \
  --log-file /var/log/rclone/data.log \
  --log-level INFO
```

Restore:

```bash
rclone copy cloudcrypt:mirror/data /restore/data --progress
rclone check cloudcrypt:mirror/data /restore/data
```

## Quellen
- [rclone Documentation](https://rclone.org/docs/)
- [rclone Commands](https://rclone.org/commands/)
- [rclone Crypt](https://rclone.org/crypt/)
- [rclone Mount](https://rclone.org/commands/rclone_mount/)
- [rclone Bisync](https://rclone.org/bisync/)

## Verwandte Notizen
- [[rsync – Premium-Spickzettel]]
- [[Syncthing – Premium-Spickzettel]]
- [[TrueNAS – Premium-Spickzettel]]
- [[Dateisysteme – Premium-Spickzettel]]
