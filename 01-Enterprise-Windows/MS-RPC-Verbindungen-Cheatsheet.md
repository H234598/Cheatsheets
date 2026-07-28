---
title: Microsoft RPC-Verbindungen – Cheatsheet
aliases:
- MS RPC
- Windows RPC
- DCOM RPC Diagnose
- MS RPC-Verbindungen – Cheatsheet
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags:
- windows
- rpc
- dcom
- networking
- firewall
- troubleshooting
source: https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/service-overview-and-network-port-requirements
---

# Microsoft RPC-Verbindungen – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für Windows Remote Procedure Call: Endpoint Mapper, dynamische Ports, DCOM/WMI, Firewallplanung, Diagnosebefehle und typische Fehlercodes.

> [!danger] Sicherheitsgrenze
> RPC/DCOM nie pauschal aus nicht vertrauenswürdigen Netzen freigeben. Zugriff auf Verwaltungsdienste über segmentierte Managementnetze, VPN/Jump Host, hostbasierte Firewall und minimale Quellbereiche begrenzen.

## Inhalt

- [[#Grundmodell]]
- [[#Ports und Verbindungsablauf]]
- [[#Wichtige RPC-basierte Dienste]]
- [[#Diagnosebefehle]]
- [[#Firewall und Portbereich]]
- [[#DCOM und WMI]]
- [[#Fehlercodes]]
- [[#Sichere Prüfreihenfolge]]

## Grundmodell

RPC erlaubt einem Prozess, eine Funktion auf einem anderen Prozess oder Rechner aufzurufen. Unter Windows nutzen viele Verwaltungs- und Domänendienste RPC, darunter DCOM, WMI, Diensteverwaltung, Ereignisprotokoll, Active Directory und Teile der Druck- oder Dateidienste.

```text
Client
  │  1. Anfrage an TCP 135
  ▼
RPC Endpoint Mapper
  │  2. Antwort: Dienst hört auf dynamischem Port X
  ▼
Client ───────────────► TCP Port X ─► RPC-Serverdienst
```

| Baustein | Aufgabe |
|---|---|
| **Endpoint Mapper** | Ordnet Interface-UUIDs konkreten Endpunkten zu; typischerweise TCP 135 |
| **Interface UUID** | Identifiziert eine RPC-Schnittstelle, nicht nur einen Prozessnamen |
| **Dynamic Endpoint** | Vom RPC-Dienst registrierter hoher Port |
| **Binding** | Beschreibung, wie Client und Server miteinander kommunizieren |
| **DCOM** | Verteiltes COM auf Basis von RPC |
| **Named Pipes** | Alternativer Transport, häufig über SMB/TCP 445 |

## Ports und Verbindungsablauf

### Typische Portgruppen

| Zweck | Typischer Port/Umfang |
|---|---|
| RPC Endpoint Mapper | TCP 135 |
| SMB Named Pipes | TCP 445 |
| Dynamische TCP-Ports moderner Windows-Systeme | typischerweise TCP 49152–65535 |
| Spezifische Serverdienste | dienstabhängig, teils statisch konfigurierbar |

> [!note]
> Nicht jeder RPC-Dienst braucht denselben Transport. Vor einer Firewalländerung den konkreten Dienst und dessen Microsoft-Portdokumentation bestimmen.

### Verbindung testen

```powershell
Resolve-DnsName server01.example.org
Test-NetConnection server01.example.org -Port 135
Test-NetConnection server01.example.org -Port 445
```

Dynamischen Port anzeigen, sofern bekannt:

```powershell
Test-NetConnection server01.example.org -Port 50234
```

Lokale Listener:

```powershell
Get-NetTCPConnection -State Listen |
  Sort-Object LocalPort |
  Select-Object LocalAddress,LocalPort,OwningProcess

Get-Process -Id (Get-NetTCPConnection -LocalPort 135 -State Listen).OwningProcess
```

Klassisch:

```cmd
netstat -ano | findstr LISTENING
tasklist /fi "PID eq 1234"
```

## Wichtige RPC-basierte Dienste

| Aufgabe | Zusätzliche Abhängigkeiten |
|---|---|
| Remote Service Control Manager | TCP 135 + dynamischer RPC-Port; teils SMB |
| WMI/DCOM | TCP 135 + dynamischer RPC-Port; DCOM-Rechte |
| Remote Event Log | RPC/SMB, Firewallgruppe und Rechte |
| Active Directory | RPC plus DNS, Kerberos, LDAP, SMB und dienstspezifische Ports |
| DHCP-/DNS-Verwaltung | RPC beziehungsweise Verwaltungsdienst-spezifisch |
| Druckverwaltung | Spooler/RPC; besonders restriktiv behandeln |

> [!warning]
> „Port 135 offen“ beweist nur, dass der Endpoint Mapper erreichbar ist. Die zweite Verbindung zum ausgehandelten Port kann weiterhin durch Firewall, NAT oder Routing scheitern.

## Diagnosebefehle

### Dienste und Ereignisse

```powershell
Get-Service RpcSs,RpcEptMapper,DcomLaunch
Get-WinEvent -LogName System -MaxEvents 200 |
  Where-Object ProviderName -Match 'RPC|DCOM|DistributedCOM|NETLOGON'
```

Relevante DCOM-Ereignisse:

```powershell
Get-WinEvent -FilterHashtable @{
  LogName='System'
  ProviderName='Microsoft-Windows-DistributedCOM'
  StartTime=(Get-Date).AddHours(-4)
} | Format-List TimeCreated,Id,LevelDisplayName,Message
```

### Firewallregeln

```powershell
Get-NetFirewallProfile
Get-NetFirewallRule -Enabled True |
  Where-Object DisplayGroup -Match 'Remote|WMI|Event|Service' |
  Select-Object DisplayName,DisplayGroup,Direction,Action
```

Firewallprotokollierung prüfen/aktivieren:

```powershell
Get-NetFirewallProfile |
  Select-Object Name,LogAllowed,LogBlocked,LogFileName

Set-NetFirewallProfile -Profile Domain \
  -LogBlocked True -LogAllowed True
```

> [!note] PowerShell-Zeilenumbruch
> In echtem PowerShell statt `\` den Backtick `` ` `` oder eine einzelne Zeile verwenden. Das obige Beispiel ist aus Lesbarkeitsgründen logisch umgebrochen.

### RPC-spezifische Werkzeuge

Je nach installiertem Support-Toolset:

```cmd
rpcping /?
portqry.exe -n server01 -e 135 -p TCP
portqry.exe -n server01 -r 49152:65535 -p TCP
```

`rpcping` kann Binding, Authentisierung und RPC-Erreichbarkeit testen. `PortQry` kann beim Endpoint Mapper registrierte Endpunkte abfragen. Werkzeuge nur aus vertrauenswürdiger Microsoft-Quelle beziehen.

### Paketmitschnitt

Wireshark-Filter:

```text
tcp.port == 135
```

```text
rpc || dcerpc
```

```text
ip.addr == 192.0.2.25 && (tcp.port == 135 || dcerpc)
```

Ablauf erkennen:

1. TCP-Handshake zu Port 135
2. DCE/RPC Bind und Endpoint-Mapper-Anfrage
3. Antwort mit dynamischem Port
4. neuer TCP-Handshake zu diesem Port
5. Bind/Aufruf auf der Zielschnittstelle

## Firewall und Portbereich

### Bevorzugte Reihenfolge

1. Prüfen, ob der konkrete Dienst einen statischen Port unterstützt.
2. Wenn nicht, RPC-Dynamikbereich nur mit Herstelleranleitung begrenzen.
3. Firewallregel auf notwendige Quell- und Zielsysteme beschränken.
4. Ausreichend Ports für Parallelität und Systemdienste vorsehen.
5. Last-, Failover- und Neustarttests durchführen.
6. Konfiguration und Rückfallweg dokumentieren.

### Aktuellen dynamischen TCP-Bereich anzeigen

```cmd
netsh int ipv4 show dynamicport tcp
netsh int ipv6 show dynamicport tcp
```

Beispiel für **allgemeinen TCP-Dynamikbereich** – nicht blind als RPC-Konfiguration verwenden:

```cmd
netsh int ipv4 set dynamicport tcp start=50000 num=10000
```

> [!danger]
> Der allgemeine TCP-Ephemeralbereich und die RPC-Runtime-Konfiguration sind nicht dasselbe. Änderungen können zahlreiche Anwendungen beeinflussen. Microsoft-Dokumentation, Kapazitätsplanung, Backup der Registry und Wartungsfenster sind Pflicht.

### RPC-Runtime-Bereich in der Registry

Microsoft dokumentiert bei Bedarf Werte unter:

```text
HKEY_LOCAL_MACHINE\Software\Microsoft\Rpc\Internet
```

Typische Werte:

```text
Ports                   REG_MULTI_SZ
PortsInternetAvailable  REG_SZ
UseInternetPorts        REG_SZ
```

Nach Änderungen ist ein Neustart erforderlich. Die Beispielbereiche aus Dokumentationen sind Illustrationen, keine universelle Dimensionierung.

## DCOM und WMI

### Lokale WMI-Funktion prüfen

```powershell
Get-CimInstance Win32_OperatingSystem
Get-CimInstance Win32_Service | Select-Object -First 5
```

Remote über modernere WS-Man-Verbindung:

```powershell
Get-CimInstance Win32_OperatingSystem -ComputerName server01
```

Explizite DCOM-Sitzung:

```powershell
$opt = New-CimSessionOption -Protocol Dcom
$session = New-CimSession -ComputerName server01 -SessionOption $opt
Get-CimInstance Win32_OperatingSystem -CimSession $session
Remove-CimSession $session
```

> [!tip]
> Wo möglich, PowerShell Remoting/WS-Man oder moderne verwaltete Schnittstellen gegenüber offenem DCOM bevorzugen. Das reduziert den Bedarf an breiten dynamischen Portfreigaben.

### DCOM-Konfiguration

```cmd
dcomcnfg
```

Prüfen:

- Start- und Aktivierungsberechtigungen
- Zugriffsberechtigungen
- Identität des COM-Servers
- AppID/CLSID aus Ereignismeldungen
- lokale und domänenweite Richtlinien
- UAC-Remoteeinschränkungen

Rechte nicht pauschal „Jeder/Vollzugriff“ setzen. Den betroffenen Dienst und die minimale Identität identifizieren.

## Fehlercodes

| Fehler | Bedeutung/typische Ursache |
|---|---|
| `1722 / 0x6BA RPC_S_SERVER_UNAVAILABLE` | Name, Routing, Firewall, Dienst oder dynamischer Port nicht erreichbar |
| `1753 / 0x6D9 EPT_S_NOT_REGISTERED` | Gewünschte Schnittstelle nicht beim Endpoint Mapper registriert |
| `5 / ACCESS_DENIED` | Authentisierung, DCOM-/Diensterecht oder UAC |
| `53 / BAD_NETPATH` | DNS/SMB/Pfad oder Routingproblem |
| `87 / INVALID_PARAMETER` | fehlerhafte RPC-Port- oder Dienstkonfiguration möglich |
| DCOM Event 10016 | Berechtigungsmeldung; nicht jede 10016 ist betriebsrelevant |

### Fehler 1722 systematisch zerlegen

```text
DNS korrekt?
  └─ Ping/Route nötig? (ICMP kann blockiert sein)
      └─ TCP 135 erreichbar?
          └─ Endpoint liefert Zielport?
              └─ Zielport erreichbar?
                  └─ Dienst läuft und Interface registriert?
                      └─ Authentisierung/Berechtigung gültig?
```

## Sichere Prüfreihenfolge

```powershell
Resolve-DnsName server01.example.org
Test-NetConnection server01.example.org -Port 135
Test-NetConnection server01.example.org -Port 445
Get-Service RpcSs,RpcEptMapper,DcomLaunch
Get-NetFirewallProfile
Get-WinEvent -LogName System -MaxEvents 100
```

Dann:

1. exakten Client, Server, Zeitpunkt und RPC-basierten Dienst erfassen
2. Namensauflösung und Uhrzeit/Kerberos prüfen
3. Port 135 und ausgehandelten dynamischen Port testen
4. Firewalllogs auf beiden Seiten und Zwischenfirewall korrelieren
5. Zielprozess/Dienst und registrierte Schnittstelle prüfen
6. Berechtigungen erst nach geklärter Netzwerkstrecke untersuchen
7. Änderungshistorie, GPO, Patches und Neustarts vergleichen
8. nur minimal notwendige Freigabe umsetzen und erneut testen

## Quellen
- [Microsoft: Service overview and network port requirements](https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/service-overview-and-network-port-requirements)
- [Microsoft: Configure RPC dynamic port allocation with firewalls](https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/configure-rpc-dynamic-port-allocation-with-firewalls)
- [Microsoft: RPCPing](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/rpcping)

## Verwandte Notizen
- [[Wireshark-Cheatsheet]]
- [[Netzwerk-Konfiguration-Linux-Windows-BSD]]
- [[Windows-Terminal-Cheatsheet]]
