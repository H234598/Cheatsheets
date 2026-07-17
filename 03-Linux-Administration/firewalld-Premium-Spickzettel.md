---
title: "firewalld – Premium-Spickzettel"
aliases: ["firewall-cmd Cheatsheet", "Fedora Firewall", "RHEL firewalld"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [firewalld, firewall, nftables, fedora, rhel, network-security]
source: "https://firewalld.org/documentation/"
---

# firewalld – Premium-Spickzettel

> [!abstract] Zweck
> Ausführliche Referenz für firewalld: Zonen, Interfaces, Services, Ports, Runtime/Permanent, Rich Rules, Policies, NAT, Logging, nftables-Unterbau und Diagnose.

> [!danger]
> Firewalländerungen auf Remote-Systemen immer mit zweiter Sitzung, zeitlich begrenztem Rückfall oder Out-of-band-Konsole durchführen. Quellbereich minimal halten und bestehende SSH-/Managementverbindung nicht unabsichtlich abschneiden.

## Inhalt

- [[#Grundmodell]]
- [[#Status und aktive Zonen]]
- [[#Runtime versus Permanent]]
- [[#Interfaces und Sources]]
- [[#Services und Ports]]
- [[#Rich Rules]]
- [[#Policies und Inter-Zone-Verkehr]]
- [[#Masquerading und Port Forwarding]]
- [[#Logging und Panic Mode]]
- [[#nftables-Unterbau]]
- [[#Diagnose-Reihenfolge]]

## Grundmodell

```text
Paket
  → Zuordnung zu Zone anhand Interface oder Source
  → Zone: Services/Ports/Rich Rules
  → Policies für Verkehr zwischen Zonen
  → nftables-Regeln im Kernel
```

Eine Zone beschreibt Vertrauensniveau/Regelsatz, nicht automatisch ein physisches Netz.

Typische Zonen können sein:

```text
drop, block, public, external, dmz, work, home, internal, trusted
```

Semantik und lokale Anpassungen mit `firewall-cmd --get-zones` und Zoneinfo prüfen.

## Status und aktive Zonen

```bash
firewall-cmd --state
systemctl status firewalld
firewall-cmd --get-default-zone
firewall-cmd --get-active-zones
firewall-cmd --get-zones
firewall-cmd --zone=public --list-all
firewall-cmd --list-all-zones
```

Konfiguration validieren:

```bash
sudo firewall-cmd --check-config
```

Backend/Details:

```bash
firewall-cmd --get-log-denied
sudo nft list ruleset
```

## Runtime versus Permanent

| Modus | Wirkung |
|---|---|
| Runtime | sofort, geht bei Reload/Neustart verloren |
| Permanent | gespeichert, wirkt nach Reload/Neustart |

Runtime testen, dann übernehmen:

```bash
sudo firewall-cmd --zone=public --add-service=https
# testen
sudo firewall-cmd --runtime-to-permanent
```

Permanent zuerst:

```bash
sudo firewall-cmd --permanent --zone=public --add-service=https
sudo firewall-cmd --reload
```

Vergleichen:

```bash
firewall-cmd --zone=public --list-all
firewall-cmd --permanent --zone=public --list-all
```

> [!warning]
> `--reload` verwirft nicht persistierte Runtimeänderungen. Vor Reload beide Zustände vergleichen.

## Interfaces und Sources

Interface einer Zone zuordnen:

```bash
sudo firewall-cmd --zone=internal --change-interface=eth1
```

Permanent:

```bash
sudo firewall-cmd --permanent --zone=internal --change-interface=eth1
sudo firewall-cmd --reload
```

Quellnetz:

```bash
sudo firewall-cmd --zone=internal --add-source=10.20.0.0/16
```

Anzeigen:

```bash
firewall-cmd --get-zone-of-interface=eth1
firewall-cmd --get-zone-of-source=10.20.0.0/16
firewall-cmd --zone=internal --list-interfaces
firewall-cmd --zone=internal --list-sources
```

> [!important]
> NetworkManager kann Zone in einem Connection Profile speichern. Bei unerwarteter Rückzuordnung `nmcli connection show` und `connection.zone` prüfen.

```bash
nmcli -f NAME,DEVICE,connection.zone connection show
sudo nmcli connection modify 'System eth1' connection.zone internal
sudo nmcli connection up 'System eth1'
```

## Services und Ports

Services sind XML-Definitionen mit Ports/Protokollen und optional Modulen/Helpern.

```bash
firewall-cmd --get-services
firewall-cmd --info-service=https
```

Service erlauben:

```bash
sudo firewall-cmd --zone=public --add-service=https
sudo firewall-cmd --zone=public --remove-service=https
```

Port:

```bash
sudo firewall-cmd --zone=public --add-port=8443/tcp
sudo firewall-cmd --zone=public --add-port=60000-60100/udp
```

Abfragen:

```bash
firewall-cmd --zone=public --query-service=https
firewall-cmd --zone=public --query-port=8443/tcp
```

### Eigenen Service definieren

```bash
sudo firewall-cmd --permanent --new-service=myapp
sudo firewall-cmd --permanent --service=myapp --set-description='Meine Anwendung'
sudo firewall-cmd --permanent --service=myapp --add-port=8443/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --zone=internal --add-service=myapp --permanent
sudo firewall-cmd --reload
```

Services sind wartbarer als verteilte Portlisten.

## Rich Rules

Beispiel: HTTPS nur aus Netz:

```bash
sudo firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="192.0.2.0/24" service name="https" accept'
```

Mit Logging und Limit:

```bash
sudo firewall-cmd --zone=public --add-rich-rule='rule family="ipv4" source address="198.51.100.0/24" port port="8443" protocol="tcp" log prefix="myapp-denied " limit value="5/m" reject'
```

Anzeigen:

```bash
firewall-cmd --zone=public --list-rich-rules
```

Entfernen exakt mit derselben Zeichenfolge oder Konfiguration exportieren.

> [!tip]
> Rich Rules nur verwenden, wenn Service/Port + Zone nicht ausreicht. Komplexe Regelmengen brauchen Design, Kommentare, Tests und gegebenenfalls native nftables-Verwaltung statt unübersichtlicher Einzelbefehle.

## Policies und Inter-Zone-Verkehr

Policies modellieren Verkehr zwischen Zonen, zum Beispiel internes Netz → externes Netz.

Grundkonzept:

```text
Ingress Zone(s) → Policy-Regeln → Egress Zone(s)
```

Befehle:

```bash
firewall-cmd --get-policies
firewall-cmd --info-policy POLICY
```

Beispielstruktur, genaue Optionen mit installierter Version prüfen:

```bash
sudo firewall-cmd --permanent --new-policy internal-to-external
sudo firewall-cmd --permanent --policy internal-to-external --add-ingress-zone internal
sudo firewall-cmd --permanent --policy internal-to-external --add-egress-zone external
sudo firewall-cmd --permanent --policy internal-to-external --set-target ACCEPT
sudo firewall-cmd --reload
```

Breites `ACCEPT` nur nach Sicherheitsbewertung; bevorzugt benötigte Services/Ports.

## Masquerading und Port Forwarding

Masquerade:

```bash
sudo firewall-cmd --zone=external --add-masquerade
```

Port Forward:

```bash
sudo firewall-cmd --zone=external \
  --add-forward-port=port=443:proto=tcp:toport=8443:toaddr=10.0.0.10
```

Zusätzlich:

- IP-Forwarding im Kernel
- Rückroute
- Zielhostfirewall
- SELinux des Zielservices
- Hairpin/NAT-Sonderfälle
- IPv4/IPv6 separat

prüfen.

Forwarding:

```bash
sysctl net.ipv4.ip_forward
sysctl net.ipv6.conf.all.forwarding
```

Dauerhaft unter `/etc/sysctl.d/*.conf` konfigurieren.

## Logging und Panic Mode

Verworfene Pakete loggen:

```bash
firewall-cmd --get-log-denied
sudo firewall-cmd --set-log-denied=unicast
```

Optionen je Version, zum Beispiel `off`, `all`, `unicast`, `broadcast`, `multicast`.

Logs:

```bash
journalctl -k -f
journalctl -u firewalld -b
```

Panic Mode blockiert Netzwerkverkehr weitgehend:

```bash
sudo firewall-cmd --panic-on
firewall-cmd --query-panic
sudo firewall-cmd --panic-off
```

> [!danger]
> Auf Remotehost kann Panic Mode sofort die Sitzung trennen. Nur mit Out-of-band-Zugriff oder lokalem Notfallplan.

## nftables-Unterbau

```bash
sudo nft list ruleset
sudo nft -a list ruleset
```

Firewalld generiert/verwaltert Regeln. Nicht manuell darin editieren. Eigene native nftables-Regeln nur über klar getrennten, unterstützten Mechanismus und Prioritäten integrieren.

Ports/Listener:

```bash
ss -lntup
```

Firewallfreigabe ohne Listener liefert weiterhin keine Verbindung; Listener ohne Freigabe ist von außen blockiert.

## Diagnose-Reihenfolge

### Verbindung blockiert

```bash
ip -brief address
ip route get ZIEL
firewall-cmd --get-active-zones
firewall-cmd --zone=ZONE --list-all
ss -lntup
journalctl -k --since '-10 min'
```

Dann:

1. erreicht Paket den Host? `tcpdump -ni any port PORT`
2. richtige Zone für Interface/Source?
3. Service/Port Runtime und Permanent?
4. Anwendung hört auf richtiger Adresse/Familie?
5. SELinux erlaubt Bind/Verbindung?
6. Rückroute und Zwischenfirewall?
7. IPv4 versus IPv6?

### Änderung wirkt nach Reboot nicht

```bash
firewall-cmd --zone=public --list-all
firewall-cmd --permanent --zone=public --list-all
```

Runtime nicht gespeichert oder NetworkManager ordnet andere Zone zu.

### Reload schlägt fehl

```bash
sudo firewall-cmd --check-config
journalctl -u firewalld -b -n 200
```

XML/Service/Zone/Policy-Konfiguration unter `/etc/firewalld` prüfen; Sicherung vor manueller Bearbeitung.

### Remote sichere Änderung

```bash
# bestehende Zone und SSH-Regel dokumentieren
firewall-cmd --get-active-zones
firewall-cmd --zone=ZONE --list-all

# neue Regel nur runtime
sudo firewall-cmd --zone=ZONE --add-service=NEUER_SERVICE

# zweite Verbindung testen
# erst dann:
sudo firewall-cmd --runtime-to-permanent
```

## Quellen
- [firewalld Documentation](https://firewalld.org/documentation/)
- [firewall-cmd Manual](https://firewalld.org/documentation/man-pages/firewall-cmd.html)
- [Fedora firewalld Quick Docs](https://docs.fedoraproject.org/en-US/quick-docs/firewalld/)
- [RHEL firewalld and nftables](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_firewalls_and_packet_filters/)

## Verwandte Notizen
- [[Fedora-RHEL-Premium-Spickzettel]]
- [[SELinux-Premium-Spickzettel]]
- [[Netzwerk-Konfiguration-Linux-Windows-BSD]]
- [[pfSense-Premium-Spickzettel]]
