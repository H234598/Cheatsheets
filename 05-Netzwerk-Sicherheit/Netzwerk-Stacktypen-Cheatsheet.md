---
title: "Netzwerk-Stacktypen – Cheatsheet"
aliases: ["Stacktypen Netzwerk", "IPv4 IPv6 Dual Stack", "Protocol Stack Types", "Stacktypen-Cheatsheet"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [network, ipv4, ipv6, dual-stack, nat64, protocol-stack]
source: "https://www.ietf.org/technologies/ipv6/"
---

# Netzwerk-Stacktypen – Cheatsheet

> [!abstract] Zweck
> Einordnung von Netzwerk-Stacktypen: IPv4-only, IPv6-only, Dual Stack, Dual-Stack Lite, NAT64/DNS64, 464XLAT, Overlay/Underlay sowie OSI-, TCP/IP- und Software-Stacks mit Diagnosefolgen.

> [!note] Interpretation
> „Stacktypen“ wird primär als Typ der IP-Anbindung verstanden: IPv4-only, IPv6-only und Dual Stack samt Übergangstechniken. Ergänzend werden Protokoll-, Software- und Overlay-Stacks eingeordnet.

## Inhalt

- [[#Mehrdeutigkeit des Begriffs Stack]]
- [[#IPv4-only]]
- [[#IPv6-only]]
- [[#Native Dual Stack]]
- [[#DS-Lite]]
- [[#NAT64 und DNS64]]
- [[#464XLAT]]
- [[#Tunneling und Übergang]]
- [[#Overlay und Underlay]]
- [[#OSI- und TCP-IP-Stack]]
- [[#Diagnosematrix]]
- [[#Entscheidungshilfe]]

## Mehrdeutigkeit des Begriffs Stack

| Kontext | „Stack“ bedeutet |
|---|---|
| IP-Anbindung | IPv4, IPv6 oder beides |
| Protokollmodell | Ethernet → IP → TCP/UDP → Anwendung |
| OSI/TCP-IP | Schichtenmodell |
| Software | Komponenten einer Anwendung, z. B. LEMP/MERN |
| Cloud/Container | Underlay plus Overlay/VXLAN/CNI |
| Implementierung | Kernel-Netzwerkstack, User-Space-Stack, SmartNIC/DPU |

## IPv4-only

```text
Client ─ IPv4 ─ Router/NAT ─ IPv4-Internet
```

Eigenschaften:

- nur A-Records direkt nutzbar
- private RFC1918-Adressen und NAT im LAN häufig
- begrenzter Adressraum
- alte Anwendungen meist kompatibel
- reine IPv6-Ziele nicht ohne Proxy/Gateway erreichbar

Diagnose:

```bash
ip -4 addr
ip -4 route
curl -4 https://example.org/
dig A example.org
```

## IPv6-only

```text
Client ─ native IPv6 ─ IPv6-Internet
                  └─ NAT64/Proxy für IPv4-Ziele
```

Eigenschaften:

- globale IPv6-Adressen, meist `/64` im LAN
- Link-Local und Neighbor Discovery obligatorisch
- keine direkte IPv4-Konnektivität
- Legacy-IPv4-Ziele benötigen NAT64/Proxy/CLAT
- IPv4-Literale in Anwendungen sind problematisch

Diagnose:

```bash
ip -6 addr
ip -6 route
ping -6 gateway-or-host
curl -6 https://example.org/
dig AAAA example.org
```

## Native Dual Stack

```text
           ┌─ IPv4 ─ IPv4-Ziel
Client ────┤
           └─ IPv6 ─ IPv6-Ziel
```

Beide Protokolle sind nativ vorhanden. Anwendungen wählen häufig über Happy Eyeballs.

Vorteile:

- höchste Kompatibilität
- schrittweise Migration
- native Erreichbarkeit beider Welten

Nachteile:

- zwei Adress-, Routing-, DNS- und Firewallpfade
- Fehler können nur einen Stack betreffen
- doppelte Monitoring-/Policyarbeit

Tests immer getrennt:

```bash
curl -4 https://example.org/
curl -6 https://example.org/
```

## DS-Lite

Dual-Stack Lite typischer ISP-Zugang:

```text
Kundennetz IPv4 privat
     ↓ Tunnel über IPv6
AFTR/Carrier-Grade NAT
     ↓
IPv4-Internet

IPv6 läuft nativ
```

Folgen:

- kein eigener öffentlicher IPv4-Endpunkt
- klassische IPv4-Portweiterleitung oft nicht möglich
- CGNAT teilt IPv4-Adresse
- IPv6-Portfreigabe ist separat möglich, aber Firewall beachten
- Fehlersuche muss AFTR/Providerpfad einbeziehen

Erkennungsindizien:

- WAN-IPv4 privat oder CGNAT `100.64.0.0/10`
- öffentliche „Wie ist meine IP“-Adresse weicht ab
- native IPv6-Präfixdelegation

## NAT64 und DNS64

DNS64 synthetisiert AAAA aus A-Records; NAT64 übersetzt Verkehr:

```text
IPv6-Client → synthetisierte IPv6-Adresse → NAT64 → IPv4-Server
```

Bekanntes Präfix häufig `64:ff9b::/96`, aber Betreiber können anderes verwenden.

Grenzen:

- funktioniert primär bei Namensauflösung
- IPv4-Literale scheitern ohne 464XLAT/Proxy
- Protokolle mit eingebetteten IPs können ALG/Anpassung benötigen
- DNSSEC-Validierung und Synthese müssen korrekt zusammenspielen

Test:

```bash
dig AAAA ipv4only.arpa
```

RFC-7050-artige Präfixerkennung hängt von Umgebung/Resolver ab.

## 464XLAT

Kombiniert:

- CLAT auf Client/CPE: IPv4-App → IPv6
- PLAT/NAT64 im Netz: IPv6 → IPv4-Internet

```text
IPv4-only App → CLAT → IPv6-Netz → NAT64/PLAT → IPv4-Ziel
```

Häufig in Mobilfunknetzen und IPv6-only Zugängen. Ermöglicht IPv4-Literale besser als reines DNS64/NAT64.

## Tunneling und Übergang

| Technik | Zweck | Hinweis |
|---|---|---|
| 6in4 | IPv6 über IPv4 | Protokoll 41, NAT/Firewall relevant |
| GRE | generischer Tunnel | keine Verschlüsselung |
| IPsec | geschützter Layer-3-Tunnel | MTU/Policy/Routing |
| WireGuard | moderner VPN-Tunnel | Overlay-Routen/DNS |
| Teredo/6to4 | historische Auto-Tunnel | heute meist vermeiden |

Tunnel reduzieren MTU. Overhead und Path MTU Discovery prüfen.

## Overlay und Underlay

```text
Anwendungs-/Pod-IP (Overlay)
        ↓ VXLAN/Geneve/WireGuard
Host-IP-Netz (Underlay)
        ↓
physisches Netz
```

Beispiele:

- Kubernetes CNI
- VXLAN-EVPN
- SD-WAN
- VPN-Mesh
- Cloud-VPC-Tunnel

Diagnose muss beide Ebenen trennen:

1. Pod/Overlay-Route.
2. Tunnelendpunkt.
3. Underlay-IP-Konnektivität.
4. MTU/Fragmentierung.
5. Policy/NAT.

## OSI- und TCP-IP-Stack

| OSI | TCP/IP | Beispiele |
|---:|---|---|
| 7 Anwendung | Application | HTTP, DNS, SSH |
| 6 Darstellung | Application | TLS-Encoding, JSON |
| 5 Sitzung | Application | RPC-/Sitzungssteuerung |
| 4 Transport | Transport | TCP, UDP, QUIC |
| 3 Vermittlung | Internet | IPv4, IPv6, ICMP |
| 2 Sicherung | Link | Ethernet, Wi-Fi, VLAN |
| 1 Bitübertragung | Physical | Kupfer, Glas, Funk |

Das Modell ist Diagnosehilfe, keine perfekte Abbildung jedes Protokolls.

## Diagnosematrix

| Symptom | IPv4-Test | IPv6-Test | Interpretation |
|---|---|---|---|
| Website langsam, dann geht sie | `curl -4` | `curl -6` | ein Stack timeoutet, Happy Eyeballs fällt zurück |
| Portforwarding unmöglich | WAN IPv4 prüfen | öffentliche IPv6 prüfen | DS-Lite/CGNAT möglich |
| Name geht, IP-Literal nicht | A/IPv4 | DNS64/NAT64 | IPv6-only mit NAT64 ohne CLAT |
| nur manche Größen hängen | PMTU IPv4 | PMTU IPv6 | Tunnel/ICMP-Block/MTU |
| Ping geht, App nicht | ICMP | ICMPv6 | Port/TLS/App/Firewall getrennt |

Werkzeuge:

```bash
getent ahosts example.org
dig A example.org
dig AAAA example.org
curl -4 -v https://example.org/
curl -6 -v https://example.org/
traceroute -4 example.org
traceroute -6 example.org
```

## Entscheidungshilfe

| Ziel | Empfehlung |
|---|---|
| maximale kurzfristige Kompatibilität | native Dual Stack |
| modernes kontrolliertes Rechenzentrum | IPv6-only + NAT64/Proxy nach Apptests möglich |
| ISP ohne öffentliche IPv4 | DS-Lite/CGNAT akzeptieren oder Business-/IPv4-Option |
| Mobilfunk/Clientnetz | IPv6-only + 464XLAT verbreitet |
| Migration | Metriken, DNS, Firewall und Apps pro Stack getrennt testen |

> [!important]
> „IPv6 abschalten“ kaschiert häufig nur einen fehlerhaften IPv6-Pfad. Besser Routing, RA, DNS, Firewall und PMTU korrigieren; Abschaltung nur als bewusst dokumentierte Kompatibilitätsmaßnahme.

## Quellen
- [IETF IPv6](https://www.ietf.org/technologies/ipv6/)
- [RFC 6333 DS-Lite](https://www.rfc-editor.org/rfc/rfc6333)
- [RFC 6146 NAT64](https://www.rfc-editor.org/rfc/rfc6146)
- [RFC 6877 464XLAT](https://www.rfc-editor.org/rfc/rfc6877)

## Verwandte Notizen
- [[Netzwerk-Konfiguration – Cheatsheet]]
- [[Linux-Netzwerk – Cheatsheet]]
- [[Wireshark – Cheatsheet]]
