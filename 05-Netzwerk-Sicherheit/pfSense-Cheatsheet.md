---
title: "pfSense – Cheatsheet"
aliases: ["pfSense Firewall Cheatsheet", "Netgate pfSense", "pfSense Administration"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [pfsense, firewall, freebsd, routing, nat, vpn]
source: "https://docs.netgate.com/pfsense/en/latest/"
---

# pfSense – Cheatsheet

> [!abstract] Zweck
> Betriebsreferenz für pfSense CE/Plus: Erstsetup, Interfaces, Aliases, Firewallregeln, NAT, DHCP/DNS, VLAN, Multi-WAN, VPN, Zertifikate, Updates, Backups, HA, Paketmitschnitt, Härtung und Diagnose.

> [!danger] Firewalländerungen mit Rückfallplan
> Änderungen an WAN/LAN-Zuordnung, Managementregel, NAT, Gateway oder HA können den Zugriff sofort trennen. Vorher Konfigurationsbackup herunterladen, Konsolenzugang prüfen und bestehende Adminsitzung offen lassen.

## Inhalt

- [[#Produkt und Grundmodell]]
- [[#Erstsetup]]
- [[#Interfaces und VLANs]]
- [[#Aliases]]
- [[#Firewallregeln]]
- [[#NAT]]
- [[#DHCP und DNS Resolver]]
- [[#Routing, Gateways und Multi-WAN]]
- [[#VPN]]
- [[#Zertifikate und Benutzer]]
- [[#Updates und Pakete]]
- [[#Backup und Wiederherstellung]]
- [[#High Availability]]
- [[#Monitoring und Diagnose]]
- [[#Härtung]]
- [[#Fehler-Playbooks]]

## Produkt und Grundmodell

pfSense basiert auf FreeBSD und bietet WebGUI plus Konsole für:

- stateful Packet Filter
- Routing und NAT
- DHCP/DNS
- VLAN/Bridge/LAGG
- VPN
- Multi-WAN
- Captive Portal
- Traffic Shaping
- Paketerweiterungen
- High Availability mit CARP/pfsync/XMLRPC-Konfigurationssync

Es existieren pfSense CE und pfSense Plus. Funktionen, Releasezyklen und Support unterscheiden sich. Vor Upgrade die Release Notes des konkret installierten Zweigs lesen.

Version:

```text
Dashboard → System Information
System → Update
```

Konsole/Shell:

```sh
cat /etc/version
uname -a
```

Konfigurationsquelle ist zentral `config.xml`; nicht als gewöhnliche FreeBSD-Konfiguration behandeln.

## Erstsetup

Sicheres Vorgehen:

1. WAN/LAN physisch eindeutig markieren.
2. LAN zunächst isoliert anschließen.
3. Konsolenmenü: Interfaces zuweisen, LAN-IP setzen.
4. GUI per HTTPS öffnen.
5. Adminpasswort ändern.
6. Hostname, Domain, DNS, NTP und Zeitzone.
7. WAN-Typ konfigurieren.
8. Update/Release Notes.
9. Backup herunterladen.
10. Erst dann Regeln/NAT/VPN.

> [!important]
> WebGUI nicht direkt am WAN freigeben. Administration über LAN, Management-VLAN oder VPN; Quellen zusätzlich begrenzen.

## Interfaces und VLANs

Prüfen:

```text
Interfaces → Assignments
Interfaces → [WAN/LAN/OPT]
```

Pro Interface:

- Enable
- Description
- IPv4/IPv6 Configuration Type
- MTU/MSS nur bei begründetem Bedarf
- Block private networks/bogons nur passend zur Topologie
- Upstream Gateway nur auf echten WAN-/Routinginterfaces

VLAN:

```text
Interfaces → Assignments → VLANs
```

Schritte:

1. Parent NIC wählen.
2. VLAN Tag und Beschreibung.
3. VLAN als Interface zuweisen.
4. aktivieren und IP konfigurieren.
5. DHCP/RA optional.
6. Firewallregeln auf dem VLAN-Interface.
7. Switchport Trunk/Tagged VLAN passend.

> [!warning]
> Regeln gelten eingehend auf dem Interface, auf dem Verkehr die Firewall betritt. Eine Regel auf WAN hilft nicht automatisch einem Client aus VLAN100; dessen Regel gehört typischerweise auf VLAN100.

LAGG:

```text
Interfaces → Assignments → LAGGs
```

LACP benötigt Switchkonfiguration; Management nicht ohne Konsole umziehen.

## Aliases

```text
Firewall → Aliases
```

Typen:

- Hosts
- Networks
- Ports
- URLs/URL Tables
- GeoIP je Paket/Funktion

Beispielkonzept:

```text
ADMIN_NETS = 192.0.2.0/24, 2001:db8:100::/64
WEB_SERVERS = 10.10.20.10, 10.10.20.11
WEB_PORTS = 80, 443
```

Vorteile:

- Regeln lesbar
- Änderungen zentral
- weniger Copy/Paste
- leichteres Audit

Aliasnamen stabil halten. URL-Tabellen benötigen erreichbare Quelle, valides Format und sinnvolle Aktualisierung; Ausfallverhalten testen.

## Firewallregeln

```text
Firewall → Rules → [Interface]
```

Grundsatz:

- Regeln werden pro Interface von oben nach unten ausgewertet.
- First Match gewinnt bei normalen Interface-Regeln.
- State Tracking erlaubt Rückverkehr automatisch.
- Default ist block, sofern keine passende Pass-Regel.

Saubere Regel:

```text
Action: Pass
Interface: VLAN100
Protocol: TCP
Source: ADMIN_NETS
Destination: This Firewall
Destination Port: 443
Description: Admin GUI aus Managementnetz
Log: bei kritischer Regel gezielt
```

Reihenfolge:

1. explizite Block-/Spezialregeln, falls nötig
2. Management/DNS/NTP
3. Anwendungsflüsse
4. Internetzugriff
5. implizites Block

Floating Rules nur für bewusst globale/Quick-/Direction-/Queue-Szenarien. Komplexität dokumentieren.

States nach Regeländerungen:

```text
Diagnostics → States
```

Bestehende State-Verbindungen können alte Policy weiter nutzen. Gezielt States löschen, nicht blind alle in Produktion.

Logging:

- nicht jede erlaubte Verbindung loggen
- Blocks/administrative Flows gezielt
- zentrale Syslog-Ziele und Datenschutz

## NAT

### Port Forward / Destination NAT

```text
Firewall → NAT → Port Forward
```

Beispiel:

```text
Interface: WAN
Protocol: TCP
Destination: WAN address
Destination Port: 443
Redirect target IP: 10.10.20.10
Redirect target port: 443
Filter rule association: passende Regel erzeugen/manuell
```

Prüfen:

- Dienst lauscht intern.
- Server-Defaultgateway zeigt über pfSense oder Rückroute korrekt.
- WAN-Adresse ist wirklich öffentlich; kein CGNAT/DS-Lite.
- vorgelagerter Router/Cloud-Security-Group.
- Firewallregel vorhanden.
- NAT Reflection nur wenn nötig; besser Split DNS.

### Outbound NAT / Source NAT

Modi:

- Automatic
- Hybrid
- Manual
- Disabled

Hybrid eignet sich, wenn Standardregeln plus eigene Ausnahmen benötigt werden. Manual erfordert vollständige Verantwortung.

No-NAT/Ausnahmen für VPN oder geroutete Netze oberhalb generischer NAT-Regeln platzieren.

### 1:1 NAT

Zusätzliche öffentliche Adresse auf internen Host abbilden. Firewallregeln weiterhin erforderlich; ARP/VIP/Providerroute beachten.

> [!important]
> NAT ist keine Firewallregel. Übersetzung und Erlaubnis sind getrennte Konzepte, auch wenn die GUI eine zugehörige Regel erzeugen kann.

## DHCP und DNS Resolver

DHCP:

```text
Services → DHCP Server
```

Planen:

- Pool außerhalb statischer Hosts
- Reservations/Static Mappings
- Gateway/DNS/NTP/Domain
- Leasezeiten
- HA-Sync je Architektur

DNS Resolver Unbound:

```text
Services → DNS Resolver
```

Optionen:

- Interfaces/ACLs
- DNSSEC
- Host Overrides
- Domain Overrides
- DHCP-Registrierung
- Forwarding Mode
- DoT je Version/Setup

Split DNS statt NAT Reflection:

```text
intern: app.example.org → 10.10.20.10
extern: app.example.org → öffentliche IP
```

Diagnose:

```text
Diagnostics → DNS Lookup
Status → System Logs → Resolver
```

Shell:

```sh
dril example.org
sockstat -4 -6 -l | grep ':53'
```

## Routing, Gateways und Multi-WAN

Gateways:

```text
System → Routing → Gateways
```

Monitor-IP muss stabil und über genau diesen Uplink erreichbar sein. Gateway als „down“ kann Policy Routing/Fallback auslösen.

Gateway Groups:

- Tier bestimmt Priorität/Load Balancing.
- Trigger Level bestimmt Failoverkriterium.
- DNS und bestehende States bei Wechsel beachten.

Policy Routing per Firewallregel: Gateway/Gateway Group in Advanced Options setzen. Nicht auf lokale/privat geroutete Ziele anwenden; No-Gateway-Regel für interne Netze davor.

Statische Routen:

```text
System → Routing → Static Routes
```

Nur über definierte Gateways; Rückroute auf Gegenstelle erforderlich.

## VPN

Typische Optionen:

- IPsec
- OpenVPN
- WireGuard je aktueller Paket-/Produktunterstützung

Grundcheck:

1. Zeit/NTP.
2. Zertifikat/PSK.
3. WAN-Port/Firewall.
4. Phase/Handshake.
5. Tunnelnetz ohne Überschneidung.
6. Regeln auf VPN-Interface/Tab.
7. Routen und NAT-Ausnahmen.
8. DNS-Push/Split DNS.
9. MTU/MSS.

IPsec Logs:

```text
Status → System Logs → IPsec
Status → IPsec
```

OpenVPN:

```text
Status → OpenVPN
Status → System Logs → OpenVPN
```

Remote Access niemals nur „Tunnel connected“ abnehmen; interne Ziele, DNS, Rückroute und Berechtigungen testen.

## Zertifikate und Benutzer

```text
System → Cert. Manager
System → User Manager
```

- eigene CA/Intermediate bewusst planen
- Server- und Benutzerzertifikate trennen
- Ablauf überwachen
- widerrufene Benutzer/Zertifikate entfernen
- WebGUI-Zertifikat mit korrektem SAN
- Adminrechte über Gruppen/Privileges minimal
- TOTP/MFA für GUI/VPN, sofern passend

Private Keys in Backups schützen.

## Updates und Pakete

Vor Upgrade:

1. Release Notes und Upgrade Guide.
2. Konfigurationsbackup.
3. Paketkompatibilität.
4. HA-Reihenfolge.
5. Konsolenzugang.
6. Wartungsfenster.
7. freien Speicher/Filesystemstatus.

```text
System → Update
System → Package Manager
```

Pakete erweitern Angriffsfläche und Upgradeabhängigkeiten. Nur benötigte, gepflegte Pakete installieren.

Keine FreeBSD-`pkg upgrade`-Befehle außerhalb der vorgesehenen pfSense-Mechanismen verwenden, sofern Dokumentation/Support dies nicht ausdrücklich verlangt.

## Backup und Wiederherstellung

```text
Diagnostics → Backup & Restore
Services → Auto Config Backup (je Edition/Funktion)
```

Backupoptionen:

- vollständige `config.xml`
- verschlüsselt exportieren
- RRD/Leases nur bei Bedarf
- AutoConfigBackup mit starkem Encryption Password
- Offlinekopie getrennt aufbewahren

Test:

- Backup nach wesentlichen Änderungen.
- Version/Hardware/Interfacezuordnung dokumentieren.
- Wiederherstellung in Labor/Spare Appliance prüfen.
- Encryption Password und Device Key sicher verwahren.

> [!danger]
> `config.xml` kann Passworthashes, VPN-Schlüssel, Zertifikate und andere Geheimnisse enthalten. Wie einen hochsensiblen Secret-Export behandeln.

Konsole unterstützt Wiederherstellung älterer Konfigurationen je Version. Vor Einsatz Release-Dokumentation lesen.

## High Availability

Bausteine:

- CARP Virtual IPs
- pfsync für States
- XMLRPC Configuration Synchronization
- dediziertes Sync-Interface empfohlen

Planung:

- identische/kompatible Hardware und Version
- eindeutige reale IPs je Node plus VIP
- L2-Netz unterstützt CARP/Multicast/VRRP-artigen Verkehr
- NAT nutzt VIP statt Node-IP
- DHCP-HA je Implementierung
- Split-Brain verhindern
- Upgrade sekundär → Failover → primär

Status:

```text
Status → CARP (failover)
Diagnostics → States
```

Failover kontrolliert testen, inklusive bestehender Sessions und Rückschaltung.

## Monitoring und Diagnose

Dashboard/Status:

```text
Status → Interfaces
Status → Gateways
Status → System Logs
Status → Monitoring
Diagnostics → Routes
Diagnostics → ARP Table
Diagnostics → NDP Table
Diagnostics → States
Diagnostics → Packet Capture
Diagnostics → Test Port
Diagnostics → Traceroute
Diagnostics → Ping
Diagnostics → DNS Lookup
```

Shell:

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
tcpdump -ni em0
```

GUI Packet Capture vorziehen, wenn Shellzugriff unnötig ist. Interface und Filter richtig wählen.

PF Log:

```sh
tcpdump -n -e -ttt -i pflog0
```

States zu Host:

```sh
pfctl -ss | grep 192.0.2.10
```

## Härtung

- GUI nur Managementnetz/VPN.
- HTTPS mit vertrauenswürdigem Zertifikat.
- Standardadminname/Passwort ändern, individuelle Konten.
- MFA und minimale Privileges.
- SSH nur bei Bedarf, Keyauth, Quellen begrenzen.
- UPnP/NAT-PMP standardmäßig aus oder streng begrenzen.
- WAN-Management und Anti-Lockout-Regel verstehen.
- Pakete minimieren.
- Backups verschlüsseln und testen.
- Logs/NTP/Monitoring zentral.
- Bogon-/Private-Netzoptionen passend, nicht blind.
- Regelbeschreibungen, Aliases und Änderungsprozess.
- Keine Dienste auf „all interfaces“, wenn nicht nötig.
- Regelmäßige State-/NAT-/VPN-/Zertifikatsprüfung.

## Fehler-Playbooks

### Kein Internet vom LAN

1. Client IP/Gateway/DNS.
2. LAN-Regel erlaubt Verkehr?
3. pfSense kann WAN-Gateway/Internet-IP pingen?
4. Gateway Status.
5. Outbound NAT-Regel.
6. DNS Resolver/Forwarder.
7. Packet Capture LAN und WAN.

### Portforwarding geht nicht

1. öffentliche WAN-IP/CGNAT.
2. Test von extern, nicht aus demselben LAN ohne Split DNS/Reflection.
3. WAN-Capture sieht SYN?
4. NAT-Regel trifft richtige Adresse/Port?
5. verknüpfte Firewallregel?
6. LAN-Capture zeigt weitergeleitetes Paket?
7. Dienst/Hostfirewall/Rückgateway intern?
8. State/Logs.

### VPN verbunden, kein Zugriff

1. Tunnelnetz/Route.
2. Regeln auf VPN-Tab/Interface.
3. Rückroute interner Netze.
4. Outbound NAT/No-NAT.
5. DNS.
6. Überschneidende Netze.
7. MTU/MSS.
8. Capture Tunnel und LAN.

### Multi-WAN Failover unerwartet

1. Gateway/Monitor-IP.
2. Gateway Group Tier/Trigger.
3. Policy-Routing-Regel.
4. private Zielausnahmen davor.
5. States zurücksetzen gezielt.
6. DNS/Quellbindung.
7. NAT pro WAN.

## Quellen
- [pfSense Documentation](https://docs.netgate.com/pfsense/en/latest/)
- [pfSense Backup and Recovery](https://docs.netgate.com/pfsense/en/latest/backup/)
- [pfSense Firewall](https://docs.netgate.com/pfsense/en/latest/firewall/)
- [pfSense NAT](https://docs.netgate.com/pfsense/en/latest/nat/)

## Verwandte Notizen
- [[OPNsense – Cheatsheet]]
- [[BSD-Netzwerk – Cheatsheet]]
- [[Wireshark – Cheatsheet]]
- [[TrueNAS – Cheatsheet]]
