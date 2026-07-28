---
title: "DNF – Cheatsheet"
aliases: ["dnf Cheatsheet", "DNF5", "Fedora Paketmanager"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [dnf, fedora, rhel, rpm, packages]
source: "https://dnf.readthedocs.io/"
---

# DNF – Cheatsheet

> [!abstract] Zweck
> Ausführliche DNF-Referenz für Fedora/RHEL: Suchen, Installieren, Repositories, Repoquery, Provides, History, Version Lock, Download, Gruppen, Sicherheit und Fehlerdiagnose.

> [!note]
> Moderne Fedora-Versionen verwenden DNF5 als Standardimplementierung; RHEL- und Derivatversionen können unterschiedliche DNF-Generationen und Plugins besitzen. Grundbefehle sind ähnlich, Details mit `dnf --help` und lokaler Dokumentation prüfen.

## Inhalt

- [[#Grundbefehle]]
- [[#Suchen und Informationen]]
- [[#Installieren, Entfernen und Upgrade]]
- [[#Repositories]]
- [[#Repoquery und Provides]]
- [[#History und Rollbackgrenzen]]
- [[#Gruppen, Module und Versionen]]
- [[#Download und Offline]]
- [[#Konfiguration und Proxy]]
- [[#Diagnose]]

## Grundbefehle

```bash
dnf --version
dnf --help
dnf repolist
dnf list --installed
```

Cache:

```bash
sudo dnf makecache
sudo dnf clean metadata
sudo dnf clean all
```

`clean all` erzeugt zusätzliche Downloads beim nächsten Lauf; nicht als universelle Fehlerbehebung nötig.

## Suchen und Informationen

```bash
dnf search nginx
dnf info nginx
dnf list nginx
dnf list --available
dnf list --upgrades
dnf check-update
```

Mehrere Versionen/Repos:

```bash
dnf list --showduplicates paket
dnf repoquery --info paket
dnf repoquery --qf '%{name}-%{evr}.%{arch} %{repoid}' paket
```

Paketinhalt:

```bash
dnf repoquery --list paket
```

Installiert mit RPM:

```bash
rpm -ql paket
```

## Installieren, Entfernen und Upgrade

```bash
sudo dnf install paket
sudo dnf install ./lokal.rpm
sudo dnf remove paket
sudo dnf reinstall paket
sudo dnf downgrade paket
sudo dnf upgrade --refresh
```

Transaktion vorab herunterladen/prüfen je Version/Plugin. Vor Bestätigung Paketliste, Repository, Downloadgröße und entfernte Pakete lesen.

### Bestimmte Version

```bash
sudo dnf install 'paket-1.2.3-1.fcXX'
```

EVR/Architektur exakt mit `dnf list --showduplicates` ermitteln.

### Autoremove

```bash
sudo dnf autoremove
```

Liste sorgfältig lesen; manuell benötigte, ursprünglich als Dependency markierte Pakete können vorgeschlagen werden.

### Distribution Sync

```bash
sudo dnf distro-sync
```

Gleicht Pakete an aktive Repositorystände an und kann downgraden. Wichtig nach Repositorywechseln, aber nur bewusst.

## Repositories

```bash
dnf repolist --all
dnf repoinfo REPOID
dnf repository-packages REPOID list
```

Temporär:

```bash
dnf --disablerepo='*' --enablerepo=REPOID list available
sudo dnf --enablerepo=REPOID install paket
```

Konfiguration typischerweise:

```text
/etc/dnf/dnf.conf
/etc/yum.repos.d/*.repo
```

Beispiel:

```ini
[internal]
name=Internes Repository
baseurl=https://repo.example.org/rhel/$releasever/$basearch/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-internal
```

> [!danger]
> `gpgcheck=0` oder `sslverify=0` nicht als Dauerlösung. CA-Trust, Zeit, Proxy oder Signierschlüssel korrekt beheben.

Repo verwalten, falls Plugin/Befehl verfügbar:

```bash
sudo dnf config-manager --set-enabled REPOID
sudo dnf config-manager --set-disabled REPOID
```

## Repoquery und Provides

Welches Paket stellt Datei bereit?

```bash
dnf provides '*/semanage'
dnf provides '/usr/bin/python3'
```

Dependencies:

```bash
dnf repoquery --requires paket
dnf repoquery --requires --resolve paket
dnf repoquery --whatrequires libfoo.so.1
```

Duplikate/Extras:

```bash
dnf repoquery --duplicates
dnf repoquery --extras
dnf repoquery --unsatisfied
```

Installationsgrund:

```bash
dnf repoquery --userinstalled
```

Befehlssyntax kann zwischen DNF4/DNF5 leicht variieren.

## History und Rollbackgrenzen

```bash
dnf history
dnf history info last
dnf history info <ID>
```

Undo/Redo je Version:

```bash
sudo dnf history undo <ID>
sudo dnf history redo <ID>
```

> [!warning]
> History Undo ist kein vollständiger Systemrollback. Alte Pakete müssen verfügbar sein; Datenbankmigrationen, Configänderungen, Nutzerdaten, Kernel/Boot und externe Services werden nicht automatisch zurückgesetzt.

Für kritische Änderungen Snapshot/Backup und Applikationsrollback vorsehen.

## Gruppen, Module und Versionen

Gruppen:

```bash
dnf group list
dnf group info 'Development Tools'
sudo dnf group install 'Development Tools'
sudo dnf group remove 'Development Tools'
```

Modularity/AppStream ist versionsabhängig. Falls vorhanden:

```bash
dnf module list
dnf module info NAME
```

Nicht auf Distributionen übertragen, in denen Module ersetzt oder anders gehandhabt werden.

### Version Lock

Plugin/Unterbefehl je System installieren:

```bash
sudo dnf install 'dnf-command(versionlock)'
sudo dnf versionlock add paket
dnf versionlock list
sudo dnf versionlock delete paket
```

Auf DNF5 kann Paket-/Befehlname abweichen. Locks dokumentieren, sonst bleiben Securityupdates unbemerkt aus.

Excludes:

```ini
[main]
exclude=paket1 paket2*
```

Nur zeitlich begrenzt und überwacht.

## Download und Offline

Paket herunterladen:

```bash
dnf download paket
```

Mit Abhängigkeiten, je Plugin/Version:

```bash
dnf download --resolve --alldeps --destdir ./packages paket
```

Repository erstellen:

```bash
createrepo_c ./packages
```

Lokales Repo und Signaturkonzept definieren. Einzelne RPMs ohne vollständige Dependency-Closure sind kein verlässlicher Air-Gap-Plan.

Nur Cache verwenden:

```bash
dnf --cacheonly ...
```

## Konfiguration und Proxy

```bash
dnf config-manager --dump 2>/dev/null | less
```

Hauptoptionen:

```ini
[main]
max_parallel_downloads=10
install_weak_deps=True
keepcache=False
```

Proxy je DNF-Version/Config:

```ini
proxy=http://proxy.example.org:3128
```

Credentials nicht in allgemein lesbarer Datei; Rechte und Secretmechanismus beachten.

### Debug

```bash
dnf -v repolist
dnf -d 10 install paket
```

Logorte können je Generation variieren, häufig unter `/var/log/dnf*`.

## Diagnose

### Metadata/TLS-Fehler

```bash
date -Is
getent hosts repo.example.org
curl -Iv https://repo.example.org/
dnf -v makecache
```

Uhrzeit, DNS, Proxy, CA-Trust, URL und Mirror prüfen; Verifikation nicht deaktivieren.

### Konflikte

```bash
dnf check
dnf repoquery --duplicates
dnf repoquery --unsatisfied
dnf repolist --all
```

Gemischte Repositories/Releasever prüfen. Optionen wie `--allowerasing` können notwendige Entfernen erlauben, aber Liste genau lesen:

```bash
sudo dnf upgrade --allowerasing
```

Nicht blind in Automation.

### RPMDB-Problem

Zunächst Prozesse und Speicher/Filesystem prüfen. Reparatur nur nach Backup und distributionsspezifischer Anleitung. Keine Lockdateien oder DB-Dateien blind löschen.

```bash
ps aux | grep -E '[d]nf|[r]pm'
rpm -qa >/dev/null
journalctl -b -p err
```

### Paketdatei verändert

```bash
rpm -V paket
```

Ausgabe interpretieren; Konfigurationsänderungen können legitim sein. Original aus Paket extrahieren oder reinstallieren, aber lokale Config vorher sichern.

### Universeller Prüfblock

```bash
cat /etc/os-release
dnf --version
dnf repolist --all
dnf list --showduplicates paket
dnf history info last
df -h / /var /boot
```

## Quellen
- [DNF Documentation](https://dnf.readthedocs.io/)
- [DNF5 Documentation](https://dnf5.readthedocs.io/)
- [Fedora DNF Quick Docs](https://docs.fedoraproject.org/en-US/quick-docs/dnf/)

## Verwandte Notizen
- [[Paketmanager-Cheatsheet]]
- [[RPM-Cheatsheet]]
- [[Fedora-RHEL-Cheatsheet]]
