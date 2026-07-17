---
title: "OPNsense – Premium-Spickzettel"
aliases: ["OPNsense Firewall Cheatsheet", "OPNsense Administration", "OPNsense Routing NAT"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [opnsense, firewall, freebsd, routing, nat, vpn]
source: "https://docs.opnsense.org/"
---

# OPNsense – Premium-Spickzettel

> [!abstract] Zweck
> Betriebsreferenz für OPNsense: Erstsetup, Interfaces/VLAN, Aliases, Firewall, Destination-/Source-NAT, DHCP/DNS, Multi-WAN, VPN, Zertifikate, Plugins, Updates, Backups, HA, API/CLI, Härtung und Diagnose.

> [!warning] Versionsabhängige Menünamen
> OPNsense entwickelt Teile der Firewall-/NAT-Oberfläche weiter. Je Release können „Port Forward“ als „Destination NAT“ und weitere Seiten neu benannt oder migriert sein. Vor Änderungen die Dokumentation des installierten Releasezweigs prüfen.

> [!danger] Zugriff absichern
> Vor Interface-, VLAN-, Gateway-, Firewall- oder HA-Änderungen Backup exportieren und Konsolenzugang sicherstellen. Eine zweite GUI-/SSH-Sitzung offen lassen und Managementregeln zuerst testen.

## Inhalt

- [[#Grundmodell und Erstsetup]]
- [[#Interfaces, VLAN und LAGG]]
- [[#Aliases]]
- [[#Firewallregeln]]
- [[#NAT]]
- [[#DHCP, Router Advertisements und DNS]]
- [[#Routing und Multi-WAN]]
- [[#VPN]]
- [[#Benutzer und Zertifikate]]
- [[#Plugins und Intrusion Detection]]
- [[#Updates]]
- [[#Backup und Restore]]
- [[#High Availability]]
- [[#CLI, API und Diagnose]]
- [[#Härtung]]
- [[#Fehler-Playbooks]]

## Grundmodell und Erstsetup

OPNsense basiert auf FreeBSD und nutzt unter anderem PF. Funktionen:

- stateful Firewall
- Routing/NAT
- DHCP/DNS/RA
- VLAN/LAGG/Bridges
- Multi-WAN
- IPsec/OpenVPN/WireGuard-Optionen
- IDS/IPS via Suricata
- Captive Portal
- Plugins/API
- HA mit CARP/pfsync/XMLRPC

Erstsetup:

1. WAN/LAN eindeutig zuweisen.
2. LAN isoliert anschließen.
3. Konsolenmenü für Interface/IP.
4. GUI per HTTPS.
5. Root-/Adminpasswort ändern.
6. General Setup: Hostname, Domain, DNS, NTP, Zeitzone.
7. WAN konfigurieren.
8. Updates/Release Notes.
9. Konfigurationsbackup.
10. Managementzugriff auf LAN/VPN begrenzen.

GUI nicht am WAN freigeben, außer in einer streng begrenzten Notfallarchitektur.

## Interfaces, VLAN und LAGG

```text
Interfaces → Assignments
Interfaces → Other Types → VLAN
Interfaces → Other Types → LAGG
```

Je Interface:

- Enable
- Description
- IPv4/IPv6 Configuration Type
- Upstream Gateway nur bei WAN/Routing
- Block private/bogon passend zur realen Topologie
- MTU/MSS nur begründet
- Promiscuous/Hardware Offloading nur nach Bedarf/Diagnose

VLAN-Ablauf:

1. Parent Interface und Tag.
2. VLAN zuweisen.
3. IP konfigurieren.
4. DHCP/RA.
5. Firewallregeln auf VLAN-Interface.
6. Switchport/Trunk prüfen.

Hardware-Offloading kann bei Virtualisierung/IDS/VLAN je Treiber Probleme verursachen. Nicht pauschal abschalten; Symptome und Plattformdoku prüfen.

## Aliases

```text
Firewall → Aliases
```

Typen je Version:

- Host(s)
- Network(s)
- Port(s)
- MAC
- URL Table/GeoIP je Funktion

Konzept:

```text
MGMT_NETS
DNS_SERVERS
WEB_SERVERS
WEB_PORTS
RFC1918_NETS
```

Aliases mit Beschreibung, Verantwortlichem und Zweck pflegen. Große URL-Aliases benötigen erreichbare Quelle und Updateüberwachung.

## Firewallregeln

```text
Firewall → Rules → [Interface]
```

Grundprinzip:

- Eingangsinterface entscheidet Regelset.
- Reihenfolge von oben nach unten.
- State Tracking erlaubt Antworten.
- Default deny.

Beispiel:

```text
Action: Pass
Interface: MGMT
Direction: in
TCP/IP Version: IPv4+IPv6
Protocol: TCP
Source: MGMT_NETS
Destination: This Firewall
Destination Port: HTTPS
Description: OPNsense GUI aus Managementnetz
```

`Quick`/Floating/Automationsregeln nur mit Verständnis der Auswertungsreihenfolge.

Live View:

```text
Firewall → Log Files → Live View
```

Regel-ID/Label aus Log zur verantwortlichen Regel verfolgen.

States:

```text
Firewall → Diagnostics → States
```

Nach Policyänderung können alte States fortbestehen. Nur betroffene States löschen.

## NAT

### Destination NAT / Port Forward

Je Release:

```text
Firewall → NAT → Destination NAT (Port Forward)
```

Beispiel:

```text
Interface: WAN
TCP/IP: IPv4
Protocol: TCP
Destination: WAN address
Destination Port: 443
Redirect/Translation Target: 10.10.20.10
Target Port: 443
```

Neuere UI kann Regelzuordnung anders handhaben; Firewallregel separat kontrollieren.

### Source NAT / Outbound NAT

Modi/Seiten können migriert werden. Übliche Konzepte:

- automatic
- hybrid
- manual

Eigene Regeln für:

- zusätzliche interne Netze
- VPN-Ausnahmen
- feste Quelladresse/VIP
- Multi-WAN

Reihenfolge und Interface wichtig.

### 1:1 NAT und Virtual IPs

```text
Firewall → Virtual IPs
Firewall → NAT
```

VIP-Typen haben unterschiedliche Layer-2-/HA-Semantik. Für CARP-HA NAT auf VIP statt Node-Adresse.

> [!important]
> NAT übersetzt, Firewall erlaubt/blockiert. Beides getrennt prüfen.

Split DNS ist für interne Zugriffe auf veröffentlichte Dienste meist sauberer als NAT Reflection.

## DHCP, Router Advertisements und DNS

Je Release/Plugin kann Kea DHCP anstelle älterer ISC-DHCP-Seiten verwendet werden. Vor Migration Lease-/HA-/Optionenkompatibilität prüfen.

Planung:

- Pools
- statische Mappings
- Gateway/DNS/NTP/Domain
- Leasezeit
- VLAN-spezifische Optionen
- DHCPv6 versus SLAAC
- Router Advertisements

DNS Resolver Unbound:

```text
Services → Unbound DNS
```

Funktionen:

- Interfaces/ACLs
- DNSSEC
- Host/Domain Overrides
- Forwarding/DoT je Setup
- Blocklists je Funktion/Plugin
- DHCP-Registrierung

Diagnose:

```text
Interfaces → Diagnostics → DNS Lookup
Services/Unbound → Log File
```

Shell:

```sh
dril example.org
sockstat -4 -6 -l | grep ':53'
configctl unbound check
```

Konkrete `configctl`-Aktionen versionsabhängig; `configctl -h`/GUI verwenden.

## Routing und Multi-WAN

```text
System → Gateways → Configuration
System → Routes → Configuration
```

Gateway Monitoring:

- Monitor-IP pro Uplink erreichbar
- Latenz/Loss-Schwellen
- Far Gateway nur bei berechtigter Topologie
- Gateway nicht als „default“ markieren ohne Design

Gateway Groups:

```text
System → Gateways → Group
```

Tiers/Trigger für Failover/Load Balancing. Policy Routing über Firewallregel-Gateway.

No-Policy-Routing-Regeln für lokale/VPN/private Ziele vor Internetregeln setzen.

Asymmetrisches Routing und Sticky Connections können Multi-WAN-Verhalten beeinflussen. States bei Test kontrolliert zurücksetzen.

## VPN

Typisch:

- IPsec
- OpenVPN
- WireGuard über integrierte/Pluginfunktion je Release

Checkliste:

```text
[ ] Zeit/NTP
[ ] WAN-Port/Firewall
[ ] Peer/Auth/Zertifikat
[ ] Tunnelnetze überschneidungsfrei
[ ] Regeln auf VPN-Interface
[ ] Routen/Rückrouten
[ ] Source NAT/No-NAT
[ ] DNS
[ ] MTU/MSS
[ ] Clientberechtigung
```

Status/Logs unter VPN- und System-Logseiten des jeweiligen Dienstes.

WireGuard:

- Instance/Peer
- Allowed IPs sind Routing plus Policykonzept
- Interfacezuweisung ermöglicht klare Regeln
- Endpoint/Keepalive bei NAT
- keine Netzüberlappung

IPsec:

- IKE/Child SA getrennt analysieren
- Traffic Selectors
- VTI/route-based versus policy-based
- Phase-2-Regeln/Routen

## Benutzer und Zertifikate

```text
System → Access → Users/Groups
System → Trust → Authorities/Certificates
```

- individuelle Konten
- Gruppen/Privileges minimal
- TOTP/MFA
- zentrale Authentisierung LDAP/RADIUS nur mit TLS/CA-Prüfung
- GUI-/VPN-Zertifikate mit korrekten SANs
- Ablauf/Widerruf überwachen
- Private Keys in Backups schützen

Rootzugang nur für notwendige Administration; tägliche Nutzung mit delegierten Konten, soweit praktikabel.

## Plugins und Intrusion Detection

```text
System → Firmware → Plugins
Services → Intrusion Detection
```

Plugins:

- nur gepflegte und benötigte
- vor Major Upgrade Kompatibilität prüfen
- Konfiguration/Abhängigkeiten dokumentieren

Suricata IDS/IPS:

- Interface und Home Networks korrekt
- IDS beobachten, IPS blockiert aktiv
- Netmap/Offloading/Hardwarekompatibilität
- Rule Feeds und Updates
- False Positives mit klaren Suppressions
- Performance/CPU/RAM
- TLS-Inhalte sind ohne Entschlüsselung nicht sichtbar

> [!warning]
> IPS nicht direkt mit maximalem Regelset in Produktion einschalten. Erst IDS/Baseline, dann gezielte Policies und kontrollierte Aktivierung.

## Updates

OPNsense verwendet halbjährliche Major-Serien plus Updates. Vorher:

1. Release Notes des Zielpfads.
2. vollständiges Backup.
3. Plugins/Hardware/Filesystem prüfen.
4. HA-Reihenfolge.
5. Konsole.
6. Wartungsfenster.
7. Health/Audit.

```text
System → Firmware → Status/Updates
```

Shellaktionen existieren, aber GUI/Updater bevorzugen. Keine generischen FreeBSD-Upgrades außerhalb OPNsense-Mechanismen.

## Backup und Restore

```text
System → Configuration → Backups
```

Optionen je Version:

- Download der Konfiguration
- verschlüsselter Export
- historische Revisionen
- Remote Backup/Nextcloud je Funktion/Plugin
- Bereiche selektiv wiederherstellen

Backup enthält sensible Secrets. Stark verschlüsseln, Zugriff begrenzen, Offlinekopie und Restoretest.

Vor großen Änderungen Revision/Backup markieren. Nach Restore Interface-Mapping und Version/Plugins prüfen.

## High Availability

Bausteine:

- CARP VIPs
- pfsync States
- XMLRPC-Konfigurationssync
- dediziertes Sync-Interface

Checkliste:

```text
[ ] identische Version/Plugins
[ ] eindeutige Node-IPs
[ ] CARP VIPs
[ ] pfsync geschützt
[ ] XMLRPC Sync nur Partner
[ ] NAT nutzt VIP
[ ] DHCP/DNS-HA geplant
[ ] Switch erlaubt CARP
[ ] Failover/Rückfall getestet
```

CARP-Demotion/Status über GUI und `ifconfig`/Systemdiagnose prüfen.

## CLI, API und Diagnose

Konsole bietet Recovery-/Interfaceoptionen. Shell:

```sh
ifconfig -a
netstat -rn
route -n get 8.8.8.8
arp -an
ndp -an
pfctl -sr
pfctl -sn
pfctl -ss
pfctl -si
pftop
sockstat -4 -6 -l
tcpdump -ni <interface>
```

OPNsense-spezifisch:

```sh
configctl -h
pluginctl -s
```

Aktionen/Parameter versionsabhängig und nicht blind aus fremden Releases übernehmen.

API:

- API Key/Secret pro Benutzer
- minimale Privileges
- TLS validieren
- Secrets nicht in Git/CLI-History
- idempotente Automatisierung
- vor Änderung Backup und GET/Export

GUI-Diagnosebereiche:

```text
Interfaces → Diagnostics
Firewall → Diagnostics
System → Log Files
Reporting → Health
```

Packet Capture:

- richtiges Interface
- Host/Portfilter
- intern/extern parallel bei NAT
- PCAP sensibel behandeln

PF Live Log:

```sh
tcpdump -n -e -ttt -i pflog0
```

## Härtung

- GUI nur Management/VPN, nicht WAN.
- vertrauenswürdiges HTTPS-Zertifikat.
- individuelle Konten, MFA, minimale Rechte.
- SSH aus oder Keyauth/Quellnetz.
- API-Keys rotieren und begrenzen.
- Plugins minimieren.
- UPnP aus oder auf Geräte/Ports begrenzen.
- DNS-/NTP-/Syslog-Infrastruktur absichern.
- Backups verschlüsseln.
- Regelbeschreibungen/Aliases/Changeprozess.
- IDS/IPS kontrolliert und überwacht.
- WebGUI-Listen-/Anti-Lockout-Regeln verstehen.
- Adminzugriff auch bei WAN-Ausfall über Managementpfad.
- regelmäßige Update- und Restoreübungen.

## Fehler-Playbooks

### Kein Internet

1. Client IP/Gateway/DNS.
2. Interface-Regel.
3. Firewall selbst pingt Gateway/externe IP.
4. Gateway Status/Monitoring.
5. Source NAT.
6. Unbound/DNS.
7. Capture LAN/WAN.

### Destination NAT funktioniert nicht

1. WAN öffentlich/kein CGNAT.
2. extern testen.
3. WAN-Capture sieht SYN.
4. Destination-NAT-Regel trifft.
5. separate Firewallregel.
6. LAN-Capture.
7. interner Listener/Hostfirewall/Gateway.
8. State/Live Log.

### Regel scheint ignoriert

1. eingehendes Interface korrekt?
2. Reihenfolge/Quick/Floating?
3. IP-Version/Protokoll/Port?
4. Aliasinhalt?
5. bestehender State?
6. NAT verändert Ziel vor/nach Regelphase?
7. Live Log Label/Rule ID.

### VPN ohne internen Zugriff

1. Interfacezuweisung/Regeln.
2. Allowed IPs/Traffic Selectors.
3. Rückroute.
4. Source NAT/No-NAT.
5. DNS.
6. Überschneidung.
7. MTU.
8. Capture Tunnel/LAN.

### Updateproblem

1. Release Notes/Repositories/Connectivity/DNS/Zeit.
2. Plugins.
3. freien Speicher/ZFS/UFS.
4. Health Audit.
5. Logs.
6. nicht mit generischem `pkg upgrade` improvisieren.
7. Backup/Konsole/Rollback.

## Quellen
- [OPNsense Documentation](https://docs.opnsense.org/)
- [OPNsense Firewall Manual](https://docs.opnsense.org/manual/firewall.html)
- [OPNsense NAT Manual](https://docs.opnsense.org/manual/nat.html)
- [OPNsense Releases](https://docs.opnsense.org/releases.html)

## Verwandte Notizen
- [[pfSense – Premium-Spickzettel]]
- [[BSD-Netzwerk – Premium-Spickzettel]]
- [[Wireshark – Premium-Spickzettel]]
- [[TrueNAS – Premium-Spickzettel]]
