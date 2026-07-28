---
title: "Microsoft IIS – Cheatsheet"
aliases: ["MS IIS Cheatsheet", "Internet Information Services", "IIS Administration"]
created: 2026-07-16
modified: 2026-07-17
type: reference
status: fertig
origin: "Cheatsheet I – vollständig überarbeitet"
reviewed: 2026-07-17
tags: [microsoft, windows-server, iis, webserver, powershell, appcmd, tls, administration]
source: "https://learn.microsoft.com/iis/"
---

# Microsoft IIS – Cheatsheet

> [!abstract] Zweck
> Betriebsreferenz für Internet Information Services: Installation, Sites, Application Pools, Anwendungen, Bindings, TLS, Authentifizierung, `web.config`, AppCmd, PowerShell, Logs, Failed Request Tracing, Backup, Deployment, Härtung und Diagnose.

## Inhalt

- [[#Werkzeuge und wichtige Pfade]]
- [[#Installation und Zustand]]
- [[#Sites verwalten]]
- [[#Application Pools]]
- [[#Anwendungen und virtuelle Verzeichnisse]]
- [[#Bindings und HTTPS]]
- [[#Authentifizierung und Autorisierung]]
- [[#Konfiguration mit web.config]]
- [[#AppCmd]]
- [[#Logs, Tracing und Ereignisse]]
- [[#Deployment und Wartung]]
- [[#Backup und Wiederherstellung]]
- [[#Sicherheit und Härtung]]
- [[#Fehlerdiagnose]]
- [[#Schnellreferenz]]

## Werkzeuge und wichtige Pfade

| Element | Pfad/Befehl |
|---|---|
| IIS-Manager | `inetmgr.exe` |
| IIS-Verwaltungsdienst | `W3SVC`, `WAS` |
| AppCmd | `%windir%\System32\inetsrv\appcmd.exe` |
| Hauptkonfiguration | `%windir%\System32\inetsrv\config\applicationHost.config` |
| Standard-Webroot | `C:\inetpub\wwwroot` |
| Standardlogs | `C:\inetpub\logs\LogFiles` |
| Failed Request Tracing | `C:\inetpub\logs\FailedReqLogFiles` |
| PowerShell | `WebAdministration`, teils `IISAdministration` |
| Zertifikate | `Cert:\LocalMachine\My` |

PowerShell-Modul:

```powershell
Import-Module WebAdministration
Get-Command -Module WebAdministration
Get-ChildItem IIS:\
Get-ChildItem IIS:\Sites
Get-ChildItem IIS:\AppPools
```

> [!warning]
> `applicationHost.config` nicht im laufenden Betrieb unkontrolliert von Hand überschreiben. Vor Änderungen Backup, Syntaxprüfung und Rückfallplan anlegen.

## Installation und Zustand

### Windows Server

```powershell
Get-WindowsFeature Web-*

Install-WindowsFeature Web-Server `
  -IncludeManagementTools
```

Gezielte Zusatzfeatures:

```powershell
Install-WindowsFeature `
  Web-Server, `
  Web-Common-Http, `
  Web-Default-Doc, `
  Web-Static-Content, `
  Web-Http-Errors, `
  Web-Http-Logging, `
  Web-Stat-Compression, `
  Web-Filtering, `
  Web-Windows-Auth, `
  Web-Mgmt-Console
```

### Windows Client

```powershell
Enable-WindowsOptionalFeature -Online `
  -FeatureName IIS-WebServerRole `
  -All
```

### Zustand prüfen

```powershell
Get-Service W3SVC,WAS
Get-Website
Get-ChildItem IIS:\AppPools | Select-Object Name,State
Test-NetConnection localhost -Port 80
Invoke-WebRequest http://localhost -UseBasicParsing
```

> [!tip]
> Nur tatsächlich benötigte Rollendienste installieren. WebDAV, CGI, FTP, Legacy ASP, Management Service und unnötige Authentifizierungsverfahren nicht pauschal aktivieren.

## Sites verwalten

### Auflisten

```powershell
Get-Website
Get-ChildItem IIS:\Sites
```

### App Pool und Site anlegen

```powershell
New-Item -ItemType Directory -Path 'D:\Web\MeineSite' -Force
New-WebAppPool -Name 'MeineSitePool'

New-Website `
  -Name 'MeineSite' `
  -PhysicalPath 'D:\Web\MeineSite' `
  -Port 80 `
  -HostHeader 'www.example.org' `
  -ApplicationPool 'MeineSitePool'
```

### Starten, stoppen, entfernen

```powershell
Start-Website -Name 'MeineSite'
Stop-Website -Name 'MeineSite'
Restart-WebItem 'IIS:\Sites\MeineSite'
Remove-Website -Name 'MeineSite'
```

> [!danger]
> `Remove-Website` entfernt die IIS-Konfiguration, nicht zwingend die Inhaltsdateien. Vorher Site, Bindings, Anwendungen, Zertifikate und Konfiguration dokumentieren.

### Physikalischen Pfad ändern

```powershell
Set-ItemProperty `
  'IIS:\Sites\MeineSite' `
  -Name physicalPath `
  -Value 'D:\Web\MeineSiteNeu'
```

## Application Pools

Application Pools trennen Anwendungen nach Prozess, Identität und Laufzeitkonfiguration.

```powershell
Get-ChildItem IIS:\AppPools
New-WebAppPool -Name 'ApiPool'
Start-WebAppPool -Name 'ApiPool'
Stop-WebAppPool -Name 'ApiPool'
Restart-WebAppPool -Name 'ApiPool'
```

### Runtime und Pipeline

Klassisches ASP.NET Framework:

```powershell
Set-ItemProperty IIS:\AppPools\ApiPool `
  -Name managedRuntimeVersion -Value 'v4.0'

Set-ItemProperty IIS:\AppPools\ApiPool `
  -Name managedPipelineMode -Value 'Integrated'
```

ASP.NET Core hinter dem ASP.NET Core Module:

```powershell
Set-ItemProperty IIS:\AppPools\ApiPool `
  -Name managedRuntimeVersion -Value ''
```

### Identität

```powershell
Set-ItemProperty IIS:\AppPools\ApiPool `
  -Name processModel.identityType `
  -Value ApplicationPoolIdentity
```

Virtuelle Identität:

```text
IIS AppPool\ApiPool
```

Leserechte:

```powershell
icacls 'D:\Web\MeineApi' /grant 'IIS AppPool\ApiPool:(OI)(CI)RX'
```

Gezielte Schreibrechte:

```powershell
icacls 'D:\Web\MeineApi\uploads' /grant 'IIS AppPool\ApiPool:(OI)(CI)M'
```

> [!warning]
> Nicht den gesamten Webroot mit `Full Control` versehen. Schreibrechte nur für erforderliche Upload-, Cache- oder Datenverzeichnisse erteilen.

### Recycling und Rapid-Fail

```powershell
Get-ItemProperty IIS:\AppPools\ApiPool | `
  Select-Object Name,recycling,processModel,failure
```

Bei wiederholtem Absturz Rapid-Fail Protection nicht einfach dauerhaft abschalten. Zuerst Event Log, Prozessstart, Runtime, Rechte und Anwendung prüfen.

## Anwendungen und virtuelle Verzeichnisse

Anwendung:

```powershell
New-WebApplication `
  -Site 'MeineSite' `
  -Name 'api' `
  -PhysicalPath 'D:\Web\MeineApi' `
  -ApplicationPool 'ApiPool'
```

Virtuelles Verzeichnis:

```powershell
New-WebVirtualDirectory `
  -Site 'MeineSite' `
  -Name 'downloads' `
  -PhysicalPath 'D:\Downloads'
```

Entfernen:

```powershell
Remove-WebApplication -Site 'MeineSite' -Name 'api'
Remove-WebVirtualDirectory -Site 'MeineSite' -Name 'downloads'
```

> [!note]
> Eine **Anwendung** besitzt eigenen Anwendungskontext und häufig einen App Pool. Ein **virtuelles Verzeichnis** mappt primär einen URL-Pfad auf ein Verzeichnis.

## Bindings und HTTPS

### Anzeigen

```powershell
Get-WebBinding -Name 'MeineSite'
```

### HTTP-Binding

```powershell
New-WebBinding `
  -Name 'MeineSite' `
  -Protocol http `
  -Port 80 `
  -HostHeader 'www.example.org'
```

### HTTPS mit SNI

```powershell
New-WebBinding `
  -Name 'MeineSite' `
  -Protocol https `
  -Port 443 `
  -HostHeader 'www.example.org' `
  -SslFlags 1
```

Zertifikate prüfen:

```powershell
Get-ChildItem Cert:\LocalMachine\My |
  Select-Object Subject,Thumbprint,NotBefore,NotAfter,HasPrivateKey
```

Binden:

```powershell
$thumbprint = 'ABCDEF0123456789ABCDEF0123456789ABCDEF01'
$binding = Get-WebBinding `
  -Name 'MeineSite' `
  -Protocol https `
  -Port 443 `
  -HostHeader 'www.example.org'
$binding.AddSslCertificate($thumbprint, 'My')
```

HTTP.sys prüfen:

```powershell
netsh http show sslcert
netsh http show urlacl
```

TLS von außen testen:

```powershell
Test-NetConnection www.example.org -Port 443
curl.exe -vk https://www.example.org/
```

Mit OpenSSL:

```bash
openssl s_client \
  -connect www.example.org:443 \
  -servername www.example.org \
  -showcerts </dev/null
```

> [!important]
> Das Zertifikat muss im Computerzertifikatspeicher liegen, einen privaten Schlüssel besitzen, für Server Authentication geeignet und für Hostname sowie Gültigkeitszeitraum passend sein.

## Authentifizierung und Autorisierung

Aktuellen Zustand lesen:

```powershell
Get-WebConfigurationProperty `
  -PSPath 'IIS:\' `
  -Location 'MeineSite' `
  -Filter 'system.webServer/security/authentication/*' `
  -Name enabled
```

Anonym aus, Windows Authentication an:

```powershell
Set-WebConfigurationProperty `
  -PSPath 'IIS:\' `
  -Location 'MeineSite' `
  -Filter 'system.webServer/security/authentication/anonymousAuthentication' `
  -Name enabled -Value false

Set-WebConfigurationProperty `
  -PSPath 'IIS:\' `
  -Location 'MeineSite' `
  -Filter 'system.webServer/security/authentication/windowsAuthentication' `
  -Name enabled -Value true
```

> [!warning]
> Das passende Rollenfeature muss installiert sein. Für Internetanwendungen moderne Anwendungs-Authentifizierung verwenden; Windows Authentication ist vor allem für kontrollierte Intranet-/Domänenszenarien geeignet.

### Double-Hop/Kerberos

Bei Zugriff der Webanwendung auf Backendressourcen können Kerberos, SPNs und Delegation relevant werden. Prüfen:

```powershell
setspn -Q HTTP/www.example.org
setspn -L DOMAENE\Dienstkonto
klist
```

Nicht durch pauschale Delegation oder dauerhafte Verwendung hochprivilegierter Konten „lösen“.

## Konfiguration mit `web.config`

Minimalbeispiel:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <defaultDocument>
      <files>
        <clear />
        <add value="index.html" />
      </files>
    </defaultDocument>
    <httpProtocol>
      <customHeaders>
        <add name="X-Content-Type-Options" value="nosniff" />
        <add name="Referrer-Policy" value="strict-origin-when-cross-origin" />
      </customHeaders>
    </httpProtocol>
  </system.webServer>
</configuration>
```

Konfiguration anzeigen:

```powershell
Get-WebConfiguration `
  -Filter 'system.webServer/defaultDocument' `
  -PSPath 'IIS:\'
```

> [!warning]
> Sicherheitsheader hängen von Anwendung und Inhalt ab. HSTS erst aktivieren, wenn HTTPS für alle betroffenen Hosts dauerhaft funktioniert. CSP an realen Ressourcen testen.

### Request Filtering

Beispiel Uploadlimit in Byte:

```xml
<system.webServer>
  <security>
    <requestFiltering>
      <requestLimits maxAllowedContentLength="52428800" />
    </requestFiltering>
  </security>
</system.webServer>
```

Zusätzliche Anwendungs-/Runtime-Limits beachten; das kleinste Limit gewinnt.

## AppCmd

```cmd
cd /d %windir%\System32\inetsrv
appcmd list site
appcmd list apppool
appcmd list app
appcmd list wp
appcmd list requests
```

Site anlegen:

```cmd
appcmd add site /name:"MeineSite" /bindings:"http/*:80:www.example.org" /physicalPath:"D:\Web\MeineSite"
```

Konfiguration:

```cmd
appcmd list config "MeineSite"
appcmd list config "MeineSite" /section:system.webServer/security/authentication
```

Backup:

```cmd
appcmd add backup "Vor_Aenderung_2026-07-17"
appcmd list backups
```

## Logs, Tracing und Ereignisse

### IIS-Logs

```powershell
Get-Website | Select-Object Name,Id,LogFile
Get-ChildItem 'C:\inetpub\logs\LogFiles' -Recurse -Filter '*.log'
```

Live:

```powershell
Get-Content 'C:\inetpub\logs\LogFiles\W3SVC1\u_ex*.log' `
  -Wait -Tail 50
```

Wichtige Felder:

```text
sc-status
sc-substatus
sc-win32-status
time-taken
cs-host
cs-uri-stem
cs-username
s-computername
```

### Ereignisprotokolle

```powershell
Get-WinEvent -LogName System -MaxEvents 200 |
  Where-Object ProviderName -Match 'WAS|W3SVC|HTTP'

Get-WinEvent -LogName Application -MaxEvents 200 |
  Where-Object LevelDisplayName -in 'Error','Warning'
```

### Failed Request Tracing

FREB erfordert Rollenfeature, Site-Aktivierung und Regeln. Typischer Speicherort:

```text
C:\inetpub\logs\FailedReqLogFiles
```

> [!warning]
> Traces und Logs können URLs, Konten, Query-Parameter, Header und personenbezogene Daten enthalten. Aufbewahrung, Rechte und Weitergabe begrenzen.

### HTTP.sys

```powershell
netsh http show servicestate
netsh http show iplisten
netsh http show sslcert
```

HTTPERR-Logs:

```text
C:\Windows\System32\LogFiles\HTTPERR
```

Wenn eine Anfrage IIS gar nicht erreicht, zuerst HTTP.sys, Listener, Firewall und Binding prüfen.

## Deployment und Wartung

Sicherer Ablauf:

```text
1. Konfiguration und Inhalte sichern
2. Healthcheck und Rollback definieren
3. neue Version separat bereitstellen
4. Berechtigungen und Konfiguration prüfen
5. App Pool/Site kontrolliert umschalten
6. Smoke-Test lokal und extern
7. Logs/Fehlerquote beobachten
8. alte Version erst später entfernen
```

### App Offline für ASP.NET Core

Eine `app_offline.htm` im Anwendungsverzeichnis kann die Anwendung kontrolliert stoppen. Danach Datei wieder entfernen und Start prüfen.

### Gezieltes Recycling

```powershell
Restart-WebAppPool -Name 'ApiPool'
```

Gesamten IIS nur wenn wirklich erforderlich:

```cmd
iisreset
```

> [!warning]
> `iisreset` betrifft alle Sites und aktive Verbindungen. Gezieltes Recycling oder Site-Neustart ist meist schonender.

## Backup und Wiederherstellung

AppCmd:

```cmd
appcmd add backup "Vor_Aenderung_2026-07-17"
appcmd list backups
appcmd restore backup "Vor_Aenderung_2026-07-17"
appcmd delete backup "Alter_Backupname"
```

Zusätzlich sichern:

- Website-Inhalte und Uploads;
- externe Konfigurationsdateien;
- Zertifikate **mit** privatem Schlüssel, sicher verschlüsselt;
- Anwendungs-Secrets getrennt;
- DNS, Firewall, Load Balancer und Servicekonten;
- Datenbanken und Backendabhängigkeiten.

> [!danger]
> Ein IIS-Konfigurationsrestore ersetzt zentrale Konfiguration und kann alle Sites betreffen. Restore in Staging testen und Wartungsfenster sowie Rückfallplan vorsehen.

## Sicherheit und Härtung

- [ ] nur benötigte Rollendienste installiert;
- [ ] getrennte App-Pool-Identitäten;
- [ ] minimale NTFS-Rechte;
- [ ] HTTPS und gültige Zertifikatskette;
- [ ] Zertifikatsablauf überwacht;
- [ ] Directory Browsing aus, sofern nicht benötigt;
- [ ] Request Filtering und Uploadlimits passend;
- [ ] keine Secrets im Webroot oder Klartext in `web.config`;
- [ ] Debug-/Detailed Errors nicht extern;
- [ ] Anwendung, Hosting Bundle und Windows gepatcht;
- [ ] Logs zentralisiert, rotiert und datenschutzgerecht;
- [ ] Backup und Restore getestet;
- [ ] Dienstkonten ohne interaktive Anmeldung und mit Least Privilege;
- [ ] ausgehende Backendverbindungen kontrolliert;
- [ ] Sicherheitsheader an Anwendung getestet.

Konfiguration nach sensiblen Mustern suchen:

```powershell
Get-ChildItem D:\Web -Recurse -File -Include web.config,*.json,*.xml |
  Select-String -Pattern 'password|secret|token|connectionString' -CaseSensitive:$false
```

Treffer nicht ungeprüft ausgeben oder zentral sammeln; Logs können selbst Secrets enthalten.

## Fehlerdiagnose

### Statuscodes

| Code | Typische Bedeutung |
|---:|---|
| `400` | ungültige Anfrage, Host Header, TLS/HTTP-Verwechslung |
| `401` | Authentifizierung fehlgeschlagen; Unterstatus beachten |
| `403` | Zugriff verboten; Rechte, Filter, Zertifikat, Unterstatus |
| `404` | Ressource/Handler fehlt; Unterstatus beachten |
| `413` | Upload-/Request-Limit |
| `500.19` | ungültige oder gesperrte Konfiguration |
| `502.5` | häufig ASP.NET-Core-Prozessstart fehlgeschlagen |
| `503` | App Pool gestoppt, Rapid-Fail, Queue oder Dienstproblem |

### Universelle Prüfreihenfolge

```powershell
Get-Service W3SVC,WAS
Get-Website
Get-ChildItem IIS:\AppPools | Select-Object Name,State
Get-WebBinding -Name 'MeineSite'
Test-NetConnection localhost -Port 443
Get-WinEvent -LogName Application -MaxEvents 50
```

Dann:

1. exakten Zeitstempel und Request erfassen;
2. IIS-Log inklusive Unterstatus und Win32-Code;
3. HTTPERR prüfen, falls kein IIS-Logeintrag;
4. Event Logs und FREB;
5. Binding, Hostname, SNI und Zertifikat;
6. App-Pool-Zustand, Identität und Dateirechte;
7. Handler, Hosting Bundle, Runtime und `web.config`;
8. Backend direkt testen;
9. Ressourcen, Queue, Antivirus/EDR und Netzwerk;
10. Änderung mit kleinstem Radius rückgängig machen.

### `500.19`

Prüfen:

```powershell
& $env:windir\System32\inetsrv\appcmd.exe list config "MeineSite"
```

Häufig:

- XML-Syntaxfehler;
- unbekannte Direktive wegen fehlendem Modul;
- gesperrter Konfigurationsabschnitt;
- doppelte Einträge;
- unlesbare Datei;
- ungültiger Pfad oder Schlüssel.

### `503`

```powershell
Get-WebAppPoolState -Name 'ApiPool'
Get-WinEvent -LogName System -MaxEvents 100 |
  Where-Object ProviderName -Match 'WAS'
```

Nicht nur starten: Crashursache, Rapid-Fail, Identität, Passwort eines benutzerdefinierten Kontos, Runtime und Anwendung untersuchen.

## Schnellreferenz

```powershell
Import-Module WebAdministration
Get-Website
Get-ChildItem IIS:\AppPools
Get-WebBinding -Name 'MeineSite'
Start-Website -Name 'MeineSite'
Stop-Website -Name 'MeineSite'
Restart-WebAppPool -Name 'ApiPool'
Get-Service W3SVC,WAS
Get-WinEvent -LogName Application -MaxEvents 50
```

Goldene Regeln:

```text
Erst config/Status/Logs prüfen, dann neu starten.
App-Pool statt Gesamt-IIS recyceln.
Bindings immer mit Hostname, SNI und Zertifikat zusammen betrachten.
NTFS-Rechte minimal und an App-Pool-Identität binden.
Vor Restore, Rollenänderung und Zertifikatswechsel Backup + Rollback.
```

## Quellen

- [Microsoft IIS Documentation](https://learn.microsoft.com/iis/)
- [IIS Configuration Reference](https://learn.microsoft.com/iis/configuration/)
- [AppCmd command-line reference](https://learn.microsoft.com/iis/get-started/getting-started-with-iis/getting-started-with-appcmdexe)
- [WebAdministration PowerShell module](https://learn.microsoft.com/powershell/module/webadministration/)
- [IIS security](https://learn.microsoft.com/iis/manage/configuring-security/)

## Verwandte Notizen

- [[MS-RPC-Verbindungen-Cheatsheet]]
- [[Windows-Terminal-Cheatsheet]]
- [[OpenSSL-Cheatsheet]]
- [[nginx-Cheatsheet]]
- [[Apache-HTTP-Server-Cheatsheet]]
