---
title: "RPM – Premium-Spickzettel"
aliases: ["rpm Cheatsheet", "RPM Package Manager", "RPM Build"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [rpm, fedora, rhel, packages, rpmbuild]
source: "https://rpm.org/documentation.html"
---

# RPM – Premium-Spickzettel

> [!abstract] Zweck
> Ausführliche RPM-Referenz: Pakete abfragen, Inhalte und Skripte prüfen, Signaturen verifizieren, Dateiintegrität, lokale Installation, rpm2cpio sowie Grundlagen von Spec und rpmbuild.

> [!important]
> RPM ist Low-Level-Paketformat und Datenbank. Für normale Installation/Entfernung auf Fedora/RHEL DNF verwenden, damit Abhängigkeiten und Repositorytransaktionen korrekt behandelt werden.

## Inhalt

- [[#Installiertes Paket abfragen]]
- [[#RPM-Datei vor Installation prüfen]]
- [[#Signaturen und Schlüssel]]
- [[#Installieren und Entfernen]]
- [[#Verify und Konfigurationsdateien]]
- [[#Inhalte extrahieren]]
- [[#RPM-Datenbank]]
- [[#Spec und rpmbuild]]
- [[#Diagnose]]

## Installiertes Paket abfragen

```bash
rpm -q paket
rpm -qi paket
rpm -ql paket
rpm -qc paket
rpm -qd paket
rpm -q --scripts paket
rpm -q --changelog paket | head
```

Dateiinhaber:

```bash
rpm -qf /usr/bin/ssh
```

Query Format:

```bash
rpm -q --qf '%{NAME} %{EPOCHNUM}:%{VERSION}-%{RELEASE}.%{ARCH}\n' paket
```

Alle installierten:

```bash
rpm -qa --qf '%{NAME}\t%{VERSION}-%{RELEASE}\t%{ARCH}\n' | sort
```

Requires/Provides:

```bash
rpm -qR paket
rpm -q --provides paket
```

## RPM-Datei vor Installation prüfen

`-p` bedeutet Paketdatei:

```bash
rpm -qpi ./paket.rpm
rpm -qpl ./paket.rpm
rpm -qpR ./paket.rpm
rpm -qp --scripts ./paket.rpm
rpm -qp --changelog ./paket.rpm | head
```

Signatur:

```bash
rpm -K ./paket.rpm
rpm --checksig --verbose ./paket.rpm
```

> [!danger]
> Paket-Scriptlets laufen bei Installation/Upgrade/Entfernung häufig als Root. Vor unbekannten Drittanbieter-RPMs Skripte, Signatur, Vendor und Quelle prüfen.

## Signaturen und Schlüssel

Importierte Schlüssel:

```bash
rpm -qa 'gpg-pubkey*'
rpm -qi gpg-pubkey-*
```

Keydatei Fingerprint mit GPG prüfen:

```bash
gpg --show-keys --with-fingerprint RPM-GPG-KEY-vendor
```

Import:

```bash
sudo rpm --import RPM-GPG-KEY-vendor
```

Bevorzugt über distributions-/repositoryseitig dokumentierten Mechanismus. Fingerprint nicht nur von derselben möglicherweise kompromittierten Downloadseite übernehmen.

## Installieren und Entfernen

Bevorzugt:

```bash
sudo dnf install ./paket.rpm
```

Low-Level:

```bash
sudo rpm -Uvh ./paket.rpm
sudo rpm -ivh ./paket.rpm
sudo rpm -e paket
```

- `-U`: installieren oder upgraden
- `-i`: zusätzliche Installation, kann parallele Version erzeugen
- `-e`: entfernen

> [!danger]
> `--nodeps`, `--force`, `--replacefiles` und `--replacepkgs` nur nach genauer Ursachenanalyse. Sie können Datenbank und Systemzustand inkonsistent machen.

Test:

```bash
rpm -Uvh --test ./paket.rpm
```

## Verify und Konfigurationsdateien

```bash
rpm -V paket
rpm -Va
```

Spalten der Verify-Ausgabe können anzeigen:

```text
S Größe
M Modus/Rechte/Typ
5 Digest
D Device
L Symlinkziel
U User
G Group
T mtime
P Capabilities
```

Marker `c` kennzeichnet Konfigurationsdatei.

> [!note]
> Abweichung ist nicht automatisch Kompromittierung: Konfigurationen, Datenbanken, Zertifikate oder dynamisch erzeugte Dateien können legitim abweichen. Pfad, Paketzweck und Änderungsmanagement prüfen.

Konfigurationsbackup bei Upgrade:

- `.rpmnew`: neue Vendorversion neben lokaler Datei
- `.rpmsave`: lokale alte Datei gesichert, neue aktiv
- `.rpmorig`: mögliche Sicherung je Fall

Finden:

```bash
find /etc -type f \( -name '*.rpmnew' -o -name '*.rpmsave' -o -name '*.rpmorig' \) -print
```

Diff/Merge bewusst durchführen.

## Inhalte extrahieren

Ohne Installation:

```bash
mkdir extract && cd extract
rpm2cpio ../paket.rpm | cpio -idmv
```

Nur Liste:

```bash
rpm2cpio paket.rpm | cpio -t
```

Mit `bsdtar`, falls unterstützt:

```bash
bsdtar -tf paket.rpm
```

Nicht extrahierte Dateien manuell nach `/usr` kopieren; Paketdatenbank würde sie nicht kennen.

## RPM-Datenbank

Status:

```bash
rpm -qa >/dev/null
```

DB-Pfade/Backend sind versionsabhängig. Vor Reparatur:

1. laufende DNF/RPM-Prozesse prüfen
2. Dateisystem/Platz/I/O prüfen
3. Backup der Datenbank
4. distributionsspezifische Anleitung
5. Transaktionslogs sichern

```bash
ps aux | grep -E '[d]nf|[r]pm'
df -h /var
journalctl -b -p err
```

Rebuild-Befehl existiert:

```bash
sudo rpm --rebuilddb
```

> [!warning]
> Nicht reflexartig verwenden. Er behebt keine kaputten Paketdateien oder abgebrochene Maintainer Scripts und kann Diagnosebeweise verändern.

## Spec und rpmbuild

Buildumgebung typischerweise im Benutzerkonto:

```text
~/rpmbuild/
├── BUILD
├── BUILDROOT
├── RPMS
├── SOURCES
├── SPECS
└── SRPMS
```

Setup:

```bash
rpmdev-setuptree
```

Minimale Spec-Skizze:

```spec
Name:           hello
Version:        1.0.0
Release:        1%{?dist}
Summary:        Beispielprogramm
License:        MIT
URL:            https://example.org/hello
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
BuildRequires:  gcc

%description
Kleine Beispielanwendung.

%prep
%autosetup

%build
%make_build

%install
%make_install

%files
%license LICENSE
%doc README.md
%{_bindir}/hello

%changelog
```

Bauen:

```bash
rpmbuild -ba ~/rpmbuild/SPECS/hello.spec
```

Buildabhängigkeiten über DNF:

```bash
sudo dnf builddep hello.spec
```

Noch besser reproduzierbar in Mock/isolierter Buildroot:

```bash
mock -r fedora-XX-x86_64 hello.src.rpm
```

Konkrete Chroot-Namen lokal ermitteln; Build als normaler Benutzer, nicht unkontrolliert als Root.

### Makros

```bash
rpm --eval '%{_bindir}'
rpm --showrc | less
```

Architekturpfade nicht hart codieren; RPM-Makros verwenden.

## Diagnose

### Dependency fehlt

```bash
rpm -qpR paket.rpm
dnf provides 'BENÖTIGTES_CAPABILITY'
```

Nicht `--nodeps`; passendes Repo/Package ermitteln.

### Datei gehört zu welchem Paket?

```bash
rpm -qf /pfad/datei
```

Nicht installiert:

```bash
dnf provides '*/datei'
```

### Paket scheint manipuliert

```bash
rpm -V paket
rpm -qf /pfad/datei
stat /pfad/datei
```

Danach Vergleich mit signierter Paketquelle, Logs, EDR/Forensik. Reinstallieren erst nach Beweissicherung, wenn Sicherheitsvorfall möglich.

### Scriptlet schlägt fehl

```bash
rpm -qp --scripts paket.rpm
journalctl -b
```

DNF-Transaktionslog und betroffenen Scriptaufruf identifizieren; DB, Benutzer, Pfade, SELinux und Servicezustand prüfen.

### Universeller Prüfblock

```bash
rpm --version
rpm -q paket
rpm -qi paket
rpm -V paket
rpm -K ./paket.rpm
rpm -qp --scripts ./paket.rpm
```

## Quellen
- [RPM Documentation](https://rpm.org/documentation.html)
- [rpm Manual](https://rpm.org/docs/latest/man/rpm.8.html)
- [Fedora Packaging Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/)

## Verwandte Notizen
- [[dnf-Premium-Spickzettel]]
- [[Paketmanager-Premium-Spickzettel]]
- [[Make-und-Source-Builds-Premium-Spickzettel]]
