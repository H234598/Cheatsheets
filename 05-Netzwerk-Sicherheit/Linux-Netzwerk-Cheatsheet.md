---
title: "Linux-Netzwerk – Cheatsheet"
aliases: ["Linux Netzwerk einrichten", "ip addr nmcli wpa_supplicant", "Linux Network Cheatsheet"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, network, iproute2, networkmanager, wpa-supplicant, systemd-networkd]
source: "https://networkmanager.dev/docs/"
---

# Linux-Netzwerk – Cheatsheet

> [!abstract] Zweck
> Sehr ausführliche Linux-Netzwerkreferenz von `ip link`/`ip addr` über NetworkManager, systemd-networkd, wpa_supplicant, VLAN/Bond/Bridge, Routing, DNS, Wi-Fi, Serverdienste, Firewall und Paketdiagnose.

> [!danger] Remote-Netzwerkänderungen
> Bei Änderungen an Management-IP, Default Route, VLAN, Bonding oder Firewall eine zweite Sitzung und Konsolenzugriff offen halten. Persistenzdateien erst nach erfolgreichem Laufzeittest aktivieren – oder einen automatischen Rollback planen.

## Inhalt

- [[#Bestand aufnehmen]]
- [[#iproute2: Link, Adresse, Route und Nachbarn]]
- [[#NetworkManager mit nmcli]]
- [[#WLAN mit NetworkManager]]
- [[#wpa_supplicant direkt]]
- [[#systemd-networkd]]
- [[#Netplan]]
- [[#VLAN, Bridge, Bond und Team]]
- [[#DNS mit systemd-resolved]]
- [[#Routing und Policy Routing]]
- [[#MTU, Offloads und Performance]]
- [[#Serverdienste und Listener]]
- [[#Firewall]]
- [[#Diagnose und Mitschnitt]]
- [[#Persistenz- und Abnahmecheck]]

## Bestand aufnehmen

```bash
ip -br link
ip -br address
ip route
ip -6 route
ip neigh
resolvectl status
ss -tulpn
nmcli general status
nmcli device status
```

System/Hardware:

```bash
lspci -nnk | grep -A3 -Ei 'Ethernet|Network'
lsusb -t
ethtool -i enp1s0
udevadm info /sys/class/net/enp1s0
```

Interface-Namen nicht raten:

```bash
ls /sys/class/net
```

## iproute2: Link, Adresse, Route und Nachbarn

### Links

```bash
ip link show
ip -details link show dev enp1s0
sudo ip link set dev enp1s0 up
sudo ip link set dev enp1s0 down
sudo ip link set dev enp1s0 mtu 1500
```

MAC temporär:

```bash
sudo ip link set enp1s0 down
sudo ip link set enp1s0 address 02:00:00:00:00:10
sudo ip link set enp1s0 up
```

NetworkManager kann dies beim Reconnect überschreiben.

### Adressen

```bash
ip addr show
ip -br addr
sudo ip addr add 192.0.2.10/24 dev enp1s0
sudo ip addr del 192.0.2.10/24 dev enp1s0
sudo ip -6 addr add 2001:db8:1::10/64 dev enp1s0
```

Alle Adressen temporär leeren – gefährlich remote:

```bash
sudo ip addr flush dev enp1s0
```

### Routen

```bash
ip route
ip -6 route
sudo ip route add default via 192.0.2.1 dev enp1s0
sudo ip route replace default via 192.0.2.1 dev enp1s0 metric 100
sudo ip route add 198.51.100.0/24 via 192.0.2.254
sudo ip route del 198.51.100.0/24
```

Routenentscheidung:

```bash
ip route get 203.0.113.10
ip route get 203.0.113.10 from 192.0.2.10
ip -6 route get 2001:db8:ffff::1
```

### Nachbarn ARP/ND

```bash
ip neigh
ip neigh show dev enp1s0
sudo ip neigh flush dev enp1s0
```

Zustände wie `REACHABLE`, `STALE`, `DELAY`, `FAILED` helfen bei Layer-2-/Gatewayproblemen.

### Statistik

```bash
ip -s link show dev enp1s0
ethtool enp1s0
ethtool -S enp1s0 | less
```

Fehler/Drop-Zähler vor und nach Test vergleichen.

## NetworkManager mit nmcli

Status:

```bash
nmcli general status
nmcli device status
nmcli connection show
nmcli connection show --active
```

Gerätedetails:

```bash
nmcli device show enp1s0
```

### DHCP-Verbindung

```bash
sudo nmcli connection add type ethernet \
  ifname enp1s0 con-name lan-dhcp \
  ipv4.method auto ipv6.method auto

sudo nmcli connection up lan-dhcp
```

### Statisches IPv4, IPv6 automatisch

```bash
sudo nmcli connection add type ethernet \
  ifname enp1s0 con-name lan-static \
  ipv4.method manual \
  ipv4.addresses 192.0.2.10/24 \
  ipv4.gateway 192.0.2.1 \
  ipv4.dns '192.0.2.53 192.0.2.54' \
  ipv4.dns-search 'example.org' \
  ipv6.method auto
```

Bestehende Verbindung ändern:

```bash
sudo nmcli con mod lan-static \
  ipv4.addresses 192.0.2.10/24 \
  ipv4.gateway 192.0.2.1 \
  ipv4.dns '192.0.2.53 192.0.2.54' \
  ipv4.method manual
```

Aktivieren:

```bash
sudo nmcli con up lan-static
```

Zusätzliche Adresse:

```bash
sudo nmcli con mod lan-static +ipv4.addresses 192.0.2.11/24
sudo nmcli con mod lan-static -ipv4.addresses 192.0.2.11/24
```

Keine Default Route:

```bash
sudo nmcli con mod storage ipv4.never-default yes ipv6.never-default yes
```

Routen:

```bash
sudo nmcli con mod lan-static +ipv4.routes '198.51.100.0/24 192.0.2.254 100'
```

Autoconnect:

```bash
sudo nmcli con mod lan-static connection.autoconnect yes
```

Checkpoints/rollback, sofern Version unterstützt:

```bash
sudo nmcli device checkpoint --timeout 60 enp1s0
```

Alternativ `nmcli networking off/on` nicht remote ohne Konsole.

Verbindung löschen:

```bash
sudo nmcli con delete lan-static
```

Dateien befinden sich modern häufig unter:

```text
/etc/NetworkManager/system-connections/*.nmconnection
```

Rechte typischerweise `600`.

## WLAN mit NetworkManager

Funkstatus:

```bash
nmcli radio
nmcli radio wifi on
rfkill list
sudo rfkill unblock wifi
```

Scan:

```bash
nmcli device wifi list --rescan yes
```

WPA2/WPA3-Personal verbinden:

```bash
nmcli device wifi connect 'SSID' password 'PASSWORT'
```

Sicherer ohne Passwort in Prozessliste/History:

```bash
nmcli --ask device wifi connect 'SSID'
```

Interface angeben:

```bash
nmcli --ask device wifi connect 'SSID' ifname wlp2s0
```

Profil:

```bash
nmcli con show
nmcli con show 'SSID'
nmcli con up 'SSID'
```

WPA3-SAE erzwingen, abhängig von Backend/Version:

```bash
sudo nmcli con mod 'SSID' 802-11-wireless-security.key-mgmt sae
```

Hidden SSID:

```bash
nmcli --ask device wifi connect 'SSID' hidden yes
```

Unternehmens-WLAN EAP-TTLS/PEAP muss CA-/Servernamen korrekt validieren. Beispielstruktur:

```bash
sudo nmcli con add type wifi ifname wlp2s0 con-name corp ssid CORP
sudo nmcli con mod corp \
  wifi-sec.key-mgmt wpa-eap \
  802-1x.eap peap \
  802-1x.identity 'alice@example.org' \
  802-1x.phase2-auth mschapv2 \
  802-1x.ca-cert /etc/pki/ca-trust/source/anchors/corp-ca.pem \
  802-1x.domain-suffix-match radius.example.org
```

Passwort über Secret Agent/`nmcli --ask`, nicht im Klartextskript.

Signal/Verbindung:

```bash
iw dev wlp2s0 link
iw dev wlp2s0 station dump
nmcli -f IN-USE,SSID,BSSID,CHAN,RATE,SIGNAL,SECURITY dev wifi
```

## wpa_supplicant direkt

NetworkManager nutzt je System selbst wpa_supplicant oder iwd. Nicht parallel zwei Manager auf dasselbe Interface loslassen.

Konfiguration generieren:

```bash
wpa_passphrase 'SSID'
```

Mit Passwort per stdin:

```bash
wpa_passphrase 'SSID' 'PASSWORT' | sudo tee /etc/wpa_supplicant/wpa_supplicant-wlp2s0.conf >/dev/null
sudo chmod 600 /etc/wpa_supplicant/wpa_supplicant-wlp2s0.conf
```

Das Ergebnis enthält häufig einen kommentierten Klartext-PSK; Kommentar entfernen.

Beispiel:

```ini
ctrl_interface=DIR=/run/wpa_supplicant GROUP=wheel
update_config=0
country=DE

network={
    ssid="MEIN-WLAN"
    psk=HASHWERT
    key_mgmt=WPA-PSK SAE
    ieee80211w=1
}
```

Start:

```bash
sudo wpa_supplicant -B -i wlp2s0 \
  -c /etc/wpa_supplicant/wpa_supplicant-wlp2s0.conf
```

Debug im Vordergrund:

```bash
sudo wpa_supplicant -dd -i wlp2s0 -c /etc/wpa_supplicant/wpa_supplicant-wlp2s0.conf
```

Steuerung:

```bash
sudo wpa_cli -i wlp2s0 status
sudo wpa_cli -i wlp2s0 scan
sudo wpa_cli -i wlp2s0 scan_results
sudo wpa_cli -i wlp2s0 reassociate
```

Danach DHCP, z. B. je Distribution:

```bash
sudo dhclient -v wlp2s0
```

Oder statisch mit `ip addr`/`ip route`. `wpa_supplicant` selbst vergibt keine IP-Adresse.

> [!danger]
> Bei 802.1X niemals Zertifikatsprüfung mit leeren/unsicheren CA-Optionen umgehen. Sonst kann ein falscher Access Point Zugangsdaten abgreifen.

## systemd-networkd

Aktivierung nur, wenn nicht NetworkManager dasselbe Interface verwaltet:

```bash
sudo systemctl enable --now systemd-networkd
```

Statisch:

```ini
# /etc/systemd/network/20-lan.network
[Match]
Name=enp1s0

[Network]
Address=192.0.2.10/24
Gateway=192.0.2.1
DNS=192.0.2.53
Domains=example.org
IPv6AcceptRA=yes
```

DHCP:

```ini
[Match]
Name=enp1s0

[Network]
DHCP=yes
IPv6AcceptRA=yes
```

Linkoptionen:

```ini
# /etc/systemd/network/10-lan.link
[Match]
MACAddress=00:11:22:33:44:55

[Link]
Name=lan0
MTUBytes=1500
```

Reload/Reconfigure:

```bash
sudo networkctl reload
sudo networkctl reconfigure enp1s0
networkctl status enp1s0
```

Logs:

```bash
journalctl -u systemd-networkd -b
```

## Netplan

Netplan rendert je Konfiguration für NetworkManager oder networkd.

DHCP:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp1s0:
      dhcp4: true
      dhcp6: true
```

Statisch:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp1s0:
      addresses:
        - 192.0.2.10/24
      routes:
        - to: default
          via: 192.0.2.1
      nameservers:
        addresses: [192.0.2.53, 192.0.2.54]
        search: [example.org]
```

Sicher testen:

```bash
sudo netplan generate
sudo netplan try
sudo netplan apply
```

`netplan try` bietet einen automatischen Rückfall, ist für Remoteänderungen besonders wichtig.

## VLAN, Bridge, Bond und Team

### Temporäres VLAN mit ip

```bash
sudo ip link add link enp1s0 name enp1s0.100 type vlan id 100
sudo ip link set enp1s0 up
sudo ip link set enp1s0.100 up
sudo ip addr add 192.0.2.10/24 dev enp1s0.100
```

NetworkManager:

```bash
sudo nmcli con add type vlan con-name vlan100 \
  ifname enp1s0.100 dev enp1s0 id 100 \
  ipv4.method manual ipv4.addresses 192.0.2.10/24 ipv4.gateway 192.0.2.1
```

### Bridge

```bash
sudo nmcli con add type bridge ifname br0 con-name br0
sudo nmcli con add type ethernet ifname enp1s0 master br0 con-name br0-port
sudo nmcli con mod br0 ipv4.method auto ipv6.method auto
sudo nmcli con up br0
```

IP gehört auf Bridge, nicht zusätzlich auf Slave-Port.

Temporär mit `ip`:

```bash
sudo ip link add br0 type bridge
sudo ip link set enp1s0 master br0
sudo ip link set enp1s0 up
sudo ip link set br0 up
```

### Bond

```bash
sudo nmcli con add type bond ifname bond0 con-name bond0 bond.options 'mode=active-backup,miimon=100'
sudo nmcli con add type ethernet ifname enp1s0 master bond0 con-name bond0-enp1s0
sudo nmcli con add type ethernet ifname enp2s0 master bond0 con-name bond0-enp2s0
```

802.3ad/LACP benötigt passende Switchkonfiguration:

```text
mode=802.3ad,lacp_rate=fast,miimon=100
```

Status:

```bash
cat /proc/net/bonding/bond0
```

`teamd`/teaming gilt in manchen Enterprise-Umgebungen als legacy gegenüber Bonding; Distributionsstand prüfen.

## DNS mit systemd-resolved

```bash
resolvectl status
resolvectl query example.org
resolvectl dns enp1s0 192.0.2.53 192.0.2.54
resolvectl domain enp1s0 example.org
resolvectl flush-caches
resolvectl statistics
```

Routing-Domain für Split DNS:

```bash
sudo resolvectl domain tun0 '~corp.example.org'
sudo resolvectl dns tun0 10.10.0.53
```

`~.` markiert eine Route für alle Domains und kann VPN-DNS priorisieren.

`/etc/resolv.conf` prüfen:

```bash
readlink -f /etc/resolv.conf
cat /etc/resolv.conf
```

Nicht blind bearbeiten, wenn es von NetworkManager/resolved erzeugt wird.

NetworkManager DNS:

```bash
nmcli con mod lan-static ipv4.ignore-auto-dns yes
nmcli con mod lan-static ipv4.dns '192.0.2.53 192.0.2.54'
nmcli con up lan-static
```

## Routing und Policy Routing

Mehrere Tabellen:

```bash
ip rule
ip route show table all
```

Beispiel Quelle → eigene Tabelle:

```bash
echo '100 uplink2' | sudo tee -a /etc/iproute2/rt_tables
sudo ip route add default via 198.51.100.1 dev enp2s0 table uplink2
sudo ip route add 198.51.100.0/24 dev enp2s0 src 198.51.100.10 table uplink2
sudo ip rule add from 198.51.100.10/32 table uplink2 priority 1000
```

Persistenz über NetworkManager/networkd konfigurieren, nicht nur Runtime.

Forwarding:

```bash
sysctl net.ipv4.ip_forward
sudo sysctl -w net.ipv4.ip_forward=1
sysctl net.ipv6.conf.all.forwarding
```

Dauerhaft:

```ini
# /etc/sysctl.d/90-router.conf
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
```

Router Advertisements und IPv6-Forwarding interagieren; Router-/Hostrolle bewusst konfigurieren.

Reverse Path Filter kann Multihoming/asymmetrisches Routing stören:

```bash
sysctl net.ipv4.conf.all.rp_filter
```

Nicht pauschal deaktivieren; Topologie und Securitywirkung verstehen.

## MTU, Offloads und Performance

```bash
ip link show dev enp1s0
sudo ip link set dev enp1s0 mtu 9000
```

Jumbo Frames nur Ende-zu-Ende im Segment.

Path MTU testen:

```bash
ping -M do -s 1472 192.0.2.1       # IPv4: 1472 + 28 = 1500
tracepath example.org
```

IPv6:

```bash
tracepath6 example.org
```

Offloads:

```bash
ethtool -k enp1s0
sudo ethtool -K enp1s0 gro off gso off tso off
```

Offloads nur zur Diagnose temporär deaktivieren; Performanceeinbruch möglich.

Link:

```bash
ethtool enp1s0
ethtool --show-eee enp1s0
```

Durchsatz:

```bash
iperf3 -s
iperf3 -c server
iperf3 -c server -R
iperf3 -c server -P 4
```

## Serverdienste und Listener

```bash
ss -tulpn
ss -tan state listening
ss -s
```

Konkreter Port:

```bash
sudo ss -ltnp 'sport = :443'
sudo lsof -iTCP:443 -sTCP:LISTEN -P -n
```

Bind-Adresse:

```text
127.0.0.1:PORT  nur lokal IPv4
::1:PORT        nur lokal IPv6
0.0.0.0:PORT    alle IPv4-Adressen
[::]:PORT       alle IPv6, je sysctl eventuell auch IPv4-mapped
```

Clienttest:

```bash
nc -vz server 443
curl -vk https://server/
openssl s_client -connect server:443 -servername server </dev/null
```

UDP ist verbindungslos; `nc -u` beweist weniger als ein Protokolltest oder Mitschnitt.

## Firewall

firewalld:

```bash
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --zone=public --list-all
sudo firewall-cmd --permanent --zone=public --add-service=https
sudo firewall-cmd --reload
```

nftables:

```bash
sudo nft list ruleset
sudo nft monitor trace
```

iptables kann ein Kompatibilitätsfrontend zu nftables sein; Backend prüfen:

```bash
iptables --version
```

Forwarding/NAT muss mit Routing, conntrack und Zonen zusammenpassen.

## Diagnose und Mitschnitt

Basis:

```bash
ip -br link
ip -br addr
ip route get 1.1.1.1
ip neigh
resolvectl status
ping -c 3 192.0.2.1
ping -c 3 1.1.1.1
getent ahosts example.org
curl -v https://example.org/
```

Pakete:

```bash
sudo tcpdump -ni any host 192.0.2.10
sudo tcpdump -ni enp1s0 'tcp port 443'
sudo tcpdump -ni enp1s0 -w diagnose.pcapng 'host 192.0.2.10'
```

NetworkManager:

```bash
journalctl -u NetworkManager -b
nmcli general logging level DEBUG domains ALL
# nach Diagnose zurücksetzen
nmcli general logging level INFO domains DEFAULT
```

Kernel:

```bash
journalctl -k -b | grep -Ei 'link|firmware|timeout|reset|net|wifi'
ip -s link
ethtool -S enp1s0
```

DHCP:

```bash
journalctl -b | grep -Ei 'dhcp|lease'
sudo tcpdump -ni enp1s0 -vv 'port 67 or port 68'
```

DNS:

```bash
resolvectl query example.org
dig @192.0.2.53 example.org A +noall +answer
sudo tcpdump -ni any 'port 53'
```

TCP:

```bash
ss -ti dst 203.0.113.10
sudo tcpdump -ni any 'host 203.0.113.10 and tcp port 443'
```

## Persistenz- und Abnahmecheck

```text
[ ] Genau ein Manager verwaltet jedes Interface
[ ] Laufzeit und persistente Konfiguration stimmen überein
[ ] Reconnect/Reboot getestet
[ ] IPv4 und IPv6 getrennt geprüft
[ ] DNS-Split/Domainrouting dokumentiert
[ ] VLAN/Bridge/Bond am Switch abgestimmt
[ ] MTU Ende-zu-Ende
[ ] Firewall/Listener und SELinux geprüft
[ ] Zeit/NTP synchron
[ ] Konfigurationsbackup und Out-of-Band-Rollback vorhanden
```

## Quellen
- [NetworkManager Documentation](https://networkmanager.dev/docs/)
- [iproute2 Manual](https://man7.org/linux/man-pages/man8/ip.8.html)
- [wpa_supplicant Documentation](https://w1.fi/wpa_supplicant/)
- [systemd-networkd](https://www.freedesktop.org/software/systemd/man/latest/systemd-networkd.html)

## Verwandte Notizen
- [[Netzwerk-Konfiguration – Cheatsheet]]
- [[Wireshark – Cheatsheet]]
- [[firewalld – Cheatsheet]]
- [[SSH – Cheatsheet]]
