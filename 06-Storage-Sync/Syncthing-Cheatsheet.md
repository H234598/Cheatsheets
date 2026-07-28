---
title: "Syncthing – Cheatsheet"
aliases: ["Syncthing Cheatsheet", "Peer to Peer Dateisynchronisation", "Syncthing Administration"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [syncthing, sync, peer-to-peer, backup, security]
source: "https://docs.syncthing.net/"
---

# Syncthing – Cheatsheet

> [!abstract] Zweck
> Ausführliche Syncthing-Referenz für Geräte und Ordner, Send/Receive-Typen, Versionierung, Ignore Patterns, Rechte, Konflikte, Discovery/Relay, GUI/API, systemd, Updates, Sicherheit, Backups und Diagnose.

> [!danger] Synchronisation ist kein Backup
> Löschungen, Verschlüsselungsschäden und Fehländerungen können auf alle Geräte repliziert werden. Dateiversionierung und ein separates offline/immutable Backup verwenden. Die Syncthing-Konfiguration samt Geräteidentität ebenfalls sichern.

## Inhalt

- [[#Grundmodell]]
- [[#Installation und Betriebsarten]]
- [[#Geräte koppeln]]
- [[#Ordner hinzufügen und Typen]]
- [[#Versionierung]]
- [[#Ignore Patterns]]
- [[#Dateirechte, Ownership und Metadaten]]
- [[#Konflikte und Override/Revert]]
- [[#Discovery, Relays und Ports]]
- [[#GUI, API und CLI]]
- [[#Systemd und Mehrbenutzerbetrieb]]
- [[#Performance und Datenbank]]
- [[#Sicherheit]]
- [[#Backup und Migration]]
- [[#Diagnose]]
- [[#Abnahmecheckliste]]

## Grundmodell

- Jedes Gerät besitzt eine kryptografische Geräte-ID.
- Ordner werden explizit zwischen ausgewählten Geräten geteilt.
- Änderungen werden blockweise erkannt und übertragen.
- Geräte verbinden sich direkt oder über Relays.
- Discovery findet Adressen; Datenübertragung bleibt authentisiert/verschlüsselt.
- Es gibt keinen zwingenden zentralen Server.

Begriffe:

| Begriff | Bedeutung |
|---|---|
| Device ID | öffentliche Identität eines Syncthing-Geräts |
| Folder ID | stabile logische Ordnerkennung |
| Folder Path | lokaler Pfad auf einem Gerät |
| Introducer | Gerät, das weitere Gerätebeziehungen bekanntmachen kann |
| Global Discovery | Dienst zur Adressauffindung |
| Local Discovery | Broadcast/Multicast im LAN |
| Relay | vermittelt Daten, falls direkte Verbindung nicht gelingt |
| Index Database | lokaler Zustand/Metadaten der Synchronisierung |

## Installation und Betriebsarten

Version:

```bash
syncthing --version
syncthing --help
```

Typische Betriebsarten:

- Desktopbenutzer als User-Service
- Headless Server als dedizierter Benutzer
- Container, mit persistentem Config- und Datenvolume
- systemweiter Dienst pro explizitem Konto

Nicht als Root betreiben, nur um Rechteprobleme zu umgehen.

Initial starten:

```bash
syncthing
```

Standard-GUI häufig auf Loopback `127.0.0.1:8384`. Konfiguration je OS unter Benutzerprofil, Linux typischerweise XDG-/`~/.config/syncthing` oder versionsabhängig. Effektiv anzeigen:

```bash
syncthing paths
```

## Geräte koppeln

Geräte-ID anzeigen:

```bash
syncthing device-id
```

In GUI:

```text
Actions → Show ID
Add Remote Device
```

Sicher koppeln:

1. Device IDs über vertrauenswürdigen Kanal vergleichen.
2. sprechenden Namen vergeben.
3. keine ungeprüften Ordnerfreigaben automatisch akzeptieren.
4. Address `dynamic` bevorzugen, statisch nur bei Bedarf.
5. Introducer nur für vertrauenswürdige Topologien.

Device ID ist nicht geheim, aber Identitäts-/Topologiedatum. Sie ersetzt keine Benutzerautorisierung auf dem lokalen Dateisystem.

## Ordner hinzufügen und Typen

Ordnerparameter:

- Label
- Folder ID
- Path
- Geräte
- Folder Type
- Rescan Interval / Watcher
- Versioning
- Ignore Permissions
- Minimum Free Disk Space
- File Pull Order

### Send & Receive

Standard. Änderungen in beide Richtungen.

### Send Only

Lokale Seite gilt operativ als Quelle. Remoteänderungen erscheinen als „out of sync“ und können über **Override Changes** überschrieben werden.

Geeignet für:

- Verteilung aus kontrollierter Quelle
- nicht allein als Backup, da lokale Löschungen repliziert werden

### Receive Only

Lokale Änderungen werden als Abweichung markiert; **Revert Local Changes** setzt auf Clusterzustand zurück.

Geeignet für Ziel-/Archivknoten, aber lokale Versionierung/Backup weiterhin.

### Receive Encrypted

Je aktueller Version: untrusted Device speichert verschlüsselte Ordnerdaten, benötigt Passwort/Schlüsselkonzept. Featurestatus/Kompatibilität der installierten Version prüfen und Restore testen.

> [!warning]
> „Send Only“ verhindert nicht, dass kompromittierte/fehlerhafte Quelldaten verteilt werden. „Receive Only“ ist nicht automatisch immutable.

## Versionierung

In Ordner → File Versioning.

Typen:

| Typ | Verhalten |
|---|---|
| Trash Can | alte Version für definierte Zeit |
| Simple | feste Anzahl Versionen |
| Staggered | viele jüngere, zunehmend ausgedünnte ältere Versionen |
| External | eigenes Kommando/Skript |

Versionierte Dateien landen typischerweise in `.stversions` oder konfiguriertem Pfad.

Planung:

- Versionierung auf mehreren Geräten?
- Speicherbedarf/Retention.
- `.stversions` im Backup.
- Ransomware-Szenario.
- Restore testen.

External Versioning erhält Pfade/Variablen gemäß Doku. Skript robust gegen Sonderzeichen, Parallelität und Fehler schreiben.

> [!important]
> Versionierung reagiert auf durch Synchronisation ersetzte/gelöschte Dateien. Sie ist kein vollständiges Langzeitbackup der Syncthing-Datenbank, Konfiguration oder aller lokalen Änderungen.

## Ignore Patterns

Datei im Folderroot:

```text
.stignore
```

Beispiel:

```text
// Kommentare
.git
node_modules
*.tmp
(?d)cache
(?i)Thumbs.db
#include common-ignore.txt
```

Semantik exakt in der Syncthing-Doku/GUI-Hilfe prüfen. Wichtige Marker:

- `!` Negation
- `(?i)` case-insensitive
- `(?d)` ignorierte Dateien dürfen gelöscht werden, wenn nötig
- `#include` Include-Datei

Test/Ansicht über GUI **Edit Ignore Patterns**. `.stignore` selbst wird je Semantik nicht als normale Nutzdatei synchronisiert; auf jedem Gerät konsistent verwalten.

> [!warning]
> Neu ignorierte bereits synchronisierte Dateien verschwinden nicht zwingend automatisch überall. Vor Policyänderung Testordner und Clusterzustand prüfen.

Nicht synchronisieren:

- Datenbankdateien im laufenden Betrieb
- VM-Diskimages ohne Konsistenzstrategie
- Browserprofile bei paralleler Nutzung
- Unix-Sockets/Device Nodes
- Cloudmount-Caches
- Syncthing-eigene Config/DB im selben bidirektionalen Ordner

## Dateirechte, Ownership und Metadaten

Syncthing synchronisiert Dateiinhalt und bestimmte Metadaten, aber nicht als universeller POSIX-/NTFS-ACL-Replikator.

- UID/GID/Owner werden nicht wie rsync-Backup garantiert übertragen.
- POSIX Permissions können synchronisiert oder mit „Ignore Permissions“ ignoriert werden.
- ACLs, xattrs, SELinux-Kontexte, Hardlinks und Sparse-Semantik sind nicht vollständiger Backupfokus.
- Windows und Unix unterscheiden Case, verbotene Zeichen und Executable Bit.
- Symlinkbehandlung plattform-/versionsabhängig.

Für Systembackups `rsync -aHAX`, ZFS/Btrfs send oder Backupsoftware verwenden.

`umask` und Dienstbenutzer bestimmen neue Dateirechte. Gemeinsame Gruppen:

```bash
sudo usermod -aG shared syncthing
sudo chgrp -R shared /srv/share
sudo chmod 2770 /srv/share
setfacl -m d:g:shared:rwx /srv/share
```

Syncthing-Service neu anmelden/restarten, damit Gruppen gelten.

## Konflikte und Override/Revert

Bei gleichzeitiger Änderung entstehen Conflict Copies, typischer Name enthält `sync-conflict`, Zeit und Gerätekennung.

Finden:

```bash
find /pfad -type f -name '*sync-conflict*' -print
```

Vorgehen:

1. beide Versionen sichern.
2. Inhalt vergleichen.
3. gewünschte Version unter Originalnamen herstellen.
4. Konfliktdatei nach Freigabe löschen/archivieren.
5. Ursache: parallele Bearbeitung, Uhr, App-Locking, Offlinegerät.

Send Only → **Override Changes**:

- setzt Cluster auf lokalen Stand
- kann Remoteänderungen überschreiben
- vorher Remoteabweichungen sichern

Receive Only → **Revert Local Changes**:

- verwirft lokale Abweichungen zugunsten Cluster
- vorher lokale Dateien sichern

> [!danger]
> Override/Revert sind destruktive Richtungsentscheidungen, keine harmlose Statusbereinigung.

## Discovery, Relays und Ports

Typische Verbindungen je Version/Config:

- TCP Sync: 22000
- QUIC/UDP Sync: 22000
- Local Discovery: UDP 21027
- GUI: 8384 lokal

Effektiv prüfen:

```bash
ss -tulpn | grep syncthing
syncthing cli show connections
```

Firewalls:

- direkte eingehende Verbindung verbessert Performance
- NAT Traversal/UPnP optional
- Relay als Fallback
- Global Discovery verrät Device-ID-/Adressmetadaten an Discoveryinfrastruktur

Privacy-Modus:

- Global Discovery deaktivieren
- Relays deaktivieren
- statische Adressen/VPN
- Local Discovery nur intern

Dann Erreichbarkeit selbst sicherstellen.

Verbindungsadressen:

```text
dynamic
tcp://host:22000
quic://host:22000
relay://...
```

## GUI, API und CLI

GUI-Authentisierung sofort setzen, insbesondere bei nicht-Loopback Binding.

HTTPS für GUI aktivieren oder Reverse Proxy/VPN verwenden. Direkte WAN-Exposition vermeiden.

CLI:

```bash
syncthing cli show system
syncthing cli show connections
syncthing cli show pending devices
syncthing cli show pending folders
```

CLI-Syntax entwickelt sich; `syncthing cli --help`.

REST API:

```bash
curl -H 'X-API-Key: SECRET' http://127.0.0.1:8384/rest/system/status
```

API-Key als Secret, nicht im Skript/History. Environment/Secret File:

```bash
curl -H "X-API-Key: $(cat /run/secrets/syncthing-api)" ...
```

Events/API können Monitoring und Automatisierung ermöglichen; Rate/Fehler behandeln.

## Systemd und Mehrbenutzerbetrieb

User-Service:

```bash
systemctl --user enable --now syncthing.service
systemctl --user status syncthing.service
journalctl --user -u syncthing -b
```

Linger für Headless User, damit ohne Login läuft:

```bash
sudo loginctl enable-linger alice
```

Systeminstanz je Distribution:

```bash
sudo systemctl enable --now syncthing@alice.service
sudo systemctl status syncthing@alice.service
```

Nicht User- und Systeminstanz für denselben Configpfad gleichzeitig starten.

Dedizierter Nutzer:

```bash
sudo useradd --system --create-home --home-dir /var/lib/syncthing syncthing
```

Datenrechte explizit. Home/Config nicht auf zu synchronisierenden Folder legen.

Container:

- Config persistent mounten
- UID/GID angleichen
- Ports/Discovery/Hostnetwork bewusst
- nicht bei jedem Start neue Device Identity erzeugen
- Datenvolume separat

## Performance und Datenbank

Faktoren:

- Zahl/Größe der Dateien
- Hashing/CPU
- Storage-Latenz
- Watcher versus Rescan
- Netzwerk/Relay
- Verschlüsselung
- Concurrent Writes
- Datenbankgröße

GUI zeigt Scan-/Syncstatus. Logs:

```bash
journalctl --user -u syncthing -f
```

Viele kleine Dateien sind Metadatenlastig. Rescan nicht extrem kurz setzen; File Watcher nutzen, wo zuverlässig.

Minimum Free Disk Space konfigurieren, damit Folder vor kritischem Vollstand stoppt.

Datenbank neu aufbauen – nur nach Backup/Verständnis:

```bash
syncthing --reset-database
```

Dies kann vollständigen Rescan/Indexaustausch auslösen. Nicht mit `--reset-deltas`/anderen Optionen blind experimentieren.

Profiling/Debug nur temporär und datenschutzbewusst.

## Sicherheit

- Device IDs prüfen, unbekannte Anfragen ablehnen.
- GUI-User/Passwort und HTTPS/VPN.
- GUI nicht WAN-exponieren.
- API-Key schützen/rotieren.
- Dienst nicht als Root.
- Folderrechte minimal.
- Introducer nur vertrauenswürdig.
- Versionierung plus getrenntes Backup.
- UPnP/NAT Traversal nur nach Netzwerkpolicy.
- Discovery/Relay-Privacy bewusst.
- Updates zeitnah und release notes.
- `.stignore` gegen Secrets/Buildartefakte.
- Untrusted/Receive Encrypted nur mit getesteter Schlüsselstrategie.
- Konfigurationsbackup enthält private Geräteschlüssel und API-Key.

## Backup und Migration

Sichern:

1. Syncthing stoppen oder konsistenten Configsnapshot erstellen.
2. Configverzeichnis aus `syncthing paths`.
3. Datenordner.
4. `.stversions`.
5. `.stignore`.
6. Dienstdefinitionen/Firewall.

```bash
systemctl --user stop syncthing
syncthing paths
rsync -a ~/.local/state/syncthing/ /backup/syncthing-state/   # Pfad nur Beispiel, tatsächlichen Output nutzen
systemctl --user start syncthing
```

Migration mit gleicher Identität:

- Config/Keys geschützt auf neuen Host
- alten Host nicht gleichzeitig mit identischer Device Identity betreiben
- Pfade anpassen
- Rechte prüfen
- Partnerverbindungen testen

Neue Identität bedeutet auf allen Geräten neues Device hinzufügen und Freigaben bestätigen.

## Diagnose

Status:

```bash
syncthing --version
syncthing paths
syncthing cli show system
syncthing cli show connections
```

Ports:

```bash
ss -tulpn | grep -E '22000|21027|8384'
```

Logs:

```bash
journalctl --user -u syncthing -b --no-pager
```

Dateirechte:

```bash
namei -l /srv/sync/folder
getfacl /srv/sync/folder
```

Uhr:

```bash
timedatectl status
```

Häufige Zustände:

| Zustand | Bedeutung/Prüfung |
|---|---|
| Disconnected | Adresse, Firewall, Discovery, Relay, Device Pause |
| Out of Sync | Dateien fehlen/abweichen; Pull Errors ansehen |
| Local Additions (Receive Only) | lokale Änderungen; sichern, dann Revert entscheiden |
| Override Needed (Send Only) | Remoteänderungen; sichern, dann Override entscheiden |
| Folder Stopped | Pfad/Rechte/Freiplatz/Markerfehler |
| Failed Items | Dateiname, Rechte, Disk, Lock, Case Conflict |
| Scan läuft ewig | sehr viele Dateien, IO, DB, rekursive Änderungen |

Markerdatei `.stfolder` zeigt korrektes Folderroot. Fehlt sie, stoppt Syncthing zum Schutz vor leerem/unmountetem Pfad. Ursache beheben, nicht nur Schutz blind umgehen.

Diagnosereihenfolge:

1. Prozess/Version/Configpfad.
2. Folderpfad und `.stfolder`/Mount.
3. Rechte/Freiplatz.
4. Verbindung zum Peer.
5. GUI „Failed Items“/Logs.
6. Ignore-/Case-/Zeichenkonflikte.
7. Clock und Versionen.
8. erst zuletzt Datenbankreset.

## Abnahmecheckliste

```text
[ ] Device IDs unabhängig geprüft
[ ] GUI/Auth/TLS geschützt
[ ] Folder Type bewusst gewählt
[ ] Versionierung aktiviert und Restore getestet
[ ] separates Backup vorhanden
[ ] Ignore Patterns dokumentiert
[ ] Rechte/UID/GID plattformübergreifend geklärt
[ ] Ports/Discovery/Relay nach Policy
[ ] Minimum Free Space gesetzt
[ ] Config/Identity gesichert
[ ] Konflikt- und Ransomwareprozess dokumentiert
```

## Quellen
- [Syncthing Documentation](https://docs.syncthing.net/)
- [Syncthing Configuration](https://docs.syncthing.net/users/config.html)
- [File Versioning](https://docs.syncthing.net/users/versioning.html)
- [Ignoring Files](https://docs.syncthing.net/users/ignoring.html)
- [Security Principles](https://docs.syncthing.net/users/security.html)

## Verwandte Notizen
- [[rclone – Cheatsheet]]
- [[rsync – Cheatsheet]]
- [[TrueNAS – Cheatsheet]]
- [[POSIX-ACL – Cheatsheet]]
