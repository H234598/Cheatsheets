---
title: "Windows-Netzwerk – Premium-Spickzettel"
aliases: ["Windows Netzwerk einrichten", "PowerShell Netzwerk Cheatsheet", "netsh Netzwerk"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [windows, network, powershell, dns, routing, wifi]
source: "https://learn.microsoft.com/powershell/module/nettcpip/"
---

# Windows-Netzwerk – Premium-Spickzettel

> [!abstract] Zweck
> Ausführliche Windows-Netzwerkreferenz mit PowerShell, NetTCPIP, DNSClient, netsh, WLAN, statischen Adressen, Routen, Profilen, Firewall, Serverbindings, Reset, pktmon und Diagnose.

> [!danger] Remoteadministration
> IP, Gateway, DNS, Firewallprofil oder Adapter remote nur mit zweitem Verwaltungsweg ändern. Bei Windows Server gegebenenfalls Hypervisor-/iLO-/iDRAC-/KVM-Konsole bereithalten.

## Inhalt

- [[#Bestand aufnehmen]]
- [[#Adapter und Profile]]
- [[#IP-Adressen und DHCP]]
- [[#Routen]]
- [[#DNS]]
- [[#WLAN mit netsh]]
- [[#Firewall]]
- [[#Listener und Verbindungen]]
- [[#Teaming, VLAN und virtuelle Adapter]]
- [[#Reset und Reparatur]]
- [[#Mitschnitt und Diagnose]]
- [[#Abnahme]]

## Bestand aufnehmen

PowerShell als Administrator:

```powershell
Get-NetAdapter
Get-NetIPConfiguration
Get-NetIPAddress
Get-NetRoute
Get-DnsClientServerAddress
Get-NetConnectionProfile
Get-NetFirewallProfile
```

Kompakt:

```powershell
Get-NetIPConfiguration |
  Format-List InterfaceAlias,InterfaceIndex,IPv4Address,IPv6Address,IPv4DefaultGateway,DNSServer
```

Klassisch:

```cmd
ipconfig /all
route print
arp -a
netstat -ano
```

## Adapter und Profile

```powershell
Get-NetAdapter | Sort-Object ifIndex
Enable-NetAdapter -Name 'Ethernet' -Confirm:$false
Disable-NetAdapter -Name 'Ethernet' -Confirm:$false
Restart-NetAdapter -Name 'Ethernet'
```

Umbenennen:

```powershell
Rename-NetAdapter -Name 'Ethernet 2' -NewName 'LAN'
```

Link-/Treiberdetails:

```powershell
Get-NetAdapter -Name LAN | Format-List *
Get-NetAdapterAdvancedProperty -Name LAN
Get-NetAdapterStatistics -Name LAN
```

Netzwerkprofil:

```powershell
Get-NetConnectionProfile
Set-NetConnectionProfile -InterfaceAlias LAN -NetworkCategory Private
```

| Profil | Typische Policy |
|---|---|
| Public | restriktiv für fremde Netze |
| Private | vertrauenswürdiges internes Netz |
| DomainAuthenticated | automatisch bei AD-Domainkontakt |

DomainAuthenticated nicht manuell erzwingen; Erkennung hängt von Domain/DNS/Authentisierung ab.

## IP-Adressen und DHCP

Interfaceindex:

```powershell
Get-NetAdapter -Name LAN
```

Statisches IPv4:

```powershell
New-NetIPAddress `
  -InterfaceAlias 'LAN' `
  -IPAddress '192.0.2.10' `
  -PrefixLength 24 `
  -DefaultGateway '192.0.2.1'
```

DNS:

```powershell
Set-DnsClientServerAddress `
  -InterfaceAlias 'LAN' `
  -ServerAddresses '192.0.2.53','192.0.2.54'
```

Zusätzliche Adresse ohne Gateway:

```powershell
New-NetIPAddress -InterfaceAlias LAN -IPAddress 192.0.2.11 -PrefixLength 24
```

Adresse entfernen:

```powershell
Remove-NetIPAddress -InterfaceAlias LAN -IPAddress 192.0.2.11 -Confirm:$false
```

Auf DHCP zurück:

```powershell
Set-NetIPInterface -InterfaceAlias LAN -AddressFamily IPv4 -Dhcp Enabled
Set-DnsClientServerAddress -InterfaceAlias LAN -ResetServerAddresses
```

Lease erneuern:

```cmd
ipconfig /release
ipconfig /renew
```

Spezifisch per PowerShell ist DHCP-Clientverhalten versionsabhängig; `ipconfig` bleibt praktisch.

IPv6 statisch:

```powershell
New-NetIPAddress `
  -InterfaceAlias LAN `
  -AddressFamily IPv6 `
  -IPAddress '2001:db8:1::10' `
  -PrefixLength 64 `
  -DefaultGateway 'fe80::1'
```

Bei Link-Local Gateway kann Interface-Scope nötig sein; PowerShell über InterfaceAlias bindet die Route passend.

> [!warning]
> IPv6 nicht pauschal am Adapter deaktivieren. Windows-Komponenten erwarten IPv6; lieber fehlerhafte Route/DNS/Policy gezielt beheben.

## Routen

```powershell
Get-NetRoute -AddressFamily IPv4 |
  Sort-Object DestinationPrefix,RouteMetric
```

Statische Route:

```powershell
New-NetRoute `
  -DestinationPrefix '198.51.100.0/24' `
  -InterfaceAlias 'LAN' `
  -NextHop '192.0.2.254' `
  -RouteMetric 50
```

Entfernen:

```powershell
Remove-NetRoute -DestinationPrefix '198.51.100.0/24' -InterfaceAlias LAN -Confirm:$false
```

Metrik:

```powershell
Get-NetIPInterface | Sort-Object InterfaceMetric
Set-NetIPInterface -InterfaceAlias LAN -AddressFamily IPv4 -AutomaticMetric Disabled -InterfaceMetric 10
```

Klassisch persistent:

```cmd
route -p add 198.51.100.0 mask 255.255.255.0 192.0.2.254 metric 50
```

Routingdiagnose:

```powershell
Test-NetConnection 203.0.113.10 -DiagnoseRouting -InformationLevel Detailed
```

## DNS

Konfiguration:

```powershell
Get-DnsClient
Get-DnsClientServerAddress
Get-DnsClientGlobalSetting
```

Abfrage:

```powershell
Resolve-DnsName example.org
Resolve-DnsName example.org -Type A
Resolve-DnsName example.org -Type AAAA
Resolve-DnsName example.org -Server 192.0.2.53
```

Cache:

```powershell
Get-DnsClientCache
Clear-DnsClientCache
```

Klassisch:

```cmd
ipconfig /displaydns
ipconfig /flushdns
nslookup example.org
```

DNS-Suffix:

```powershell
Set-DnsClient -InterfaceAlias LAN -ConnectionSpecificSuffix 'example.org' -RegisterThisConnectionsAddress $true
```

Domain Controller und AD-Clients müssen interne AD-DNS-Server verwenden, nicht beliebige öffentliche Resolver.

Hosts-Datei:

```text
C:\Windows\System32\drivers\etc\hosts
```

Nur temporär/gezielt; keine zentrale DNS-Verwaltung ersetzen.

## WLAN mit netsh

Interfaces:

```cmd
netsh wlan show interfaces
netsh wlan show drivers
netsh wlan show networks mode=bssid
```

Profile:

```cmd
netsh wlan show profiles
netsh wlan show profile name="SSID"
```

Verbinden:

```cmd
netsh wlan connect name="PROFILNAME" interface="Wi-Fi"
```

Trennen:

```cmd
netsh wlan disconnect interface="Wi-Fi"
```

Profil löschen:

```cmd
netsh wlan delete profile name="SSID"
```

Profil exportieren:

```cmd
netsh wlan export profile name="SSID" folder="C:\Temp"
```

Mit `key=clear` würde ein PSK im XML im Klartext exportiert – nur in geschützter Umgebung und danach sicher löschen.

WLAN-Bericht:

```cmd
netsh wlan show wlanreport
```

Bericht liegt typischerweise unter `C:\ProgramData\Microsoft\Windows\WlanReport\`.

> [!important]
> Unternehmens-WLAN-Profile bevorzugt über MDM/GPO verteilen und CA-/Servernamenvalidierung erzwingen. Benutzer dürfen nicht „Zertifikat ignorieren“ als Dauerlösung verwenden.

## Firewall

Profile:

```powershell
Get-NetFirewallProfile
```

Regeln suchen:

```powershell
Get-NetFirewallRule -Enabled True |
  Where-Object DisplayName -Match 'Remote|SSH|HTTP'
```

TCP 443 eingehend für Private/Domain:

```powershell
New-NetFirewallRule `
  -DisplayName 'App HTTPS 443' `
  -Direction Inbound `
  -Action Allow `
  -Protocol TCP `
  -LocalPort 443 `
  -Profile Domain,Private
```

Quelle begrenzen:

```powershell
New-NetFirewallRule `
  -DisplayName 'Admin SSH' `
  -Direction Inbound `
  -Action Allow `
  -Protocol TCP `
  -LocalPort 22 `
  -RemoteAddress 192.0.2.0/24 `
  -Profile Domain,Private
```

Regel deaktivieren/entfernen:

```powershell
Disable-NetFirewallRule -DisplayName 'App HTTPS 443'
Remove-NetFirewallRule -DisplayName 'App HTTPS 443'
```

Effektive Portfilter:

```powershell
Get-NetFirewallPortFilter -AssociatedNetFirewallRule `
  (Get-NetFirewallRule -DisplayName 'App HTTPS 443')
```

Firewall nicht global abschalten; gezielte Testregel/Logging verwenden.

## Listener und Verbindungen

```powershell
Get-NetTCPConnection -State Listen
Get-NetUDPEndpoint
Get-NetTCPConnection -LocalPort 443
```

Prozess:

```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 443 -State Listen).OwningProcess
```

Klassisch:

```cmd
netstat -ano
netstat -abno
```

`-b` benötigt Administratorrechte und kann langsam sein.

Porttest:

```powershell
Test-NetConnection server.example.org -Port 443 -InformationLevel Detailed
```

HTTP/TLS:

```powershell
Invoke-WebRequest https://server.example.org/ -UseBasicParsing
curl.exe -vk https://server.example.org/
```

## Teaming, VLAN und virtuelle Adapter

Server-NIC-Teaming:

```powershell
Get-NetLbfoTeam
Get-NetLbfoTeamMember
```

LBFO gilt je Windows-Version/Hyper-V-Szenario unterschiedlich; für Hyper-V ist Switch Embedded Teaming häufig relevant.

Hyper-V:

```powershell
Get-VMSwitch
Get-VMNetworkAdapter -All
Get-NetAdapter -IncludeHidden
```

VLAN bei Hyper-V-VM:

```powershell
Set-VMNetworkAdapterVlan -VMName 'VM1' -Access -VlanId 100
```

Physische Adapter-VLANs hängen vom Treiber ab:

```powershell
Get-NetAdapterAdvancedProperty -Name LAN
```

Keine herstellerunabhängige Standardproperty annehmen.

## Reset und Reparatur

Adapter neu starten:

```powershell
Restart-NetAdapter -Name LAN
```

DHCP/DNS:

```cmd
ipconfig /release
ipconfig /renew
ipconfig /flushdns
```

Winsock-/IP-Stack-Reset – letzte Stufe, Reboot erforderlich/Verlust eigener Einstellungen möglich:

```cmd
netsh winsock reset
netsh int ip reset
```

Kompletter Netzwerkreset über Windows-Einstellungen entfernt/neu installiert Adapter und kann VPN/virtuelle Switches beschädigen. Vorher exportieren/dokumentieren.

Proxy:

```cmd
netsh winhttp show proxy
netsh winhttp reset proxy
```

Benutzerproxy zusätzlich in Windows-Einstellungen/Internet Options; WinHTTP und WinINET sind getrennte Pfade.

## Mitschnitt und Diagnose

Ereignisse:

```powershell
Get-WinEvent -LogName System -MaxEvents 200 |
  Where-Object ProviderName -Match 'Tcpip|DNS|Dhcp|NlaSvc|WLAN'
```

Pktmon:

```cmd
pktmon filter remove
pktmon filter add -p 443
pktmon start --etw -m real-time
```

Stop/PCAPNG:

```cmd
pktmon stop
pktmon pcapng PktMon.etl -o capture.pcapng
```

Netsh Trace:

```cmd
netsh trace start capture=yes scenario=InternetClient report=yes tracefile=C:\Temp\net.etl
netsh trace stop
```

ETL kann sensible Daten enthalten.

Konnektivität:

```powershell
Get-NetIPConfiguration
Test-NetConnection 192.0.2.1
Test-NetConnection 1.1.1.1
Resolve-DnsName example.org
Test-NetConnection example.org -Port 443
tracert example.org
pathping example.org
```

ARP/Nachbarn:

```powershell
Get-NetNeighbor
Clear-NetNeighbor -InterfaceAlias LAN -Confirm:$false
```

Prüfreihenfolge:

1. Adapter `Up`, Medienstatus und Fehlerzähler.
2. IP/Prefix/Gateway/DNS.
3. Profil und Firewall.
4. Route/Metrik/Quelladresse.
5. Gateway und externe IP.
6. DNS A/AAAA.
7. Zielport und Listener.
8. Proxy/VPN/NRPT.
9. Mitschnitt/ETL.

## Abnahme

```text
[ ] Adaptername/Index dokumentiert
[ ] Profil Public/Private/Domain korrekt
[ ] DHCP oder statische Adresse persistent
[ ] DNS passend zu AD/Split-DNS
[ ] IPv4/IPv6 getestet
[ ] Routen/Metriken eindeutig
[ ] Firewallregel minimal und profiliert
[ ] Dienste lauschen auf richtigen Adressen
[ ] Reboot getestet
[ ] VPN/Hyper-V/WSL-Auswirkungen geprüft
```

## Quellen
- [Microsoft NetTCPIP Module](https://learn.microsoft.com/powershell/module/nettcpip/)
- [Microsoft DNSClient Module](https://learn.microsoft.com/powershell/module/dnsclient/)
- [Windows Firewall PowerShell](https://learn.microsoft.com/windows/security/operating-system-security/network-security/windows-firewall/configure-with-command-line)
- [netsh wlan](https://learn.microsoft.com/windows-server/networking/technologies/netsh/netsh-wlan)

## Verwandte Notizen
- [[Netzwerk-Konfiguration – Premium-Spickzettel]]
- [[MS RPC-Verbindungen – Premium-Spickzettel]]
- [[Windows Terminal – Premium-Spickzettel]]
- [[Wireshark – Premium-Spickzettel]]
