---
title: "FreeBSD pkg – Cheatsheet"
aliases: ["pkg Cheatsheet", "FreeBSD Package Manager", "pkgng"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [freebsd, pkg, bsd, packages]
source: "https://man.freebsd.org/cgi/man.cgi?query=pkg&sektion=8"
---

# FreeBSD pkg – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für den FreeBSD-Paketmanager pkg: Bootstrap, Repositories, Suche, Installation, Upgrade, Audit, Lock, Autoremove, Which/Query, Offlinebetrieb und Diagnose.

> [!note]
> Diese Seite behandelt `pkg` auf FreeBSD. FreeBSD-Basissystem und Drittanbieterpakete sind getrennte Lebenszyklen; `pkg upgrade` aktualisiert nicht automatisch Kernel und Base System.

## Inhalt

- [[#Bootstrap und Status]]
- [[#Suchen und Installieren]]
- [[#Upgrade und Base-System]]
- [[#Repositorys]]
- [[#Abfragen und Dateien]]
- [[#Lock, Autoremove und Leaf-Pakete]]
- [[#Audit und Integrität]]
- [[#Jails und ABI]]
- [[#Diagnose]]

## Bootstrap und Status

Auf frischem FreeBSD:

```sh
pkg bootstrap
pkg -vv
pkg stats
```

`pkg` kann beim ersten Aufruf Bootstrap anbieten. Signatur/Repositorykonfiguration prüfen.

Paketliste:

```sh
pkg info
pkg info -a
pkg version
```

## Suchen und Installieren

```sh
pkg search nginx
pkg search -f nginx
pkg info nginx
sudo pkg install nginx
sudo pkg delete nginx
sudo pkg reinstall nginx
```

Dry Run:

```sh
pkg install -n nginx
pkg upgrade -n
```

> [!tip]
> Vor Upgrade mit `-n` geplante Installationen, Updates und Löschungen ansehen.

Lokales Paket:

```sh
sudo pkg add ./paket.pkg
```

Abhängigkeiten werden bei lokalem Einzelpaket nur entsprechend verfügbarer Metadaten/Repos gelöst; normales `pkg install` bevorzugen.

## Upgrade und Base-System

```sh
sudo pkg update
sudo pkg upgrade
```

Repositorykatalog erzwingen:

```sh
sudo pkg update -f
```

> [!important]
> `pkg` verwaltet Ports-/Third-Party-Pakete. FreeBSD Base System wird je Version mit dokumentiertem Mechanismus wie `freebsd-update` oder Sourcebuild aktualisiert. Reihenfolge und ABI-Kompatibilität bei Major/Minor-Upgrades beachten.

Nach OS-Upgrade können Pakete gegen neues ABI neu installiert werden müssen:

```sh
sudo pkg-static upgrade -f
```

Nur nach offizieller Upgradeanleitung; `pkg-static` ist hilfreich, wenn dynamische Bibliotheken nach Upgrade nicht passen.

## Repositorys

Systemdefaults nicht direkt überschreiben, sondern lokale Repo-Datei nutzen, typischerweise:

```text
/usr/local/etc/pkg/repos/*.conf
```

Beispiel:

```conf
FreeBSD: {
  enabled: yes,
  url: "pkg+https://pkg.FreeBSD.org/${ABI}/quarterly",
  mirror_type: "srv",
  signature_type: "fingerprints",
  fingerprints: "/usr/share/keys/pkg"
}
```

Quarterly versus latest entsprechend Stabilitäts-/Aktualitätsanforderung. Nicht ohne Plan wechseln.

Repositorystatus:

```sh
pkg -vv | less
pkg rquery '%n-%v %R'
```

Interne Repositories mit `pkg repo`/Poudriere und Signaturkonzept erstellen.

## Abfragen und Dateien

Paketdateien:

```sh
pkg info -l nginx
pkg which /usr/local/sbin/nginx
pkg which -o /usr/local/sbin/nginx
```

Abhängigkeiten:

```sh
pkg info -d paket
pkg info -r paket
pkg query '%n-%v %o' paket
pkg rquery '%n-%v %o' paket
```

Optionen/Annotations:

```sh
pkg info -A paket
pkg annotate -S paket
```

Konfigurationsdateien liegen bei Drittsoftware häufig unter `/usr/local/etc`, Binärdateien unter `/usr/local/bin`/`sbin` und Daten unter `/var/db` beziehungsweise `/usr/local`-spezifischen Pfaden.

## Lock, Autoremove und Leaf-Pakete

Lock:

```sh
sudo pkg lock paket
pkg lock -l
sudo pkg unlock paket
```

Securityupdates für Locks überwachen.

Automatisch installierte Dependencies:

```sh
pkg query -e '%a = 1' '%n-%v'
```

Autoremove:

```sh
sudo pkg autoremove -n
sudo pkg autoremove
```

Leaf-Pakete:

```sh
pkg prime-list
pkg leaf
```

Vor Entfernen prüfen, ob Paket manuell gebraucht wird.

## Audit und Integrität

Vulnerabilities:

```sh
sudo pkg audit -F
pkg audit
```

Package-DB und Dateien:

```sh
pkg check -d
pkg check -s
pkg check -B
```

Optionen mit `pkg help check` prüfen; Integritätscheck kann dauern.

> [!warning]
> Keine gemeldete bekannte Schwachstelle ist keine allgemeine Sicherheitsgarantie. Base-System-Advisories separat prüfen.

## Jails und ABI

Jails können eigene Package DB und Repositories besitzen. Befehle im Jail ausführen oder mit Jailmanagementtool orchestrieren.

```sh
jls
jexec JID /bin/sh
pkg -vv | grep -E 'ABI|url'
```

ABI-Beispiel:

```text
FreeBSD:14:amd64
```

Repository muss zum ABI passen. Nach Host-/Jail-Upgrade Paketupgrade und Dienste separat prüfen.

## Diagnose

### pkg funktioniert nach OS-Upgrade nicht

```sh
/usr/local/sbin/pkg-static -vv
sudo pkg-static update -f
```

Dann nach offizieller Upgradeanleitung vollständiges Paketupgrade. Libraries und ABI prüfen:

```sh
freebsd-version -ku
uname -K
pkg -vv | grep ABI
```

### Repositoryfehler

```sh
pkg -vv
fetch -o /dev/null https://pkg.FreeBSD.org/
date
```

DNS, Zeit, CA, Proxy, ABI, Repo-URL und Signatur prüfen.

### Lock/DB

```sh
ps auxww | grep '[p]kg'
pkg check -d
```

Datenbank nicht blind löschen. Backup unter `/var/backups` beziehungsweise pkg-DB-Snapshots prüfen.

### Datei fehlt

```sh
pkg which /pfad
auditdistd 2>/dev/null || true
pkg check -s paket
sudo pkg reinstall paket
```

Lokale Config vorher sichern.

### Universeller Prüfblock

```sh
freebsd-version -ku
uname -a
pkg -vv
pkg stats
pkg version -vIL=
pkg audit -F
```

## Quellen
- [FreeBSD pkg Manual](https://man.freebsd.org/cgi/man.cgi?query=pkg&sektion=8)
- [FreeBSD Handbook: Packages and Ports](https://docs.freebsd.org/en/books/handbook/ports/)
- [pkg Documentation](https://github.com/freebsd/pkg)

## Verwandte Notizen
- [[Paketmanager-Cheatsheet]]
- [[Netzwerk-Konfiguration-Linux-Windows-BSD]]
- [[pfSense-Cheatsheet]]
