---
title: "APT – Cheatsheet"
aliases: ["apt Cheatsheet", "Debian Paketmanager", "Ubuntu apt"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [apt, debian, ubuntu, dpkg, packages]
source: "https://www.debian.org/doc/manuals/apt-guide/"
---

# APT – Cheatsheet

> [!abstract] Zweck
> Ausführliche APT-Referenz für Debian/Ubuntu: Quellen, Update/Upgrade, Suche, apt-cache, dpkg, Pinning, Holds, Downloads, unattended upgrades, Konfigurationsdateien und Diagnose.

> [!note]
> `apt` ist für interaktive Nutzung; `apt-get` und `apt-cache` besitzen stabilere Skriptschnittstellen. Automation sollte Ausgabe, Exitcodes und Noninteractive-Verhalten explizit kontrollieren.

## Inhalt

- [[#Grundbefehle]]
- [[#Quellen und Schlüssel]]
- [[#Upgradevarianten]]
- [[#Suchen, Policy und Dateien]]
- [[#dpkg und Konfigurationsdateien]]
- [[#Holds und Pinning]]
- [[#Download und Offline]]
- [[#Automatische Updates]]
- [[#Diagnose]]

## Grundbefehle

```bash
sudo apt update
apt list --upgradable
sudo apt upgrade
sudo apt install paket
sudo apt remove paket
sudo apt purge paket
sudo apt autoremove
apt search begriff
apt show paket
```

Reinstall:

```bash
sudo apt install --reinstall paket
```

Bestimmte Version:

```bash
apt-cache policy paket
sudo apt install paket=VERSION
```

Version eventuell halten, wenn Repository sonst sofort aktualisiert.

## Quellen und Schlüssel

Pfade:

```text
/etc/apt/sources.list
/etc/apt/sources.list.d/*.list
/etc/apt/sources.list.d/*.sources
/etc/apt/keyrings/
```

Deb822-Beispiel:

```text
Types: deb
URIs: https://repo.example.org/debian
Suites: stable
Components: main
Signed-By: /etc/apt/keyrings/example.gpg
Architectures: amd64
```

> [!danger]
> Veraltete globale Trust-Methoden und `trusted=yes` vermeiden. Repositoryschlüssel mit `Signed-By` auf konkrete Quelle begrenzen und Fingerprint über vertrauenswürdigen Kanal prüfen.

Quellen anzeigen:

```bash
apt-cache policy
apt-cache policy paket
```

Architekturen:

```bash
dpkg --print-architecture
dpkg --print-foreign-architectures
sudo dpkg --add-architecture i386
sudo apt update
```

Multiarch nur bei Bedarf, da Dependencyraum wächst.

## Upgradevarianten

| Befehl | Verhalten |
|---|---|
| `apt upgrade` | aktualisiert, ohne vorhandene Pakete für Konfliktlösung zu entfernen; kann neue Dependencies installieren |
| `apt full-upgrade` | darf Pakete entfernen/installieren, um Upgrade vollständig aufzulösen |
| `apt-get dist-upgrade` | klassischer Name ähnlich full-upgrade |

```bash
sudo apt update
sudo apt full-upgrade
```

Entfernliste aufmerksam lesen.

> [!warning]
> Distribution-Releasewechsel nicht durch bloßes Ändern von Codenames und `full-upgrade` improvisieren. Offiziellen Upgradepfad, Backup, Drittanbieterquellen und Recovery verwenden.

## Suchen, Policy und Dateien

```bash
apt search nginx
apt show nginx
apt-cache policy nginx
apt-cache depends nginx
apt-cache rdepends nginx
```

Installierte Pakete:

```bash
apt list --installed
dpkg-query -W -f='${binary:Package}\t${Version}\n'
```

Dateien eines installierten Pakets:

```bash
dpkg -L paket
dpkg -S /usr/bin/datei
```

Nicht installiertes Paket finden, mit `apt-file`:

```bash
sudo apt install apt-file
sudo apt-file update
apt-file search '/usr/bin/datei'
apt-file list paket
```

## dpkg und Konfigurationsdateien

Lokales Paket mit Abhängigkeitsauflösung:

```bash
sudo apt install ./paket.deb
```

Low-Level:

```bash
sudo dpkg -i paket.deb
sudo apt-get -f install
```

Bevorzugt `apt install ./...`, da es Dependencies direkt auflöst.

Paketstatus:

```bash
dpkg -s paket
dpkg -l paket
dpkg-deb -I paket.deb
dpkg-deb -c paket.deb
```

Konfigurationsdateien:

```bash
dpkg-query -W -f='${Conffiles}\n' paket
```

Bei Upgrade kann dpkg nach lokal geänderter Config fragen. Diff lesen, lokale und neue Vendoroptionen mergen. Automation muss `Dpkg::Options` bewusst setzen, nicht ungeprüft „immer alt“/„immer neu“.

### Halbkonfigurierte Pakete

```bash
sudo dpkg --configure -a
sudo apt-get -f install
```

Erst Log/Fehler des Maintainer Scripts lesen; Wiederholung kann erneut scheitern.

## Holds und Pinning

Hold:

```bash
sudo apt-mark hold paket
apt-mark showhold
sudo apt-mark unhold paket
```

Holds dokumentieren und auf Securityfolgen überwachen.

Pinning unter `/etc/apt/preferences` oder `.d`:

```text
Package: paket
Pin: version 1.2.*
Pin-Priority: 1001
```

Oder Herkunft/Release. Prioritäten sind mächtig; mit `apt-cache policy paket` testen.

> [!danger]
> Falsches Pinning kann Sicherheitsupdates verhindern oder einen inkonsistenten Mix aus Releases erzeugen. Stable/Testing/Ubuntu-Releases nicht ohne klares Apt-Pinning-Konzept mischen.

## Download und Offline

Paketdatei:

```bash
apt download paket
```

Download ohne Installation:

```bash
sudo apt-get --download-only install paket
```

Cache häufig:

```text
/var/cache/apt/archives/
```

Quellpaket:

```bash
apt source paket
apt build-dep paket
```

Dafür `deb-src`-Quellen und Buildtools nötig.

Repositorymirror/Snapshot für reproduzierbare Offlineumgebungen bevorzugen. Manifest mit Release, Architektur, Paketen, Hashes und Schlüssel führen.

## Automatische Updates

Typischer Baustein:

```bash
sudo apt install unattended-upgrades
```

Konfiguration je Distribution unter `/etc/apt/apt.conf.d/`. Prüfen:

- erlaubte Origins
- automatische Reboots
- Rebootzeit
- E-Mail/Monitoring
- Paket-Blacklist
- Lockkonflikte
- Serviceunterbrechung

Dry Run/Debug je Version:

```bash
sudo unattended-upgrade --dry-run --debug
```

Nicht nur installieren; Ergebnis und Neustartbedarf überwachen.

## Diagnose

### `apt update` Signatur/TLS

```bash
date -Is
getent hosts repo.example.org
curl -Iv https://repo.example.org/
apt-cache policy
sudo apt update -o Debug::Acquire::https=true
```

Uhrzeit, CA, Proxy, Schlüssel-Fingerprint, Suite/Codename und URL prüfen.

### Lock

```bash
ps aux | grep -E '[a]pt|[d]pkg|unattended'
systemctl status apt-daily.service apt-daily-upgrade.service
```

Lockdatei nicht löschen, solange Prozess/Transaktion aktiv sein kann.

### Broken Dependencies

```bash
sudo dpkg --configure -a
sudo apt-get -f install
apt-cache policy BETROFFENES_PAKET
```

Drittanbieterquellen, Pinning, Holds und Multiarch prüfen.

### Keine Installationskandidatin

```bash
apt-cache policy paket
apt-cache search paket
```

Falscher Name, Komponente nicht aktiviert, Architektur/Release nicht verfügbar oder Metadaten veraltet.

### Paketdatei verändert

Debianpakete haben nicht immer vollständige Verifikationsmetadaten wie RPM Verify. Prüfsummen unter `/var/lib/dpkg/info/*.md5sums` können helfen; Werkzeuge wie `debsums` optional. Konfigurationsdateien separat betrachten.

### Logs

```bash
less /var/log/apt/history.log
less /var/log/apt/term.log
less /var/log/dpkg.log
```

### Universeller Prüfblock

```bash
cat /etc/os-release
apt --version
dpkg --print-architecture
apt-cache policy
apt-mark showhold
grep -RhsE '^(deb |Types:|URIs:|Suites:|Components:|Signed-By:)' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null
```

## Quellen
- [APT User Guide](https://www.debian.org/doc/manuals/apt-guide/)
- [apt Manual](https://manpages.debian.org/apt)
- [Debian Repository Format](https://wiki.debian.org/DebianRepository/Format)
- [Ubuntu Package Management](https://help.ubuntu.com/community/AptGet/Howto)

## Verwandte Notizen
- [[Paketmanager-Cheatsheet]]
- [[dnf-Cheatsheet]]
- [[FreeBSD-pkg-Cheatsheet]]
