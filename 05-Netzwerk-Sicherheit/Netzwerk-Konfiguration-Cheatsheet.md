---
title: "Netzwerk-Konfiguration – Cheatsheet"
aliases: ["Netzwerk einrichten Cheatsheet", "Client Server Netzwerk", "TCP IP Administration", "Netzwerk-Konfiguration-Linux-Windows-BSD"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [network, linux, windows, bsd, tcp-ip, dns, routing]
source: "https://www.ietf.org/standards/"
---

# Netzwerk-Konfiguration – Cheatsheet

> [!abstract] Zweck
> Betriebssystemübergreifende Leitseite zum Einrichten und Diagnostizieren von Netzwerken auf Linux-, Windows- und BSD-Clients und -Servern – von Link und WLAN bis IP, Routing, DNS, Firewall und Diensten.

> [!abstract] Universelles Schichtenmodell
> Netzwerkprobleme von unten nach oben prüfen: **Hardware/Link → VLAN/WLAN → Adresse → Route → DNS → Transportport → Anwendung → Policy/Firewall**. Ein Ping allein beweist nur einen kleinen Ausschnitt.

## Inhalt

- [[#Grundbegriffe]]
- [[#Universelle Prüfreihenfolge]]
- [[#Planung vor der Konfiguration]]
- [[#Client versus Server]]
- [[#IPv4 und IPv6]]
- [[#DNS]]
- [[#Routing]]
- [[#WLAN]]
- [[#Firewall und Freigaben]]
- [[#Werkzeugzuordnung nach Betriebssystem]]
- [[#Abnahmecheckliste]]

## Grundbegriffe

| Begriff | Bedeutung |
|---|---|
| Interface | physische oder virtuelle Netzwerkschnittstelle |
| MAC-Adresse | Layer-2-Adresse einer Schnittstelle |
| VLAN | logische Layer-2-Segmentierung nach 802.1Q |
| IP-Adresse | Layer-3-Adresse eines Hosts/Interfaces |
| Prefix | Netzanteil, z. B. `/24` oder `/64` |
| Gateway | Next Hop für Ziele außerhalb lokaler Netze |
| Route | Zuordnung Zielprefix → Next Hop/Interface |
| DNS Resolver | übersetzt Namen und IP-Adressen |
| DHCP | dynamische Adress-/Optionsvergabe |
| SLAAC | IPv6-Autokonfiguration über Router Advertisements |
| NAT | Übersetzung von Adressen/Ports, meist IPv4 |
| MTU | maximale Layer-3-Paketgröße ohne Fragmentierung |
| Socket | Kombination aus Protokoll, Adresse und Port |

## Universelle Prüfreihenfolge

1. **Scope:** ein Host, ein VLAN, ein Standort oder alle?
2. **Link:** Kabel, Funk, Portstatus, Treiber, Interface UP?
3. **Layer 2:** richtiges VLAN, WLAN-SSID/Authentisierung, keine Port-Security-Sperre?
4. **Adresse:** richtige IPv4/IPv6-Adresse, Prefix, Lease?
5. **Lokale Nachbarn:** ARP/ND zum Gateway?
6. **Route:** Default Route und spezifische Routen korrekt?
7. **DNS:** Resolver erreichbar, Name korrekt, Split-DNS/Suffix?
8. **Transport:** TCP/UDP-Port erreichbar?
9. **Anwendung:** Dienst lauscht auf richtiger Adresse, TLS/SNI/Auth?
10. **Policy:** Hostfirewall, Netzfirewall, ACL, SELinux/AppArmor?
11. **Pfad:** asymmetrisches Routing, MTU/PMTUD, Proxy/VPN?
12. **Beweis:** Mitschnitt an passendem Punkt.

Minimaltests:

```text
Link → lokale IP → Gateway → externe IP → DNS → Zielport → Anwendung
```

> [!tip]
> Immer IP-Test und Namenstest trennen. Funktioniert `203.0.113.10`, aber `server.example.org` nicht, ist das Problem wahrscheinlich DNS/Suchpfad und nicht die Grundroute.

## Planung vor der Konfiguration

Dokumentieren:

```text
Hostname:
Interface/Port:
VLAN-ID:
IPv4-Adresse/Prefix:
IPv4-Gateway:
IPv6-Modus/Adresse/Prefix:
IPv6-Gateway/RA:
DNS-Server:
DNS-Suchdomains:
MTU:
Proxy/VPN:
Firewallfreigaben:
NTP:
Verantwortung/Rollback:
```

Adresskonflikte vermeiden:

- DHCP-Reservierung oder IPAM prüfen.
- Statische Adresse außerhalb dynamischer Pools oder sauber reserviert.
- IPv6 DAD/Neighbor Discovery beachten.
- Gateway nicht als Hostadresse vergeben.
- Netzwerk-/Broadcastadresse bei klassischem IPv4 nicht nutzen.

Remoteänderungen:

> [!danger]
> Bei Gateway, VLAN, Firewall oder Management-IP immer Konsolen-/Out-of-Band-Zugang und Rückfallplan vorsehen. Neue Konfiguration zuerst zusätzlich setzen, testen und alte erst danach entfernen, sofern das System dies erlaubt.

## Client versus Server

### Client

- DHCP/SLAAC oft sinnvoll.
- DNS-Suchdomain kontrollieren.
- WLAN/Roaming/Energiesparen relevant.
- VPN und Proxy können Routen/DNS überschreiben.
- Hostfirewall meist ausgehend offen, eingehend restriktiv.

### Server

- stabile Adresse über statisch oder DHCP-Reservierung.
- mehrere NICs/Routen bewusst planen.
- Dienst-Bindings und Firewall explizit.
- DNS A/AAAA/PTR und Zertifikatsnamen abstimmen.
- Zeit/NTP, Monitoring und Logging.
- keine zweite Default Route ohne Policy-/Metrikkonzept.
- Management-, Storage- und Clientnetze segmentieren.

## IPv4 und IPv6

IPv4:

```text
192.0.2.10/24
Gateway 192.0.2.1
```

IPv6:

```text
2001:db8:1234:1::10/64
fe80::...%interface   # Link-Local mit Scope-ID
```

IPv6-Grundregeln:

- Link-Local `fe80::/10` ist normal und nötig.
- `/64` ist das typische LAN-Präfix für SLAAC.
- Router Advertisement ist nicht gleich DHCPv6.
- DNS kann via RA/RDNSS oder DHCPv6 kommen.
- ICMPv6 nicht pauschal blockieren; es ist für ND und Path MTU wesentlich.
- NAT ist für normales IPv6 nicht erforderlich; Firewall bleibt wichtig.

Dual Stack diagnostizieren:

```bash
curl -4 https://example.org/
curl -6 https://example.org/
```

Happy Eyeballs kann einen defekten Stack kaschieren, da Anwendungen auf den anderen ausweichen.

## DNS

Prüffragen:

1. Welche Resolver sind effektiv aktiv?
2. Welche Suchdomains gelten?
3. Split-DNS/VPN?
4. A und AAAA unterschiedlich erreichbar?
5. Cache oder veralteter Record?
6. DNSSEC/DoT/DoH/Proxy?

Werkzeuge:

```bash
dig example.org A
dig example.org AAAA
dig +trace example.org
getent ahosts example.org
nslookup example.org
Resolve-DnsName example.org
```

Server direkt fragen:

```bash
dig @192.0.2.53 example.org
```

Reverse:

```bash
dig -x 192.0.2.10
```

> [!warning]
> `dig` zeigt DNS-Antworten, aber nicht zwingend die komplette Resolverlogik der Anwendung. Auf Linux zusätzlich `getent`, auf Windows `Resolve-DnsName` und Anwendungsproxy prüfen.

## Routing

Grundprinzip:

- längstes passendes Präfix gewinnt
- danach Metrik/Priorität
- Policy Routing kann zusätzlich Quelle, Markierung oder Tabelle berücksichtigen

Wichtige Fragen:

- Welche Route wird für **diese Zieladresse** gewählt?
- Welche Quelladresse wird verwendet?
- Ist der Rückweg symmetrisch?
- Gibt es VPN-/Container-/Cloud-Routen?

Werkzeuge:

```bash
ip route get 203.0.113.10
route -n get 203.0.113.10      # BSD/macOS-ähnlich
Get-NetRoute
Test-NetConnection host -DiagnoseRouting
```

## WLAN

Schichten:

1. Funk/Regulatory Domain.
2. SSID/BSSID/Kanal/Band.
3. Authentisierung (PSK, SAE, 802.1X/EAP).
4. Layer-2-Verbindung.
5. DHCP/SLAAC.
6. Captive Portal/Policy.

Sicherheit:

- WPA2-AES oder WPA3; WEP/TKIP vermeiden.
- Unternehmens-WLAN: CA und Servername bei EAP validieren.
- PSKs nicht in Logs/CLI-History ausgeben.
- Autoconnect für fremde offene Netze deaktivieren.

## Firewall und Freigaben

Eine Freigabe benötigt meist:

```text
Quelle → Ziel → Protokoll → Zielport → Richtung → Interface/Zone → Zustand
```

Server prüfen:

1. Dienst lauscht?
2. richtige Bind-Adresse?
3. Hostfirewall?
4. Netzfirewall/ACL?
5. NAT/Portforwarding?
6. Rückroute?
7. TLS/SNI/Anwendung?

Listener:

```bash
ss -tulpn
Get-NetTCPConnection -State Listen
sockstat -4 -6 -l
```

## Werkzeugzuordnung nach Betriebssystem

| Aufgabe | Linux | Windows | BSD |
|---|---|---|---|
| Interfaces | `ip link`, `nmcli` | `Get-NetAdapter` | `ifconfig` |
| Adressen | `ip addr` | `Get-NetIPAddress` | `ifconfig` |
| Routen | `ip route` | `Get-NetRoute` | `netstat -rn`, `route` |
| Nachbarn | `ip neigh` | `Get-NetNeighbor` | `arp -an`, `ndp -an` |
| DNS | `resolvectl`, `dig` | `Get-DnsClientServerAddress`, `Resolve-DnsName` | `drill`, `host`, `/etc/resolv.conf` |
| WLAN | `nmcli`, `iw`, `wpa_cli` | `netsh wlan` | `ifconfig wlan0 list scan` |
| Ports | `ss`, `nc` | `Test-NetConnection`, `Get-NetTCPConnection` | `sockstat`, `nc` |
| Mitschnitt | `tcpdump`, Wireshark | `pktmon`, Wireshark | `tcpdump` |

## Abnahmecheckliste

```text
[ ] Interface und VLAN korrekt
[ ] Linkgeschwindigkeit/Duplex plausibel
[ ] IPv4 und IPv6 wie geplant
[ ] Default- und Spezialrouten korrekt
[ ] DNS A/AAAA/PTR und Suchdomain geprüft
[ ] NTP synchron
[ ] Firewall nur erforderliche Flows
[ ] Serverdienste auf vorgesehenen Adressen
[ ] MTU/PMTUD getestet
[ ] Reboot-/Reconnect-Persistenz geprüft
[ ] Monitoring und Logs vorhanden
[ ] Konfiguration und Rollback dokumentiert
```

## Quellen
- [IETF Internet Standards](https://www.ietf.org/standards/)
- [Wireshark Documentation](https://www.wireshark.org/docs/)

## Verwandte Notizen
- [[Linux-Netzwerk – Cheatsheet]]
- [[Windows-Netzwerk – Cheatsheet]]
- [[BSD-Netzwerk – Cheatsheet]]
- [[Netzwerk-Stacktypen – Cheatsheet]]
- [[Wireshark – Cheatsheet]]
