---
title: "BSD-Netzwerk – Cheatsheet"
aliases: ["FreeBSD OpenBSD Netzwerk", "ifconfig rc.conf pf Cheatsheet", "BSD Network"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [bsd, freebsd, openbsd, network, ifconfig, pf]
source: "https://docs.freebsd.org/en/books/handbook/network/"
---

# BSD-Netzwerk – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für Netzwerkbetrieb auf FreeBSD und OpenBSD: ifconfig, rc.conf/hostname.if, Routen, DNS, WLAN, VLAN, lagg/trunk, Bridge, PF, Serverlistener, tcpdump und Diagnose.

> [!note] BSD ist keine einzelne Implementierung
> FreeBSD, OpenBSD, NetBSD und macOS teilen Konzepte, unterscheiden sich aber bei Persistenz, Interfaceklonen, WLAN und Dienstverwaltung. Dieser Spickzettel fokussiert FreeBSD und OpenBSD und kennzeichnet Unterschiede.

## Inhalt

- [[#Bestand aufnehmen]]
- [[#Laufzeit mit ifconfig und route]]
- [[#FreeBSD persistent konfigurieren]]
- [[#OpenBSD persistent konfigurieren]]
- [[#DNS]]
- [[#WLAN]]
- [[#VLAN, Bridge und Aggregation]]
- [[#PF Firewall]]
- [[#Server und Listener]]
- [[#Diagnose]]
- [[#Abnahme]]

## Bestand aufnehmen

```sh
ifconfig -a
netstat -rn
route -n get default
arp -an
ndp -an
sockstat -4 -6 -l        # FreeBSD
netstat -na               # OpenBSD/allgemein
cat /etc/resolv.conf
```

Hardware/Logs FreeBSD:

```sh
pciconf -lv
dmesg | grep -Ei 'em|igb|ix|re|wlan|link'
```

OpenBSD:

```sh
pcidump -v
dmesg
```

## Laufzeit mit ifconfig und route

Interface hoch/runter:

```sh
doas ifconfig em0 up
doas ifconfig em0 down
```

IPv4:

```sh
doas ifconfig em0 inet 192.0.2.10 netmask 255.255.255.0
```

CIDR-Syntax wird je BSD/Version unterstützt, klassische Netmask ist portabel.

IPv6:

```sh
doas ifconfig em0 inet6 2001:db8:1::10 prefixlen 64
```

Alias:

```sh
doas ifconfig em0 alias 192.0.2.11 netmask 255.255.255.255
```

Default Route:

```sh
doas route add default 192.0.2.1
doas route delete default
```

Netzroute:

```sh
doas route add -net 198.51.100.0/24 192.0.2.254
```

Entscheidung:

```sh
route -n get 203.0.113.10
```

MTU:

```sh
doas ifconfig em0 mtu 1500
```

Medienstatus:

```sh
ifconfig em0
```

## FreeBSD persistent konfigurieren

`/etc/rc.conf`:

```sh
hostname="server.example.org"
ifconfig_em0="inet 192.0.2.10 netmask 255.255.255.0"
defaultrouter="192.0.2.1"

ifconfig_em0_ipv6="inet6 accept_rtadv"
# oder statisch:
# ifconfig_em0_ipv6="inet6 2001:db8:1::10 prefixlen 64"
# ipv6_defaultrouter="fe80::1%em0"
```

DHCP:

```sh
ifconfig_em0="DHCP"
```

Service neu anwenden:

```sh
service netif restart em0
service routing restart
```

> [!danger]
> `service netif restart` kann alle Interfaces beeinflussen, wenn ohne Interface verwendet. Remote vorsichtig und mit Konsole.

Temporär DHCP erneuern:

```sh
service dhclient restart em0
```

Statische Routen:

```sh
static_routes="corp"
route_corp="-net 198.51.100.0/24 192.0.2.254"
```

Gatewaybetrieb:

```sh
gateway_enable="YES"
ipv6_gateway_enable="YES"
```

Entspricht Forwarding; Firewall/RA/DHCP separat.

## OpenBSD persistent konfigurieren

Pro Interface `/etc/hostname.em0`:

Statisch:

```text
inet 192.0.2.10 255.255.255.0
inet6 2001:db8:1::10 64
up
```

DHCP/autoconf:

```text
inet autoconf
inet6 autoconf
```

Default Route wird bei statischem Setup modern häufig über `route`-Zeile in Interface-Datei oder `/etc/mygate` je Release/Tradition konfiguriert. Aktuelle `hostname.if(5)`-Seite des installierten Releases verwenden.

Beispiel in `hostname.em0`:

```text
inet 192.0.2.10 255.255.255.0
!route add default 192.0.2.1
```

Anwenden:

```sh
doas sh /etc/netstart em0
```

Alle Interfaces:

```sh
doas sh /etc/netstart
```

Hostname:

```text
/etc/myname
```

## DNS

`/etc/resolv.conf` klassisch:

```text
search example.org
nameserver 192.0.2.53
nameserver 192.0.2.54
```

DHCP/`resolvd` kann Datei verwalten. Eigentümer/Flags und Systemmechanismus prüfen, nicht gegen Automatisierung anschreiben.

Abfragen:

```sh
dril example.org A
dril example.org AAAA
host example.org
nslookup example.org
```

OpenBSD nutzt typischerweise `unwind` als validierenden lokalen Resolver, wenn aktiviert:

```sh
doas rcctl enable unwind
doas rcctl start unwind
unwindctl status
```

FreeBSD kann `local_unbound` nutzen:

```sh
sysrc local_unbound_enable=YES
service local_unbound start
```

## WLAN

### FreeBSD

Treiber/Clone:

```sh
ifconfig wlan0 create wlandev iwm0
```

`/etc/rc.conf`:

```sh
wlans_iwm0="wlan0"
ifconfig_wlan0="WPA DHCP"
```

`/etc/wpa_supplicant.conf`:

```ini
network={
    ssid="MEIN-WLAN"
    psk="PASSWORT"
}
```

```sh
chmod 600 /etc/wpa_supplicant.conf
service netif restart wlan0
```

Scan:

```sh
ifconfig wlan0 list scan
```

### OpenBSD

Scan:

```sh
ifconfig iwm0 scan
```

`/etc/hostname.iwm0`:

```text
join MEIN-WLAN wpakey PASSWORT
inet autoconf
inet6 autoconf
```

Passwortdatei restriktiv schützen:

```sh
doas chmod 600 /etc/hostname.iwm0
```

Mehrere Netze/802.1X je Release über `ifconfig`, `hostname.if` und `wpa_supplicant`-Möglichkeiten prüfen.

## VLAN, Bridge und Aggregation

### VLAN FreeBSD

Laufzeit:

```sh
ifconfig vlan100 create
ifconfig vlan100 vlan 100 vlandev em0
ifconfig vlan100 inet 192.0.2.10/24 up
```

`/etc/rc.conf`:

```sh
cloned_interfaces="vlan100"
ifconfig_vlan100="inet 192.0.2.10/24 vlan 100 vlandev em0"
```

### VLAN OpenBSD

`/etc/hostname.vlan100`:

```text
parent em0 vnetid 100
inet 192.0.2.10 255.255.255.0
up
```

### Bridge

FreeBSD:

```sh
ifconfig bridge0 create
ifconfig bridge0 addm em0 addm tap0 up
```

OpenBSD `/etc/hostname.bridge0`:

```text
add em0
add vether0
up
```

IP meist auf Bridge-/virtuellem Interface gemäß Architektur, nicht unkoordiniert auf allen Mitgliedern.

### Aggregation

FreeBSD `lagg`:

```sh
ifconfig lagg0 create
ifconfig lagg0 laggproto lacp laggport em0 laggport em1
```

OpenBSD `trunk` oder neuere `aggr` je Release; installierte Manpage prüfen:

```sh
man trunk
man aggr
```

LACP erfordert passende Switchkonfiguration.

## PF Firewall

Syntax:

```sh
doas pfctl -nf /etc/pf.conf
```

Laden:

```sh
doas pfctl -f /etc/pf.conf
```

Aktivieren:

```sh
doas pfctl -e
```

Regeln anzeigen:

```sh
doas pfctl -sr
doas pfctl -sn
doas pfctl -ss
doas pfctl -si
```

Minimalbeispiel:

```pf
wan = "em0"
lan = "em1"

set skip on lo
block log all
pass out on $wan inet from ($wan:network) to any keep state
pass in on $lan from $lan:network to any keep state
pass in on $wan proto tcp to ($wan) port 22 from 192.0.2.0/24 keep state
```

NAT:

```pf
match out on $wan from $lan:network to any nat-to ($wan)
```

> [!danger]
> PF-Syntax und Featuredetails unterscheiden sich zwischen OpenBSD, FreeBSD/pfSense und macOS. Regeln mit der lokalen `pf.conf(5)`-Manpage und `pfctl -nf` prüfen.

Remote sicher laden:

1. Syntaxcheck.
2. bestehende Regeln sichern.
3. automatische Rücknahme per `at`/Watchdog planen.
4. neue Regeln laden.
5. zweite Sitzung testen.
6. Rücknahme abbrechen.

## Server und Listener

FreeBSD:

```sh
sockstat -4 -6 -l
sockstat -4 -6 -c
```

OpenBSD:

```sh
netstat -na -f inet
netstat -na -f inet6
fstat | less
```

Serviceverwaltung:

FreeBSD:

```sh
service sshd status
sysrc sshd_enable=YES
service sshd start
```

OpenBSD:

```sh
rcctl check sshd
rcctl enable sshd
rcctl start sshd
```

## Diagnose

Basis:

```sh
ifconfig -a
netstat -rn
route -n get default
arp -an
ndp -an
cat /etc/resolv.conf
ping -c 3 192.0.2.1
traceroute example.org
traceroute6 example.org
```

Mitschnitt:

```sh
doas tcpdump -ni em0
doas tcpdump -ni em0 'host 192.0.2.10 and port 443'
doas tcpdump -ni em0 -w /tmp/diag.pcap 'host 192.0.2.10'
```

PF Logs:

```sh
doas tcpdump -n -e -ttt -i pflog0
```

Interfacezähler:

```sh
netstat -I em0 -w 1
```

Routing Socket/Änderungen:

```sh
route -n monitor
```

Prüfreihenfolge:

1. Interface/Media/Link.
2. IP/Prefix.
3. ARP/ND zum Gateway.
4. Route und Rückroute.
5. DNS.
6. PF-Regel/State/Log.
7. Listener/Bind-Adresse.
8. Paketmitschnitt auf intern/extern.

## Abnahme

```text
[ ] Release-spezifische Manpages verwendet
[ ] Runtime und rc.conf/hostname.if stimmen
[ ] IPv4/IPv6 getrennt getestet
[ ] Resolververwaltung geklärt
[ ] PF-Syntax und Remote-Rollback getestet
[ ] VLAN/LACP am Switch passend
[ ] Reboot und Dienststart geprüft
[ ] Konfigurationsbackup vorhanden
```

## Quellen
- [FreeBSD Handbook Networking](https://docs.freebsd.org/en/books/handbook/network/)
- [OpenBSD Networking FAQ](https://www.openbsd.org/faq/faq6.html)
- [OpenBSD hostname.if(5)](https://man.openbsd.org/hostname.if)
- [OpenBSD pf.conf(5)](https://man.openbsd.org/pf.conf)

## Verwandte Notizen
- [[Netzwerk-Konfiguration – Cheatsheet]]
- [[pfSense – Cheatsheet]]
- [[OPNsense – Cheatsheet]]
- [[Wireshark – Cheatsheet]]
