---
title: "Paketmanager – Vergleich und Premium-Spickzettel"
aliases: ["Packetmanager", "Package Manager Vergleich", "Linux Paketverwaltung"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [package-management, dnf, apt, pkg, rpm, chocolatey]
source: "https://docs.fedoraproject.org/en-US/quick-docs/dnf/"
---

# Paketmanager – Vergleich und Premium-Spickzettel

> [!abstract] Zweck
> Übersichtsseite für Paketverwaltung auf Fedora/RHEL, Debian/Ubuntu, FreeBSD und Windows: Rollen, Sicherheitsmodell, typische Befehle, Repositories, Updates und Auswahl des richtigen Werkzeugs.

> [!note] Schreibweise
> „Packetmanager“ wird hier als **Paketmanager/Package Manager** interpretiert. `pkg` bezeichnet primär den FreeBSD-Paketmanager; Termux nutzt ebenfalls einen `pkg`-Wrapper, ist aber nicht Schwerpunkt dieser Seite.

## Inhalt

- [[#Schichtenmodell]]
- [[#Vergleich]]
- [[#Universelle Arbeitsweise]]
- [[#Pakete suchen und Herkunft prüfen]]
- [[#Updates und Neustarts]]
- [[#Offline-, Mirror- und Proxybetrieb]]
- [[#Sicherheit und Supply Chain]]
- [[#Diagnose]]

Unterseiten:

- [[dnf-Premium-Spickzettel]]
- [[apt-Premium-Spickzettel]]
- [[FreeBSD-pkg-Premium-Spickzettel]]
- [[RPM-Premium-Spickzettel]]
- [[Chocolatey-Premium-Spickzettel]]

## Schichtenmodell

```text
Repository/Feed
    │ Metadaten + Pakete + Signaturen
    ▼
High-Level Manager
  DNF / APT / pkg / Chocolatey
    │ Abhängigkeitsauflösung, Transaktion, Download
    ▼
Low-Level Format/Installer
  RPM / dpkg / FreeBSD pkg database / NuGet+Installskript
    ▼
Dateien, Services, Datenbank, Hooks/Scripts
```

High-Level-Manager bevorzugen. Low-Level-Installationen können Abhängigkeiten oder Transaktionszustand umgehen.

## Vergleich

| Plattform | High-Level | Paketformat/Low-Level | Repo-Konfiguration |
|---|---|---|---|
| Fedora/RHEL | `dnf` | RPM / `rpm` | `/etc/yum.repos.d/*.repo` |
| Debian/Ubuntu | `apt` | DEB / `dpkg` | `/etc/apt/sources.list`, `sources.list.d` |
| FreeBSD | `pkg` | `.pkg` | `/etc/pkg`, `/usr/local/etc/pkg/repos` |
| Windows | Chocolatey `choco` | NuGet-Paket + PowerShell-Skripte | Chocolatey Sources/Config |

### Häufige Operationen

| Aufgabe | DNF | APT | FreeBSD pkg | Chocolatey |
|---|---|---|---|---|
| Metadaten/Index | automatisch/`makecache` | `apt update` | `pkg update` | `choco source`/Feed |
| Installieren | `dnf install x` | `apt install x` | `pkg install x` | `choco install x` |
| Entfernen | `dnf remove x` | `apt remove x` | `pkg delete x` | `choco uninstall x` |
| Upgrade | `dnf upgrade` | `apt upgrade`/`full-upgrade` | `pkg upgrade` | `choco upgrade all` |
| Suchen | `dnf search` | `apt search` | `pkg search` | `choco search` |
| Dateiinhaber | `rpm -qf`/`dnf provides` | `dpkg -S`/`apt-file` | `pkg which` | paket-/installerspezifisch |

## Universelle Arbeitsweise

### Vorher

```text
[ ] richtige Distribution/Version/Architektur
[ ] Repositoryherkunft und Signierschlüssel
[ ] freier Speicher, insbesondere /boot und /var
[ ] Backup/Snapshot bei kritischem System
[ ] laufende Transaktion oder Wartungsfenster
[ ] erwartete Serviceunterbrechung
[ ] Rollback-/Recoveryweg
```

### Sicherer Ablauf

1. Metadaten aktualisieren.
2. geplante Änderungen anzeigen.
3. Paketquelle, Version und Architektur prüfen.
4. Transaktion ausführen.
5. Services/Kernel/Prozesse auf Neustartbedarf prüfen.
6. Anwendungstest.
7. Paketmanager-Log/History dokumentieren.

> [!warning]
> Ein Paketupdate kann Migrationsskripte, Dienstneustarts, Konfigurationsdateien und Datenbankänderungen auslösen. Die angezeigte Paketliste ist nicht die ganze Betriebswirkung.

## Pakete suchen und Herkunft prüfen

### Namen sind nicht portabel

Beispiele:

```text
RPM Development Header: libfoo-devel
Debian Development Header: libfoo-dev
Apache RPM: httpd
Apache Debian: apache2
```

Nicht Paketnamen aus einer anderen Distribution blind übernehmen.

### Herkunft

DNF/RPM:

```bash
dnf info paket
rpm -qi paket
rpm -q --qf '%{NAME} %{VERSION}-%{RELEASE} %{ARCH} %{VENDOR}\n' paket
```

APT/dpkg:

```bash
apt-cache policy paket
dpkg-query -W paket
```

FreeBSD:

```bash
pkg info paket
pkg rquery '%n-%v %R' paket
```

Chocolatey:

```powershell
choco info paket
choco source list
```

## Updates und Neustarts

### Kategorien

- Paketdatei aktualisiert, Prozess läuft noch mit alter Bibliothek.
- Dienst wurde automatisch neu gestartet.
- Dienst braucht manuellen Neustart.
- Kernel/Bootloader/Initramfs aktualisiert: Reboot sinnvoll/erforderlich.
- Datenbank-/Schema-Migration erfolgt beim Start oder manuell.

Linux prüfen:

```bash
uname -r
systemctl --failed
```

Distributionstools können Neustartbedarf zeigen, beispielsweise `dnf needs-restarting` oder `/var/run/reboot-required` im Debian/Ubuntu-Umfeld. Existenz und Semantik distributionsabhängig prüfen.

> [!tip]
> Nicht nur „Server wurde gepatcht“ dokumentieren, sondern laufende Version nach Neustart, Anwendungs-Smoketest und verbleibende Fehler.

## Offline-, Mirror- und Proxybetrieb

Möglichkeiten:

- interner Repositorymirror
- Content-/Lifecycle-Management
- Caching Proxy
- heruntergeladene Pakete mit vollständigen Abhängigkeiten
- signiertes internes Repository
- Air-Gap-Transfer mit Manifest und Prüfsummen

Anforderungen:

```text
Repository-Metadaten
Paketdateien
Signierschlüssel/Trust
Distribution + Version + Architektur
Snapshot/Stichtag
Dependency Closure
Malware-/Lizenzprüfung
Audit und Retention
```

Ein Ordner mit einzelnen Paketen ist noch kein reproduzierbares Repository.

## Sicherheit und Supply Chain

### Grundregeln

- TLS und Paketsignatur nicht deaktivieren.
- Schlüssel-Fingerprint über vertrauenswürdigen Kanal prüfen.
- Repositorys minimal halten.
- Drittanbieterpakete nicht als gleichwertig zum Basisvendor behandeln.
- Paket-Scripts/Installskripte laufen oft mit Root/Adminrechten.
- Typosquatting und ähnlich benannte Pakete beachten.
- Versionen/Repositorysnapshot für reproduzierbare Builds fixieren.
- SBOM, Signaturen und Provenance bei kritischer Software erfassen.

### Was Signaturen leisten

Paketsignaturen bestätigen typischerweise Herkunft/Integrität relativ zum vertrauten Schlüssel. Sie garantieren nicht, dass Paketinhalt sicher, fehlerfrei oder passend konfiguriert ist.

### Geheimnisse in Repositorykonfiguration

Credentials nicht direkt in allgemein lesbare URLs schreiben. Rechte, Secret Store, kurzlebige Tokens und Proxykonfiguration nutzen.

## Diagnose

### Sperre/Lock

Nicht Lockdatei löschen, bevor geklärt ist, ob ein Paketprozess läuft:

```bash
ps aux | grep -E '[d]nf|[r]pm|[a]pt|[d]pkg|[p]kg|[c]hoco'
```

Prozess, Log und Transaktionsstatus prüfen. Abbruch während Datenbankänderung kann Reparatur erfordern.

### Dependencykonflikt

1. genaue Paketnamen, Versionen, Architekturen erfassen
2. aktive Repositorys und Prioritäten prüfen
3. gemischte Release-/Drittanbieterquellen ausschließen
4. festgehaltene/ausgeschlossene Pakete prüfen
5. Solverausgabe vollständig lesen
6. nicht mit `--force`/`--nodeps` Symptome übergehen

### Paket installiert, Befehl fehlt

```bash
command -v befehl
printf '%s\n' "$PATH"
```

Paketinhalt und Pfad prüfen, neue Shell/Hashcache, alternatives Binary-Namensschema oder optionales Subpaket.

### Konfigurationsdatei geändert

Paketmanager können `.rpmnew`, `.rpmsave`, dpkg-Konfigurationsdialoge oder andere Backupvarianten erzeugen. Änderungen bewusst mergen, nicht blind ersetzen.

### Universeller Prüfblock

```text
OS/Version/Architektur
Paketmanager-Version
aktive Repositorys
gewünschtes Paket + Version
Transaktionslog/History
freier Speicher
Netzwerk/DNS/TLS/Proxy
Signaturschlüssel
```

## Quellen
- [Fedora DNF Quick Docs](https://docs.fedoraproject.org/en-US/quick-docs/dnf/)
- [Debian APT User Guide](https://www.debian.org/doc/manuals/apt-guide/)
- [FreeBSD pkg Manual](https://man.freebsd.org/cgi/man.cgi?query=pkg&sektion=8)
- [Chocolatey Documentation](https://docs.chocolatey.org/en-us/)

## Verwandte Notizen
- [[dnf-Premium-Spickzettel]]
- [[apt-Premium-Spickzettel]]
- [[FreeBSD-pkg-Premium-Spickzettel]]
- [[RPM-Premium-Spickzettel]]
- [[Chocolatey-Premium-Spickzettel]]
