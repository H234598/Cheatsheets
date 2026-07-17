---
title: "TrueNAS – Premium-Spickzettel"
aliases: ["TrueNAS SCALE Cheatsheet", "TrueNAS Administration", "ZFS NAS"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [truenas, zfs, nas, smb, nfs, replication, backup]
source: "https://www.truenas.com/docs/"
---

# TrueNAS – Premium-Spickzettel

> [!abstract] Zweck
> Sehr ausführliche TrueNAS-Betriebsreferenz für SCALE/CORE-nahe Konzepte: Hardware, Pools/vdevs, Datasets, ACLs, SMB/NFS/iSCSI, Snapshots, Replication, Cloud Sync, Scrubs/SMART, Apps/VMs, Updates, Backups, Recovery und Härtung.

> [!danger] TrueNAS über die Managementschicht administrieren
> ZFS-, Netzwerk-, Paket- und Dienstkonfiguration grundsätzlich über TrueNAS-GUI/API/unterstützte CLI-Mechanismen vornehmen. Manuelle Änderungen im Basissystem können beim Neustart/Update überschrieben werden oder Support und Konsistenz gefährden.

> [!important] Snapshot ≠ Backup
> Snapshots im selben Pool schützen nicht vor Pool-, Hardware-, Standort- oder Administrationsverlust. Replikation auf ein getrenntes System und mindestens eine externe/offline/immutable Kopie vorsehen.

## Inhalt

- [[#Produktvarianten und Grundmodell]]
- [[#Hardwareplanung]]
- [[#Erstsetup und Netzwerk]]
- [[#Disks, Pools und vdevs]]
- [[#Datasets und zvols]]
- [[#Benutzer, Gruppen und ACLs]]
- [[#SMB]]
- [[#NFS]]
- [[#iSCSI]]
- [[#Snapshots]]
- [[#Replication]]
- [[#Cloud Sync und TrueCloud Backup]]
- [[#Scrubs, SMART und Disktausch]]
- [[#Apps, Container und VMs]]
- [[#Verschlüsselung]]
- [[#Updates und Boot Environments]]
- [[#Systemkonfigurationsbackup]]
- [[#Monitoring und Alerts]]
- [[#Härtung]]
- [[#Recovery-Playbooks]]
- [[#Abnahmecheckliste]]

## Produktvarianten und Grundmodell

TrueNAS stellt ZFS über eine Appliance-Verwaltung bereit. UI und Funktionen unterscheiden sich zwischen Releasezweigen und historisch SCALE/CORE. Dieser Spickzettel fokussiert gemeinsame Betriebsprinzipien; Menünamen mit der Dokumentation des installierten Releases abgleichen.

```text
TrueNAS Management/API
├── Netzwerk, Identität, Dienste
├── Pool/vdev-Verwaltung
├── Datasets/zvols/ACLs
├── SMB/NFS/iSCSI
├── Snapshots/Replication/Cloud Tasks
├── Apps/VMs je Edition
└── Monitoring/Alerts/Updates
    ↓
OpenZFS + Betriebssystem
```

Zentrale Begriffe:

| Begriff | Bedeutung |
|---|---|
| Pool | ZFS-Speicherpool |
| vdev | Redundanz-/Performancebaustein des Pools |
| Dataset | ZFS-Dateisystem mit eigenen Properties |
| zvol | blockorientiertes ZFS-Volume |
| Share | SMB-/NFS-/iSCSI-Veröffentlichung |
| Snapshot | read-only Point-in-Time-Zustand |
| Replication Task | ZFS Send/Receive lokal oder remote |
| System Dataset | interne Logs/Metadaten je Konfiguration |

## Hardwareplanung

Prioritäten:

- ECC-RAM empfohlen für Storageintegrität, aber ZFS korrigiert nicht jedes RAM-Problem magisch.
- HBA/JBOD statt undurchsichtigem Hardware-RAID.
- Disks direkt sichtbar mit Seriennummer/SMART.
- USV und geordnetes Shutdown.
- redundante, überwachte Kühlung/Netzteile je Kritikalität.
- Bootmedium getrennt vom Datenpool; Bootmirror erwägen.
- Netzwerk 1/2.5/10/25+ GbE nach Workload.
- genug RAM für ARC und Apps/VMs.
- SLOG nur mit Power-Loss Protection und Sync-Workload.
- Special vdev redundant und kapazitätsgeplant.

> [!danger]
> USB-Sticks, Consumer-USB-Gehäuse, Port-Multiplier und nicht transparente RAID-Controller sind für kritische Pools riskant. Fehlerweitergabe, Seriennummern, TRIM und stabile Verbindungen prüfen.

Diskgrößen/Topologie:

- vdevs möglichst aus gleich großen Disks.
- Mirror versus RAIDZ2 nach IOPS, Kapazität, Resilver und Ausfalltoleranz.
- Hot Spare ersetzt kein aktives Monitoring und kein Backup.
- Expansionmöglichkeiten vor Kauf planen.
- Pool unter hoher Auslastung vermeiden; Reserve lassen.

## Erstsetup und Netzwerk

1. Konsolenzugang testen.
2. Managementinterface/IP setzen.
3. GUI via HTTPS, Adminpasswort.
4. Hostname/Domain/DNS/Default Route/NTP/Zeitzone.
5. Updates/Release Notes.
6. E-Mail/Alertdienst.
7. Systemkonfigurationsbackup.
8. erst danach Pool/Services.

Netzwerkänderungen remote nur mit Konsole. VLAN/LAGG/Bridge in GUI und Switch abgestimmt.

Management:

- eigenes VLAN empfohlen
- GUI/SSH nur Management/VPN
- vertrauenswürdiges Zertifikat
- keine Default-Freigaben ins Internet

LAGG/LACP benötigt passende Switchseite. SMB Multichannel kann mehrere NICs nutzen, ohne dass LACP immer nötig ist; konkrete Release-/Samba-Doku und Clientunterstützung prüfen.

## Disks, Pools und vdevs

Vor Pool:

```text
Storage → Disks
Storage → Create Pool
```

Prüfen:

- Seriennummer/Größe/Modell
- SMART gesund
- keine versehentlich verwendete Boot-/Backupdisk
- vdev-Layout
- `ashift`/Sektorgröße durch Plattform korrekt
- Spare/Log/Cache/Special nur bewusst

Topologiebeispiele:

```text
2-Way Mirror:   2 Disks, ~50 % Rohkapazität
2×Mirror:       4 Disks, mehr IOPS, flexible Erweiterung
RAIDZ2 6-wide:  6 Disks, 2 Parität
RAIDZ2 8-wide:  8 Disks, Kapazität, längere Rekonstruktion
```

Poolnamen stabil wählen. Root-Dataset nicht direkt für alle Freigaben verwenden; eigene Child Datasets pro Zweck.

Nicht:

- Hardware-RAID-LUN als einziger ZFS-vdev ohne klare Architektur
- unterschiedlich kritische Daten im selben Dataset
- einzelne Cache/Special/Log-Geräte ungespiegelt, wenn Verlust kritisch
- Pool bis 100 % füllen
- unbekannte `zpool`-CLI-Manipulation außerhalb GUI

## Datasets und zvols

Pro Workload Dataset:

```text
tank/smb/team
tank/smb/homes
tank/nfs/projects
tank/apps
tank/vm
tank/backups
```

Wichtige Properties:

- Share Type/Preset
- Compression
- Record Size
- Atime
- Sync
- Quota/Refquota
- Reservation
- ACL Type/ACL Mode
- Case Sensitivity
- Encryption
- Snapshot Directory

Faustregeln:

- `compression=zstd`/empfohlener Default meist sinnvoll.
- Recordsize für allgemeine Files standardnah; große Medien größer; DB/VM gezielt.
- `sync=disabled` nicht als Performancehack für kritische Daten.
- Deduplizierung nur nach belastbarer Messung und RAM-/Recoverydesign.
- Case Sensitivity vor SMB-/Appbetrieb wählen; spätere Änderung komplex.

zvol für iSCSI/VM-Blockstorage:

- volblocksize vor Erstellung/Belegung passend.
- Sparse versus reserviert bewusst.
- Snapshot/Replication auf Blockebene.
- nicht gleichzeitig als Filesystem und Blockdevice mehreren Hosts ohne Cluster-FS.

## Benutzer, Gruppen und ACLs

Identitätsquellen:

- lokale Benutzer/Gruppen
- Active Directory
- LDAP/IdM je Release

Vor Share:

1. Identitätsquelle stabil.
2. Uhr/DNS korrekt.
3. Dataset ACL Type passend.
4. Owner/User/Group.
5. ACL-Einträge minimal.
6. Testuser statt Admin.

SMB nutzt NFSv4-/Windows-nahe ACLs je TrueNAS-Preset. Nicht parallel POSIX-Modi/ACLs per Shell „reparieren“, wenn GUI/SMB sie verwaltet.

ACL Manager:

- Preset als Ausgangspunkt
- Vererbung verstehen
- „Apply recursively“ auf großen Bäumen kann lange dauern und Berechtigungen überschreiben
- Traverse/Execute auf Elternpfaden
- Eigentümerwechsel versus ACL
- Backup der ACLs/Replication testen

Multiprotocol SMB+NFS auf demselben Dataset nur mit klarer Identity-, ACL- und Lockingarchitektur.

## SMB

```text
Shares → SMB
System Settings/Services → SMB
```

Einrichtung:

1. Dataset mit SMB-Preset.
2. ACL/Owner.
3. Share Path/Name/Purpose.
4. SMB-Dienst starten/autostart.
5. Firewall/Netz.
6. Test mit normalem Benutzer.

Sicherheit:

- SMB1 deaktiviert lassen.
- Guest nur bewusst und isoliert.
- SMB Signing/Encryption je Policy.
- Admin Shares/Shadow Copies/Audit je Bedarf.
- keine Home- und allgemeine Sharepfade überlappen.
- AD-DNS/NTP zwingend korrekt.

Windows-Test:

```powershell
Test-NetConnection truenas.example.org -Port 445
Get-SmbConnection
net use Z: \\truenas\team
```

Linux:

```bash
smbclient -L //truenas -U alice
smbclient //truenas/team -U alice
```

Shadow Copies basieren auf ZFS-Snapshots. Periodic Snapshot Task und Shareeinstellung/Releasefunktion abstimmen. Retention und Platz überwachen.

Fehler:

- User wird nicht gefunden → AD/LDAP/DNS/Clock.
- Access denied → Dataset ACL, Share ACL, Gruppen, Traverse.
- Datei gesperrt → SMB Locks/Client/App.
- langsame Auflistung → Millionen Dateien, Antivirus, ACL, DNS, SMB signing/encryption, Storage.

## NFS

```text
Shares → NFS
Services → NFS
```

Planen:

- NFSv4 bevorzugt, wenn Umgebung passt.
- Netz/Hosts begrenzen.
- `maproot`/`mapall` nur bewusst.
- Kerberos für starke Authentisierung.
- UID/GID-Konsistenz.
- Dataset ACL/POSIX-Modus.

Linux-Test:

```bash
showmount -e truenas
sudo mount -t nfs4 truenas:/mnt/tank/nfs/projects /mnt/projects
nfsstat -m
```

NFSv4-Exportpfade können je TrueNAS-Konfiguration anders erscheinen; GUI-Hinweis nutzen.

VM-Datastores/DBs benötigen Sync-/NFS-/SLOG- und Clientmount-Planung. `async`/Sync-Deaktivierung kann Datenhaltbarkeit brechen.

## iSCSI

Bausteine:

```text
Portal → Initiator Group → Target → Extent → Associated Target
```

Extent als zvol oder File; zvol bevorzugt für Blocksemantik.

Planen:

- eigenes Storage-Netz/VLAN
- CHAP/Mutual CHAP je Policy
- Multipath/MPIO
- Blockgröße/zvol Volblocksize
- LUN-ID stabil
- eine LUN nicht mehreren Hosts beschreibbar geben, außer Cluster-FS/Clusterkoordination
- Snapshot/Quiesce

Windows:

```powershell
Get-IscsiTargetPortal
Get-IscsiSession
Get-Disk
```

Linux:

```bash
iscsiadm -m discovery -t sendtargets -p truenas
iscsiadm -m node --login
multipath -ll
```

## Snapshots

```text
Data Protection → Periodic Snapshot Tasks
Datasets → Snapshots
```

Namensschema und Retention:

```text
auto-%Y-%m-%d_%H-%M
hourly 48h
daily 30d
monthly 12m
```

An Datenänderungsrate/Kapazität anpassen.

Snapshots:

- atomarer ZFS-Zustand des Datasets
- recursive Option für Child Datasets
- VM-/Datenbankkonsistenz separat
- halten gelöschte/geänderte Blöcke
- Windows Shadow Copies möglich

Rollback ist destruktiv für neuere Änderungen/Snapshots. Für Einzeldateirestore Snapshot browsen/clone oder Restorefunktion nutzen, statt kompletten Dataset-Rollback.

Snapshotaufgaben überwachen und alte manuelle Snapshots nicht vergessen.

## Replication

```text
Data Protection → Replication Tasks
Credentials → Backup Credentials → SSH Connections/Keypairs
```

Lokal:

- separates Dataset/Pool auf demselben System
- schützt vor manchen logischen Fehlern, nicht System/Standort

Remote:

- zweites TrueNAS/ZFS-System
- Push oder Pull
- SSH-Verbindung/Key
- Snapshot Naming Schema
- recursive/properties/encryption
- Schedule und Retention

Checkliste:

```text
[ ] Ziel-Dataset vorhanden
[ ] Quell-Snapshots konsistent benannt
[ ] SSH-Key/Hostkey geprüft
[ ] Least-Privilege-/sudo-Design
[ ] Bandbreite/Zeitraum
[ ] Ziel-Retention
[ ] Verschlüsselung/Raw Send
[ ] Ziel nicht normal beschreibbar
[ ] Restore aus Replikat getestet
```

> [!danger]
> Force-/Rollbackoptionen können Ziel-Snapshots oder lokale Änderungen entfernen. Ziel als Replikat behandeln und nicht gleichzeitig produktiv beschreiben.

Encrypted Replication:

- raw send kann Daten verschlüsselt replizieren
- Schlüssel/Passphrase getrennt sichern
- Zielunlock/Restore testen
- Property-/Root-Enkryptionsemantik beachten

## Cloud Sync und TrueCloud Backup

Rclone-basierte Cloud Sync Tasks je Release:

```text
Data Protection → Cloud Sync Tasks
Credentials → Backup Credentials → Cloud Credentials
```

Richtung:

- Push/Pull
- Copy/Sync/Move

`Sync` kann Ziel löschen; Dry Run/Testdataset und Provider-Versioning/Object Lock.

Cloud ist nicht automatisch vertraulich: clientseitige Verschlüsselung/TrueCloud-Funktion je Release prüfen. Credentials minimal und rotierbar.

TrueCloud Backup/modernere Funktionen können verschlüsselte, versionierte Backups bieten; Release-Dokumentation und Restoreworkflow prüfen.

## Scrubs, SMART und Disktausch

Scrub Tasks:

```text
Data Protection → Scrub Tasks
```

Regelmäßig, Ergebnisse/Alerts prüfen.

SMART Tests:

```text
Data Protection → S.M.A.R.T. Tests
Storage → Disks
```

Typisch:

- Short häufiger
- Long regelmäßig versetzt
- nicht alle Disks gleichzeitig unter Last

SMART ist nicht genug; ZFS CKSUM/READ/WRITE, Controller und Kabel einbeziehen.

Disktausch:

1. Alert und `zpool status`/GUI Topology.
2. Seriennummer, Slot, Enclosure identifizieren.
3. richtige Disk offline, falls nötig.
4. physisch ersetzen/hot swap nach Hardware.
5. **Replace** in GUI.
6. Resilver überwachen.
7. SMART/Fehler/Poolstatus nach Abschluss.
8. alte Disk sicher löschen/RMA.

> [!danger]
> Nie nur nach `/dev/sdX` ziehen; Namen können wechseln. Seriennummer/Enclosure-Slot/WWN und Pooltopologie bestätigen.

Poolstatus Shell read-only zur Diagnose:

```bash
zpool status -v
zpool iostat -v 5
```

Änderungen über GUI.

## Apps, Container und VMs

Je SCALE-Release unterscheiden sich Appplattform und UI. Grundregeln:

- Apps/VM-Datasets getrennt.
- Host Paths und ACLs bewusst.
- Daten nicht nur im ephemeral Containerlayer.
- Appkonfiguration und persistente Daten sichern.
- Snapshots allein können laufende DB inkonsistent erfassen.
- Ressourcenlimits.
- Netz/Ingress/TLS/Secrets.
- Update von App und TrueNAS getrennt planen.
- keine Drittanbieter-Kataloge/Images ohne Vertrauensprüfung.

VMs:

- zvol/Storage passend
- VirtIO-Treiber
- Snapshots mit Guest-Agent/Shutdown für Konsistenz
- Backup/Restore der VM-Konfiguration plus Disks
- nicht zu viel RAM/CPU der Storagefunktion entziehen

NAS zuerst Storage-Appliance; Apps nicht unkontrolliert zum allgemeinen Server wachsen lassen.

## Verschlüsselung

ZFS Native Encryption auf Datasetebene. Optionen:

- Passphrase
- Keyfile/Hex Key je Release
- automatische/manuel Unlock
- verschlüsselte Replikation

Schlüsselmanagement:

```text
[ ] Schlüssel exportiert
[ ] Passphrase offline dokumentiert
[ ] zweite autorisierte Person/Recoveryprozess
[ ] Reboot-Unlock getestet
[ ] Replikationsziel unlockbar
[ ] Schlüssel nicht nur auf demselben Pool
```

Pool-/Datasetnamen und Größenmetadaten können sichtbar bleiben. Ein laufend entsperrtes System schützt nicht vor kompromittiertem Admin/Host.

SED-Festplattenverschlüsselung und ZFS-Verschlüsselung sind unterschiedliche Ebenen. Recovery/RMA/Boot berücksichtigen.

## Updates und Boot Environments

Vor Update:

1. Release Notes und bekannte Probleme.
2. Systemkonfigurationsbackup plus Secret Seed/Keys, sofern angeboten.
3. Poolzustand gesund.
4. Apps/Plugins/VMs-Kompatibilität.
5. Replikation aktuell.
6. Konsolenzugang.
7. Bootpool frei/gesund.
8. Wartungsfenster.

TrueNAS nutzt Boot Environments/Bootpoolmechanismen je Edition. Ein Bootrollback ersetzt kein Datenpoolbackup und kann neue Config-/Appzustände inkompatibel machen.

Pool Feature Flags nicht sofort nach OS-Update aktivieren; Rückkehr zu älterem Boot/Recoveryziel kann sonst scheitern.

Keine generischen `apt`, `dnf`, `pkg`-Systemupgrades auf Appliancebasis.

## Systemkonfigurationsbackup

```text
System Settings → General → Manage Configuration / Download File
```

Je Release Optionen:

- Config DB
- Secret Seed
- Passwords/Keys
- verschlüsselter Export

Nach wesentlichen Änderungen herunterladen und außerhalb des TrueNAS-Systems verschlüsselt speichern.

Backup enthält:

- Netzwerk
- Benutzer/Services
- Shares/Tasks
- Credentials/Secrets je Option
- nicht automatisch alle Nutzdaten

Restorelabor/Spare Hardware/VM testen. Interfacezuordnung nach Hardwarewechsel prüfen.

## Monitoring und Alerts

Aktivieren:

- E-Mail/OAuth/Alert Service
- SMART
- Scrubresultate
- Pool/Bootpoolstatus
- Kapazität
- Temperaturen
- UPS
- Replikations-/Snapshot-/Cloud-Taskfehler
- Zertifikatsablauf
- AD/LDAP-Zustand
- NTP

Dashboard allein genügt nicht; Alerts extern zustellen.

Kapazitätswarnung früh, nicht erst 95+ %. Snapshot-/Reservation-/Appnutzung aufschlüsseln.

Logs/UI Jobs bei Fehlern öffnen. Shelllogs nur zur Diagnose und versionsspezifisch.

## Härtung

- Management-VLAN/VPN.
- GUI mit vertrauenswürdigem TLS, kein WAN.
- individuelle Admins, MFA falls verfügbar.
- Root/SSH nur nötig; Keys, Quellen begrenzen.
- keine unsicheren Guest-Shares.
- SMB1 aus.
- NFS Exports auf Netze/Hosts, Kerberos je Bedarf.
- iSCSI Storage-Netz/CHAP/Firewall.
- Apps/Plugins minimieren.
- Secrets/Credentials rotieren.
- Konfigurationsbackup verschlüsseln.
- Dataset ACLs least privilege.
- Immutable/offline Backups.
- UPS und sauberes Shutdown.
- regelmäßige Update-/Restore-/Disktauschübungen.
- Auditing/Logs zentral, Datenschutz.

## Recovery-Playbooks

### Pool degraded

1. Alert quittieren, aber nicht löschen.
2. Pooltopologie/Seriennummer/Fehlerart.
3. SMART/Controller/Kabel/Temperatur.
4. Replikation/Backupstatus.
5. bei flapping Link nicht vorschnell mehrere Disks ersetzen.
6. defekte Disk gezielt ersetzen.
7. Resilver überwachen.
8. Scrub/Status nach Abschluss.

### Dataset voll

1. `used`, Snapshots, Quotas, Reservations, Child Datasets.
2. gelöschte offene Dateien/Apps.
3. alte Snapshots nach Retention, nicht blind alle.
4. Replikationsziel/Backups prüfen.
5. Quota/Storage erweitern.
6. Ursache/Alarmgrenzen.

### SMB Access Denied

1. User/AD-Auflösung und Uhr/DNS.
2. Dataset Owner/ACL.
3. Sharepfad und Purpose.
4. Gruppenmitgliedschaften/Token neu anmelden.
5. Parent Traverse.
6. SMB Logs/Audit.
7. Test mit neuem einfachen Ordner, nicht `chmod 777`.

### Replikation fehlgeschlagen

1. letzte erfolgreiche Snapshotbasis.
2. SSH/Hostkey/Key/Sudo.
3. Zielplatz und Read-only/Lock.
4. Naming Schema/Retention.
5. Encryption Keys.
6. Ziel wurde manuell verändert?
7. Force/Rollback erst nach Zielbackup.

### Konfiguration verloren

1. nicht am Datenpool formatieren/neu erstellen.
2. neue/ersetzte Bootinstallation passend.
3. Systemkonfigurationsbackup importieren.
4. Interfacezuordnung prüfen.
5. Pool importieren, nicht neu erstellen.
6. Schlüssel entsperren.
7. Shares/Tasks testen.

### Pool lässt sich nicht importieren

- keine Force-/Rewind-Kommandos blind.
- Disks/Controller/Seriennummern.
- Version/Featureflags.
- read-only Import/Support-/OpenZFS-Plan.
- Blockimages bei Hardwarefehler.
- professionelle Datenrettung bei einzigem Exemplar.

## Abnahmecheckliste

```text
[ ] Pooltopologie und Ersatzstrategie dokumentiert
[ ] Datasets pro Workload mit passenden ACLs/Properties
[ ] Snapshots mit Retention
[ ] Remote-Replikation erfolgreich
[ ] Offline/immutable Backup
[ ] Datei-, Dataset- und Vollsystem-Restore getestet
[ ] SMART/Scrub/Alerts/UPS
[ ] Konfigurationsbackup inkl. Schlüssel
[ ] Management/VPN/TLS/MFA
[ ] SMB/NFS/iSCSI mit normalen Benutzern getestet
[ ] Kapazitäts- und Zertifikatsalarme
[ ] Update-/Boot-/Poolfeature-Rollback verstanden
```

## Quellen
- [TrueNAS Documentation Hub](https://www.truenas.com/docs/)
- [TrueNAS SCALE Data Protection](https://www.truenas.com/docs/scale/dataprotection/)
- [TrueNAS Replication Tasks](https://www.truenas.com/docs/scale/dataprotection/replication/)
- [TrueNAS Datasets](https://www.truenas.com/docs/scale/scaleuireference/datasets/)
- [OpenZFS Documentation](https://openzfs.github.io/openzfs-docs/)

## Verwandte Notizen
- [[ZFS – Premium-Spickzettel]]
- [[pfSense – Premium-Spickzettel]]
- [[OPNsense – Premium-Spickzettel]]
- [[rclone – Premium-Spickzettel]]
- [[Syncthing – Premium-Spickzettel]]
