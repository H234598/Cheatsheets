---
title: "Chocolatey – Cheatsheet"
aliases: ["choco Cheatsheet", "Chocolatey Windows", "Windows Package Manager Chocolatey"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [chocolatey, windows, packages, powershell, automation]
source: "https://docs.chocolatey.org/en-us/"
---

# Chocolatey – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für Chocolatey auf Windows: Installation, Sources, Suche, Install/Upgrade, Pinning, Konfiguration, internes Repository, Paketbau, Sicherheit und Diagnose.

> [!danger]
> Chocolatey-Pakete können PowerShell-Installskripte mit Administratorrechten ausführen und Fremdinstaller herunterladen. Quelle, Maintainer, Paketdateien, Prüfsummen und interne Freigabeprozesse sind zentrale Sicherheitsgrenzen.

## Inhalt

- [[#Status und Grundbefehle]]
- [[#Sources und Priorität]]
- [[#Installieren und Upgraden]]
- [[#Pins und Versionen]]
- [[#Konfiguration und Cache]]
- [[#Paketinhalt und Sicherheit]]
- [[#Eigene Pakete]]
- [[#Enterprise- und Offlinebetrieb]]
- [[#Diagnose]]

## Status und Grundbefehle

Administrative PowerShell, wenn Installation/Installer es erfordert:

```powershell
choco --version
choco -?
choco list
choco search git
choco info git
```

Installierte Pakete:

```powershell
choco list --local-only
```

Je Chocolatey-Version kann `choco list` bereits lokal bedeuten; Hilfe der installierten Version beachten.

## Sources und Priorität

```powershell
choco source list
choco source add --name='internal' --source='https://repo.example.org/nuget/chocolatey'
choco source disable --name='chocolatey'
choco source enable --name='internal'
choco source remove --name='old'
```

Credentials möglichst über unterstützte verschlüsselte/verwaltete Mechanismen und minimal berechtigte Serviceidentität. Keine Passwörter in Kommandozeilen, Logs oder Konfigurationsrepository.

> [!important]
> In Unternehmen öffentliche Communityquelle nicht unkontrolliert neben intern freigegebenem Feed verwenden. Paketverwechslung/Dependency Confusion durch Sources, Prioritäten, Namen und Freigabeprozess verhindern.

## Installieren und Upgraden

```powershell
choco install git -y
choco upgrade git -y
choco upgrade all -y
choco uninstall git -y
```

Bestimmte Version:

```powershell
choco install paket --version=1.2.3 -y
choco upgrade paket --version=1.2.3 -y
```

Parameter an Chocolatey versus nativen Installer unterscheiden:

```powershell
choco install paket `
  --params='"/Feature:Value"' `
  --install-arguments='"/quiet /norestart"' `
  -y
```

Syntax paketabhängig; `choco info paket` und Paketdokumentation prüfen.

### Exitcodes

In Automation Exitcodes auswerten:

```powershell
choco install paket -y
if ($LASTEXITCODE -notin @(0, 1605, 1614, 1641, 3010)) {
    throw "Chocolatey/Installer fehlgeschlagen: $LASTEXITCODE"
}
```

Akzeptierte Codes hängen von Prozess und Richtlinie ab. `3010` signalisiert häufig erfolgreichen Installer mit Rebootbedarf; nicht pauschal jeden Nichtnullcode akzeptieren.

## Pins und Versionen

```powershell
choco pin add --name='paket'
choco pin list
choco pin remove --name='paket'
```

Pinning verhindert Updates und kann Schwachstellen offen lassen. Eigentümer, Grund, Ablaufdatum und Monitoring dokumentieren.

Pre-release:

```powershell
choco search paket --pre
choco install paket --pre
```

Nicht auf Produktionssystemen ohne Freigabe.

## Konfiguration und Cache

```powershell
choco config list
choco feature list
choco config get cacheLocation
```

Option setzen:

```powershell
choco config set --name='cacheLocation' --value='D:\ChocolateyCache'
```

Feature aktivieren/deaktivieren:

```powershell
choco feature enable --name='useRememberedArgumentsForUpgrades'
choco feature disable --name='useRememberedArgumentsForUpgrades'
```

> [!warning]
> Gespeicherte Installationsargumente können veraltete oder sensible Werte wiederverwenden. Feature- und Configänderungen zentral dokumentieren.

Standardpfad häufig:

```text
C:\ProgramData\chocolatey
```

Tatsächliche Installations-/Configwerte lokal prüfen.

## Paketinhalt und Sicherheit

Paket herunterladen, ohne Installation – je Edition/Befehl/Workflow, alternativ NuGet-Paket aus Source beziehen und entpacken. Inhalt typischerweise:

```text
paket.nuspec
tools/
├── chocolateyinstall.ps1
├── chocolateyuninstall.ps1
└── ggf. eingebettete Binaries
```

Vor Freigabe prüfen:

- Download-URLs und TLS
- Checksums
- Silent-Argumente
- temporäre Dateien und ACLs
- Registry-/PATH-/Serviceänderungen
- Uninstallpfad
- Rebootverhalten
- Architektur/Versionserkennung
- Signatur des Upstreaminstallers
- Telemetrie/Lizenz

> [!danger]
> Optionen zum Ignorieren von Checksums oder zum Zulassen leerer Checksums nicht als Standard verwenden.

Logs:

```text
C:\ProgramData\chocolatey\logs\chocolatey.log
```

## Eigene Pakete

Vorlage:

```powershell
choco new meine-app
```

Packen:

```powershell
choco pack .\meine-app.nuspec
```

Lokal testen:

```powershell
choco install meine-app `
  --source="'C:\packages'" `
  --yes `
  --force
```

Beispiel Installskript:

```powershell
$packageArgs = @{
  packageName    = $env:ChocolateyPackageName
  fileType       = 'msi'
  url64bit       = 'https://downloads.example.org/app-x64.msi'
  checksum64     = '<sha256>'
  checksumType64 = 'sha256'
  silentArgs     = '/qn /norestart'
  validExitCodes = @(0, 1641, 3010)
}
Install-ChocolateyPackage @packageArgs
```

Version, URL und Hash aktualisieren; Downloadartefakt unveränderlich halten. Für Air-Gap lieber Artefakt intern spiegeln/einbetten nach Lizenz- und Sicherheitsprüfung.

## Enterprise- und Offlinebetrieb

Robustes Modell:

```text
Öffentliche Quelle
  → Quarantäne/Review/Scan
  → internes Repository
  → Test-Ring
  → Produktions-Ringe
```

Anforderungen:

- Paketfreigabe und Vier-Augen-Prinzip
- interne unveränderliche Artefakte
- Malware-/Signaturprüfung
- Paket-/Installer-Logs zentral
- Rollout-Ringe und Wartungsfenster
- Rebootkoordination
- Rückfall/Deinstallation
- Quoten und Hochverfügbarkeit des Feeds
- Dependency-Confusion-Schutz

Chocolatey for Business bietet zusätzliche Verwaltungsfunktionen; konkrete Features lizenz- und versionsabhängig.

## Diagnose

### Befehl nicht gefunden

```powershell
Get-Command choco -ErrorAction SilentlyContinue
$env:Path -split ';'
Test-Path 'C:\ProgramData\chocolatey\bin\choco.exe'
```

Neue Shell öffnen; Installationspfad/Environment kontrollieren.

### Download/TLS/Proxy

```powershell
choco config list
choco source list
Test-NetConnection repo.example.org -Port 443
Invoke-WebRequest 'https://repo.example.org/' -UseBasicParsing
```

Windows Proxy, WinHTTP, TLS, CA-Trust, Zeit und authentisierten Proxy prüfen. Zertifikatsprüfung nicht deaktivieren.

WinHTTP:

```cmd
netsh winhttp show proxy
```

### Installer scheitert

1. Chocolatey-Log und Paketinstallskript lesen.
2. nativen Installer-Exitcode identifizieren.
3. Installerlog mit passenden Argumenten aktivieren.
4. vorhandene Version/Produktcode/Prozess/Lock prüfen.
5. Systemkontext versus Benutzerkontext.
6. Reboot pending.

### Upgrade nimmt falsche Source

```powershell
choco source list --limit-output
choco info paket --source='internal'
```

Quellpriorität, deaktivierte Communitysource und Paketnamen prüfen.

### Universeller Prüfblock

```powershell
choco --version
choco config list
choco feature list
choco source list
choco list --local-only
Get-Content 'C:\ProgramData\chocolatey\logs\chocolatey.log' -Tail 200
```

## Quellen
- [Chocolatey Documentation](https://docs.chocolatey.org/en-us/)
- [Chocolatey CLI Reference](https://docs.chocolatey.org/en-us/choco/commands/)
- [Create Packages](https://docs.chocolatey.org/en-us/create/create-packages/)
- [Chocolatey Security](https://docs.chocolatey.org/en-us/information/security/)

## Verwandte Notizen
- [[Paketmanager-Cheatsheet]]
- [[Windows-Terminal-Cheatsheet]]
- [[Git-Cheatsheet]]
