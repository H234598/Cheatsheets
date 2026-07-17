---
title: "Wireshark – Premium-Spickzettel"
aliases: ["Wireshark Cheatsheet", "TShark", "Packet Capture Analyse"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [wireshark, tshark, pcap, network, diagnose, security]
source: "https://www.wireshark.org/docs/wsug_html_chunked/"
---

# Wireshark – Premium-Spickzettel

> [!abstract] Zweck
> Sehr ausführliche Referenz für rechtssichere Paketmitschnitte, Interfaces, Capture- versus Display-Filter, TCP/DNS/HTTP/TLS-Analyse, Streams, Expert Information, TShark, Ringbuffer, Remote Capture, Export und systematische Diagnose.

> [!danger] Datenschutz und Berechtigung
> Paketmitschnitte können Zugangsdaten, Cookies, Tokens, interne Hostnamen, personenbezogene Daten und vollständige Inhalte enthalten. Nur in Netzen/Systemen mitschneiden, für die eine ausdrückliche Berechtigung besteht. Erfassungsumfang und Aufbewahrung minimieren, Dateien schützen und kontrolliert löschen.

## Inhalt

- [[#Grundmodell]]
- [[#Installation und Capture-Rechte]]
- [[#Interface und Mitschnittpunkt wählen]]
- [[#Capture- und Display-Filter]]
- [[#Wichtige Display-Filter]]
- [[#Ansichten, Spalten und Zeit]]
- [[#TCP analysieren]]
- [[#DNS, DHCP und ICMP]]
- [[#HTTP, TLS und QUIC]]
- [[#Streams und Objekte]]
- [[#Expert Information und Statistiken]]
- [[#TShark und dumpcap]]
- [[#Ringbuffer und Langzeitcapture]]
- [[#Remote Capture]]
- [[#TLS-Entschlüsselung eigener Sitzungen]]
- [[#Dateien schützen und anonymisieren]]
- [[#Diagnose-Playbooks]]
- [[#Schnellreferenz]]

## Grundmodell

Ein Mitschnitt beantwortet:

```text
Wer sendet wann welches Protokoll an wen,
was kommt zurück,
wie lange dauert es,
wo treten Retransmits, Fehler oder Abbrüche auf?
```

Wireshark zeigt drei Hauptbereiche:

1. Paketliste.
2. Protokollbaum des ausgewählten Pakets.
3. Rohbytes.

Wichtige Begriffe:

| Begriff | Bedeutung |
|---|---|
| Frame | aufgezeichnete Link-Layer-Einheit |
| Packet | häufig IP-Paket innerhalb des Frames |
| Segment/Datagramm | TCP-/UDP-Transporteinheit |
| Stream | logisch zusammengehörige Kommunikation |
| Capture Filter | begrenzt, was aufgenommen wird; libpcap/BPF-Syntax |
| Display Filter | begrenzt, was angezeigt wird; Wireshark-Syntax |
| Dissector | Protokollparser |
| pcap/pcapng | Capture-Dateiformate; pcapng speichert mehr Metadaten |

## Installation und Capture-Rechte

Fedora:

```bash
sudo dnf install wireshark wireshark-cli
```

Debian/Ubuntu:

```bash
sudo apt install wireshark tshark
```

Rechte werden distributionsspezifisch über `dumpcap`, Capabilities und Gruppe geregelt. Prüfen:

```bash
command -v dumpcap
getcap "$(command -v dumpcap)"
groups
```

Interfaces:

```bash
dumpcap -D
tshark -D
```

> [!warning]
> Wireshark nicht pauschal als Root starten. `dumpcap` ist dafür ausgelegt, die privilegierte Erfassung vom umfangreichen GUI-/Parserprozess zu trennen.

Windows: Npcap wird normalerweise mitinstalliert. Bei Installeroptionen Raw 802.11, Adminbeschränkung und WinPcap-Kompatibilität bewusst wählen.

## Interface und Mitschnittpunkt wählen

Die wichtigste Frage lautet nicht „welcher Filter?“, sondern „**wo** sieht man den relevanten Verkehr?“

Mögliche Punkte:

- Clientinterface
- Serverinterface
- Router/Firewall intern und extern
- Switch-SPAN/Mirror-Port
- TAP
- VM-vSwitch/Bridge
- Container-Namespace
- VPN-Tunnelinterface
- WLAN-Monitor-Interface

`any` unter Linux:

```bash
sudo tshark -i any
```

Vorteil: mehrere Interfaces. Nachteile: Link-Layer-Details/Offloaddarstellung eingeschränkt, möglicherweise Duplikate.

Offloads können lokal scheinbar falsche Checksummen oder große Segmente erzeugen. Hinweise:

- TCP Checksum „incorrect“ am sendenden Host kann durch Hardware-Offload entstehen.
- GRO/LRO/TSO verändert lokale Paketdarstellung.
- Ein Capture außerhalb des Hosts zeigt tatsächlich gesendete Frames.

Zeit synchronisieren, wenn mehrere Mitschnittpunkte verglichen werden.

## Capture- und Display-Filter

### Capture Filter – BPF/libpcap

Beim Start, reduziert Datenmenge:

```text
host 192.0.2.10
net 192.0.2.0/24
port 443
tcp port 443
udp port 53
src host 192.0.2.10 and dst port 443
host 192.0.2.10 and not port 22
ip6 and tcp port 443
```

CLI:

```bash
sudo dumpcap -i enp1s0 -f 'host 192.0.2.10 and port 443' -w capture.pcapng
```

### Display Filter – Wireshark

Nach Aufnahme, sehr mächtig:

```text
ip.addr == 192.0.2.10
tcp.port == 443
dns
http
quic
tls.handshake
```

> [!important]
> `tcp port 443` ist Capture-Filter-Syntax. `tcp.port == 443` ist Display-Filter-Syntax. Die Sprachen sind nicht austauschbar.

Logische Operatoren:

```text
and
or
not
&&
||
!
```

Vergleiche:

```text
== != > >= < <=
contains
matches
in
```

Beispiele:

```text
http.host contains "example"
tcp.port in {80 443 8080}
frame matches "(?i)token"
```

## Wichtige Display-Filter

### IP und Ethernet

```text
ip.addr == 192.0.2.10
ip.src == 192.0.2.10
ip.dst == 192.0.2.10
ipv6.addr == 2001:db8::10
eth.addr == 00:11:22:33:44:55
vlan.id == 100
arp
icmp
icmpv6
```

### TCP

```text
tcp.port == 443
tcp.flags.syn == 1
tcp.flags.syn == 1 and tcp.flags.ack == 0
tcp.flags.reset == 1
tcp.analysis.retransmission
tcp.analysis.fast_retransmission
tcp.analysis.duplicate_ack
tcp.analysis.out_of_order
tcp.analysis.zero_window
tcp.analysis.window_full
tcp.analysis.lost_segment
tcp.stream == 7
```

Nur Verbindungsaufbau zu Ziel:

```text
ip.dst == 203.0.113.10 and tcp.dstport == 443 and tcp.flags.syn == 1 and tcp.flags.ack == 0
```

### UDP

```text
udp.port == 53
udp.length > 1200
```

UDP kennt keine Verbindungsbestätigung. ICMP-Fehler und Anwendungsebene einbeziehen.

### DNS

```text
dns
dns.flags.response == 0
dns.flags.response == 1
dns.flags.rcode != 0
dns.qry.name == "example.org"
dns.qry.type == 1
dns.qry.type == 28
dns.time > 0.1
```

### DHCP

Wireshark verwendet je Version `dhcp`/`bootp`-Felder:

```text
dhcp || bootp
dhcp.option.dhcp == 1
dhcp.option.dhcp == 2
dhcp.option.dhcp == 3
dhcp.option.dhcp == 5
```

Feldnamen über Autovervollständigung/Display Filter Reference prüfen.

### HTTP

```text
http.request
http.response
http.request.method == "POST"
http.host == "example.org"
http.response.code >= 400
http.time > 1
http.request.uri contains "/api/"
```

HTTP/2:

```text
http2
http2.headers.status >= 400
```

### TLS

```text
tls
tls.handshake.type == 1
tls.handshake.type == 2
tls.handshake.extensions_server_name == "example.org"
tls.alert_message
tls.record.content_type == 21
```

### Frame und Zeit

```text
frame.number == 123
frame.len > 1500
frame.time_delta > 1
frame.time_relative > 10
frame.interface_id == 1
```

Filterbutton/Autovervollständigung hilft, gültige Feldnamen der installierten Version zu finden.

## Ansichten, Spalten und Zeit

Nützliche Spalten:

- Source/Destination
- Protocol
- Length
- TCP Stream
- `tcp.time_delta`
- `tcp.analysis.ack_rtt`
- HTTP Host/URI/Status
- TLS SNI
- DSCP
- VLAN ID

Feld als Spalte: Protokollbaum → Rechtsklick → **Apply as Column**.

Zeitdarstellungen:

- Absolute Date and Time
- Seconds Since Beginning of Capture
- Seconds Since Previous Displayed Packet
- UTC

Referenzzeit setzen: Paket → **Set/Unset Time Reference**. Für Ursache/Folge sehr hilfreich.

Namensauflösung kann Analyse erleichtern, aber externe DNS-Anfragen erzeugen und IPs verschleiern. Für belastbare Dokumentation oft zunächst numerisch arbeiten.

## TCP analysieren

### Drei-Wege-Handshake

```text
Client → Server  SYN
Server → Client  SYN,ACK
Client → Server  ACK
```

Interpretation:

| Sichtbar | Aussage |
|---|---|
| SYN, keine Antwort | Drop, falscher Pfad, Server nicht erreichbar oder Rückweg fehlt |
| SYN → RST | Host erreichbar, Port geschlossen/aktiv abgewiesen |
| SYN/SYN-ACK, kein ACK | Rückweg zum Client oder Clientpolicy problematisch |
| vollständiger Handshake, dann TLS/Appfehler | Netzwerkbasis steht; höhere Schicht prüfen |

Filter:

```text
tcp.flags.syn == 1 or tcp.flags.reset == 1
```

### Retransmissions

```text
tcp.analysis.retransmission or tcp.analysis.fast_retransmission
```

Nicht jede markierte Retransmission bedeutet Netzverlust; Capturepunkt, Out-of-Order und Offloads berücksichtigen.

Kontext:

- Wer retransmittiert?
- Kommt ACK verspätet?
- Häufen sich Ereignisse bei bestimmter Größe/Route?
- Receiver Window/Zero Window?
- RTT-Sprung?

### Reset

```text
tcp.flags.reset == 1
```

Bestimmen, welche Seite RST sendet und unmittelbar vorherige Pakete betrachten. Ursache kann Anwendung, Firewall, Load Balancer oder Portzustand sein.

### Window und RTT

```text
tcp.analysis.zero_window
tcp.analysis.window_full
tcp.analysis.ack_rtt > 0.2
```

Zero Window deutet auf empfangende Anwendung hin, die Daten nicht schnell genug liest; nicht automatisch Bandbreitenproblem.

### Graphen

- Statistics → TCP Stream Graphs → Time-Sequence
- Round Trip Time
- Throughput
- Window Scaling

Ein Stream muss ausgewählt sein.

## DNS, DHCP und ICMP

### DNS-Playbook

```text
1. Query gesendet?
2. An welchen Resolver?
3. Response vorhanden?
4. RCODE?
5. A/AAAA/CNAME korrekt?
6. Antwortzeit?
7. Fragmentierung/EDNS/TCP-Fallback?
```

Filter:

```text
dns.qry.name == "example.org" or dns.resp.name == "example.org"
```

### DHCPv4

```text
Discover → Offer → Request → ACK
```

Fehlt Offer: VLAN, Relay, Server oder Filter. Offer vorhanden, Request/ACK fehlt: Auswahl, Konflikt, Policy oder Rückweg.

### ICMP/ICMPv6

Nicht nur Echo:

- Destination Unreachable
- Fragmentation Needed / Packet Too Big
- Time Exceeded
- Neighbor Discovery
- Router Advertisement

```text
icmp.type == 3
icmpv6.type == 2
icmpv6.type in {133 134 135 136}
```

ICMPv6 pauschal zu blockieren beschädigt IPv6.

## HTTP, TLS und QUIC

### HTTP ohne TLS

Request/Response-Paar suchen:

```text
http.request or http.response
```

Response Time-Feld/„Time since request“ nutzen. Proxy-Header und Host beachten.

### TLS-Handshake

Vereinfachte Fragen:

1. TCP-Verbindung steht?
2. ClientHello mit SNI/ALPN?
3. ServerHello/Zertifikat?
4. TLS Alert?
5. Handshake abgeschlossen?
6. danach Anwendung/Close/Reset?

Filter:

```text
tls.handshake or tls.alert_message
```

SNI:

```text
tls.handshake.extensions_server_name
```

ALPN zeigt z. B. `h2` oder `http/1.1`.

Zertifikatsvalidierung geschieht beim Client; Wireshark zeigt Zertifikate, beurteilt aber nicht automatisch alle Truststore-/Hostname-Regeln der Anwendung.

### QUIC/HTTP3

QUIC läuft meist über UDP/443:

```text
quic or http3
udp.port == 443
```

Bei Blockade fällt Browser eventuell auf TCP/TLS/HTTP2 zurück. Beide Pfade vergleichen.

## Streams und Objekte

Stream folgen:

- Rechtsklick → Follow → TCP Stream
- UDP Stream
- HTTP Stream
- TLS Stream bei entschlüsselten Daten

Filter entsteht etwa:

```text
tcp.stream eq 7
```

Streaminhalt kann hochsensibel sein.

Objekte exportieren:

- File → Export Objects → HTTP/SMB/TFTP …

Nur bei eigener/berechtigter Analyse. Exportierte Dateien als potenziell schädlich behandeln und nicht ungeprüft öffnen.

## Expert Information und Statistiken

Menüs:

- Analyze → Expert Information
- Statistics → Protocol Hierarchy
- Statistics → Conversations
- Statistics → Endpoints
- Statistics → I/O Graphs
- Statistics → Flow Graph
- Statistics → Service Response Time

Expert-Meldungen sind Hinweise, keine endgültigen Diagnosen. Ein „Warning“ kann in der Topologie normal sein.

Conversations sortieren nach Bytes, Paketen oder Dauer; Endpoints identifiziert Top Talker.

I/O-Graph mit Filtern:

```text
tcp.analysis.retransmission
dns.flags.rcode != 0
http.response.code >= 500
```

## TShark und dumpcap

Interfaces:

```bash
tshark -D
dumpcap -D
```

Live anzeigen:

```bash
sudo tshark -i enp1s0
```

Capture Filter:

```bash
sudo tshark -i enp1s0 -f 'tcp port 443'
```

Display Filter live:

```bash
sudo tshark -i enp1s0 -Y 'tls.handshake'
```

`-Y` reduziert nicht die Aufnahme, nur Ausgabe/Verarbeitung. Für große Captures `-f` nutzen.

Datei lesen:

```bash
tshark -r capture.pcapng -Y 'dns.flags.rcode != 0'
```

Felder exportieren:

```bash
tshark -r capture.pcapng \
  -Y 'http.request' \
  -T fields \
  -E header=y -E separator=, -E quote=d \
  -e frame.time_epoch \
  -e ip.src \
  -e http.host \
  -e http.request.method \
  -e http.request.uri
```

JSON:

```bash
tshark -r capture.pcapng -Y dns -T json > dns.json
```

Statistik:

```bash
tshark -r capture.pcapng -q -z io,phs
tshark -r capture.pcapng -q -z conv,tcp
tshark -r capture.pcapng -q -z endpoints,ip
```

Capture mit dumpcap ist ressourcenschonend:

```bash
sudo dumpcap -i enp1s0 -f 'host 192.0.2.10' -w capture.pcapng
```

## Ringbuffer und Langzeitcapture

Nach Dateigröße rotieren:

```bash
sudo dumpcap -i enp1s0 \
  -b filesize:100000 \
  -b files:20 \
  -w /var/tmp/diag.pcapng
```

Nach Zeit:

```bash
sudo dumpcap -i enp1s0 \
  -b duration:300 \
  -b files:12 \
  -w /var/tmp/diag.pcapng
```

Automatisch stoppen:

```bash
sudo dumpcap -i enp1s0 -a duration:600 -w /var/tmp/diag.pcapng
```

Snap Length begrenzen:

```bash
sudo dumpcap -i enp1s0 -s 128 -w headers.pcapng
```

Dies reduziert Inhalte, kann aber Protokollanalyse verhindern. Datenschutz gegen Diagnosebedarf abwägen.

Speicherplatz überwachen und restriktive Rechte setzen:

```bash
umask 077
```

## Remote Capture

Sicheres Muster: `tcpdump` remote, Stream über SSH:

```bash
ssh host 'sudo tcpdump -U -s0 -w - -i eth0 "host 192.0.2.10"' \
  > remote.pcap
```

Direkt in Wireshark unter Linux:

```bash
ssh host 'sudo tcpdump -U -s0 -w - -i eth0 "tcp port 443"' |
  wireshark -k -i -
```

`sshdump`/extcap kann Remote-Capture integrieren. Sudo minimal auf genaues Capturekommando begrenzen; keine pauschale Root-Shell.

Switch-SPAN:

- Quelle/Richtung korrekt.
- Zielport nicht normal weiterverwenden.
- Überbuchung kann Pakete verlieren.
- VLAN-Tags können je Switchkonfiguration entfernt/erhalten werden.

## TLS-Entschlüsselung eigener Sitzungen

Moderne Browser/Clients können Session Keys über `SSLKEYLOGFILE` schreiben, sofern unterstützt:

```bash
export SSLKEYLOGFILE="$HOME/tls-keys.log"
firefox
```

In Wireshark: Preferences → Protocols → TLS → (Pre)-Master-Secret log filename.

> [!danger]
> Die Keylog-Datei ermöglicht die Entschlüsselung der zugehörigen Sitzungen. Wie einen privaten Schlüssel behandeln, nicht teilen und nach Analyse sicher löschen. Nur eigene oder ausdrücklich autorisierte Sessions entschlüsseln.

RSA-Private-Key-Entschlüsselung funktioniert bei modernem Forward Secrecy/TLS 1.3 nicht allgemein. Session Keys sind der praktische Weg für eigene Tests.

## Dateien schützen und anonymisieren

```bash
chmod 600 capture.pcapng
sha256sum capture.pcapng > capture.pcapng.sha256
```

Vor Weitergabe:

- zeitlich und per Filter zuschneiden
- irrelevante Pakete entfernen
- Payload minimieren
- IP/MAC/Hostnamen anonymisieren
- Kommentare/Interface-Namen prüfen
- Secrets/Tokens/Dateien suchen

Mit `editcap` zuschneiden:

```bash
editcap -A '2026-07-17 10:00:00' -B '2026-07-17 10:05:00' input.pcapng output.pcapng
```

Duplikate/Dateiformat je Bedarf:

```bash
editcap -F pcapng input.pcap output.pcapng
```

Anonymisierung ist schwierig, weil Protokolle Adressen mehrfach enthalten können. Spezialisierte Tools plus manuelle Prüfung verwenden.

## Diagnose-Playbooks

### „Serverport nicht erreichbar“

Filter:

```text
ip.addr == SERVER and tcp.port == PORT
```

1. SYN am Client?
2. SYN am Server?
3. SYN-ACK oder RST?
4. Antwort am Client?
5. Bei Handshake: TLS/App danach?
6. Bei asymmetrischem Pfad beide Seiten capturen.

### „DNS langsam“

```text
dns and dns.time > 0.1
```

- Query/Response paaren.
- Retries und mehrere Resolver erkennen.
- A/AAAA getrennt.
- UDP→TCP-Fallback.
- NXDOMAIN/SERVFAIL.
- VPN/Split-DNS.

### „Verbindung bricht bei großen Daten ab“

```text
icmp or icmpv6 or tcp.analysis.retransmission
```

- ICMP Fragmentation Needed / IPv6 Packet Too Big.
- MSS/MTU.
- Retransmissions ab bestimmter Segmentgröße.
- Tunnel-/VPN-Overhead.
- Offloadartefakte ausschließen.

### „Anwendung ist langsam“

1. DNS-Zeit.
2. TCP-Handshake/RTT.
3. TLS-Handshake.
4. Zeit bis erster Request/Response.
5. Server Think Time versus Übertragungszeit.
6. Retransmits/Window.
7. Parallelverbindungen/HTTP2/QUIC.

### „TLS funktioniert bei einem Client nicht“

```text
tls.handshake or tls.alert_message
```

Vergleichen:

- SNI
- TLS-Versionen/Cipher
- ALPN
- Zertifikatskette
- Alert Sender/Code
- Proxy/Inspection
- IPv4 versus IPv6 Ziel

## Schnellreferenz

```text
Capture: tcp port 443 and host 192.0.2.10
Display: tcp.port == 443 and ip.addr == 192.0.2.10
TCP SYN: tcp.flags.syn == 1
RST: tcp.flags.reset == 1
Retransmit: tcp.analysis.retransmission
DNS Fehler: dns.flags.rcode != 0
HTTP Fehler: http.response.code >= 400
TLS Alert: tls.alert_message
Stream: tcp.stream == N
```

```bash
dumpcap -D
sudo dumpcap -i enp1s0 -f 'host 192.0.2.10' -w diag.pcapng
tshark -r diag.pcapng -Y 'tcp.analysis.retransmission'
tshark -r diag.pcapng -q -z conv,tcp
editcap -A 'START' -B 'ENDE' input.pcapng output.pcapng
```

## Quellen
- [Wireshark User’s Guide](https://www.wireshark.org/docs/wsug_html_chunked/)
- [Wireshark Display Filter Reference](https://www.wireshark.org/docs/dfref/)
- [Wireshark Command Line Manuals](https://www.wireshark.org/docs/man-pages/)
- [pcap-filter Syntax](https://www.tcpdump.org/manpages/pcap-filter.7.html)

## Verwandte Notizen
- [[Netzwerk-Konfiguration – Premium-Spickzettel]]
- [[Linux-Netzwerk – Premium-Spickzettel]]
- [[MS RPC-Verbindungen – Premium-Spickzettel]]
- [[pfSense – Premium-Spickzettel]]
- [[OPNsense – Premium-Spickzettel]]
