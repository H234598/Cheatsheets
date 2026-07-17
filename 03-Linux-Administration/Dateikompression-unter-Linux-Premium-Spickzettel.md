---
title: "Dateikompression unter Linux – Premium-Spickzettel"
aliases: ["Linux Archive Cheatsheet", "tar gzip xz zstd zip 7z", "File Compression Linux", "File-Compression-Linux-Premium-Spickzettel"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, compression, tar, gzip, xz, zstd, zip, backup]
source: "https://www.gnu.org/software/tar/manual/"
---

# Dateikompression unter Linux – Premium-Spickzettel

> [!abstract] Zweck
> Praxisreferenz für Archive und Kompression mit tar, gzip, bzip2, xz, zstd, zip und 7-Zip – inklusive Metadaten, Verifikation, Parallelisierung, sicherem Entpacken und Formatwahl.

> [!important] Archiv ≠ Kompression
> `tar` bündelt Dateien und Metadaten zu einem Archiv. `gzip`, `xz`, `zstd` und ähnliche Verfahren komprimieren Daten. Endungen wie `.tar.zst` kombinieren beides.

## Inhalt

- [[#Formatwahl]]
- [[#tar-Grundlagen]]
- [[#gzip, bzip2, xz und zstd]]
- [[#zip und 7-Zip]]
- [[#Metadaten und Dateisystemgrenzen]]
- [[#Sicher entpacken]]
- [[#Prüfen und testen]]
- [[#Parallelisierung und Performance]]
- [[#Verschlüsselung]]
- [[#Splitten und Streaming]]
- [[#Rezepte]]

## Formatwahl

| Format | Stärken | Schwächen | Typisch |
|---|---|---|---|
| `.tar.gz` | sehr kompatibel, schnell | mittelmäßige Ratio | Quellcode, Unix-Austausch |
| `.tar.xz` | hohe Kompression | langsam, mehr RAM | Distribution/Release |
| `.tar.zst` | sehr schnell, gute Ratio | ältere Systeme evtl. ohne Tool | moderne Backups/Packages |
| `.zip` | plattformübergreifend, Einzelzugriff | Unix-Metadaten begrenzt | Windows-Austausch |
| `.7z` | hohe Ratio, AES-Verschlüsselung | weniger Unix-nativ | große Archive/Austausch |
| `.tar` | keine Kompression | groß | Pipes, Tape, Metadatencontainer |

Faustregel:

- maximale Kompatibilität: `tar.gz`
- hohe Geschwindigkeit: `tar.zst`
- maximale Ratio, Zeit zweitrangig: `tar.xz` oder `7z`
- Austausch mit Office-/Windows-Nutzern: `zip`

## tar-Grundlagen

Archiv erstellen:

```bash
tar -cf archiv.tar verzeichnis/
```

Inhalt anzeigen:

```bash
tar -tf archiv.tar
tar -tvf archiv.tar
```

Entpacken:

```bash
tar -xf archiv.tar
```

Zielverzeichnis:

```bash
mkdir -p restore
tar -xf archiv.tar -C restore
```

Komprimierte Archive:

```bash
tar -czf archiv.tar.gz verzeichnis/
tar -cJf archiv.tar.xz verzeichnis/
tar --zstd -cf archiv.tar.zst verzeichnis/
```

Entpacken erkennt Kompression meist automatisch:

```bash
tar -xf archiv.tar.gz
tar -xf archiv.tar.xz
tar -xf archiv.tar.zst
```

Ausschlüsse:

```bash
tar --exclude='.git' --exclude='*.tmp' -czf projekt.tar.gz projekt/
```

Ausschlussdatei:

```bash
tar --exclude-from=exclude.txt -czf backup.tar.gz daten/
```

> [!tip]
> Für reproduzierbare Pfade in das Elternverzeichnis wechseln:
>
> ```bash
> tar -C /srv -czf backup.tar.gz app
> ```
>
> So enthält das Archiv `app/...` statt absolute oder unnötig lange Pfade.

## gzip, bzip2, xz und zstd

Einzeldatei komprimieren:

```bash
gzip datei.log       # erzeugt datei.log.gz und entfernt Original
bzip2 datei.log
xz datei.log
zstd datei.log
```

Original behalten:

```bash
gzip -k datei.log
xz -k datei.log
zstd -k datei.log
```

Entpacken:

```bash
gunzip datei.log.gz
bunzip2 datei.log.bz2
unxz datei.log.xz
unzstd datei.log.zst
```

Ausgabe nach stdout:

```bash
zcat datei.log.gz | less
xzcat datei.log.xz | grep ERROR
zstdcat datei.log.zst | less
```

Kompressionsstufen:

```bash
gzip -1 schnell.log
gzip -9 klein.log
xz -T0 -6 datei
zstd -T0 -3 datei
zstd -T0 -19 datei
```

> [!note]
> Sehr hohe Stufen benötigen unverhältnismäßig mehr Zeit/RAM. Vor großen Archiven an einer repräsentativen Teilmenge messen.

## zip und 7-Zip

ZIP erstellen:

```bash
zip archiv.zip datei1 datei2
zip -r archiv.zip verzeichnis/
```

Anzeigen und testen:

```bash
unzip -l archiv.zip
unzip -t archiv.zip
```

Entpacken:

```bash
unzip archiv.zip -d restore/
```

7-Zip:

```bash
7z a archiv.7z verzeichnis/
7z l archiv.7z
7z t archiv.7z
7z x archiv.7z -orestore
```

ZIP mit 7-Zip:

```bash
7z a -tzip archiv.zip verzeichnis/
```

## Metadaten und Dateisystemgrenzen

Für Linux-Systembackups wichtig:

- Besitzer und Gruppen
- Modusbits
- ACLs
- Extended Attributes
- SELinux-Kontexte
- Hardlinks
- Sparse Files
- Capabilities

GNU tar kann vieles sichern:

```bash
sudo tar --acls --xattrs --selinux --sparse \
  -cpf backup.tar /pfad
```

Restore:

```bash
sudo tar --acls --xattrs --selinux --same-owner \
  -xpf backup.tar -C /restore
```

> [!warning]
> Ein Archivformat allein garantiert keine vollständige Wiederherstellung. Quell-/Zieldateisystem, Toolversion, Rechte und Mountoptionen müssen ACLs/xattrs unterstützen. Test-Restore durchführen.

ZIP ist für vollständige Unix-Systemmetadaten nicht die erste Wahl.

## Sicher entpacken

Vorher Inhalt prüfen:

```bash
tar -tf unbekannt.tar | less
unzip -l unbekannt.zip | less
7z l unbekannt.7z
```

In leeres Verzeichnis entpacken:

```bash
mkdir -m 700 unpack-test
bsdtar -xf unbekannt.tar -C unpack-test
```

Risiken:

- absolute Pfade
- `../` Path Traversal
- Symlinks auf Ziele außerhalb des Restore-Verzeichnisses
- Überschreiben vorhandener Dateien
- Device Nodes/FIFOs
- Zip Bombs und extreme Expansion
- manipulierte Besitzer/Modi bei Root-Restore

GNU tar schützt gegen manche absolute/übergeordnete Pfade, aber unbekannte Archive weiterhin isoliert und ohne Root entpacken.

Keine vorhandenen Dateien überschreiben:

```bash
tar --keep-old-files -xf archiv.tar -C restore
unzip -n archiv.zip -d restore
```

## Prüfen und testen

Archivliste:

```bash
tar -tf backup.tar.zst >/dev/null
```

Kompressionsstream testen:

```bash
gzip -t archiv.tar.gz
xz -t archiv.tar.xz
zstd -t archiv.tar.zst
bzip2 -t archiv.tar.bz2
unzip -t archiv.zip
7z t archiv.7z
```

Hash erzeugen:

```bash
sha256sum archiv.tar.zst > archiv.tar.zst.sha256
sha256sum -c archiv.tar.zst.sha256
```

> [!important]
> Ein erfolgreicher Hashvergleich beweist Integrität gegenüber dem erzeugten Hash, nicht Vertrauenswürdigkeit. Für Herkunftssicherung digitale Signaturen oder authentisierte Übertragung verwenden.

## Parallelisierung und Performance

Parallel-gzip mit `pigz`:

```bash
tar -cf - verzeichnis/ | pigz -6 > archiv.tar.gz
pigz -dc archiv.tar.gz | tar -xf -
```

Parallel-bzip2:

```bash
tar -cf - verzeichnis/ | pbzip2 > archiv.tar.bz2
```

xz parallel:

```bash
tar -cJf archiv.tar.xz --options 'xz:threads=0' verzeichnis/
```

zstd parallel:

```bash
tar -I 'zstd -T0 -6' -cf archiv.tar.zst verzeichnis/
```

Messung:

```bash
/usr/bin/time -v tar -I 'zstd -T0 -6' -cf archiv.tar.zst verzeichnis/
du -sh verzeichnis archiv.tar.zst
```

## Verschlüsselung

Klassisches ZIP-Passwort ist oft schwach. 7-Zip mit AES-256:

```bash
7z a -t7z -mhe=on -p archiv.7z verzeichnis/
```

`-mhe=on` verschlüsselt auch Dateinamen. Passwort nicht als Klartext in Skripten/History übergeben; interaktiv eingeben.

Unix-nativ mit `age`:

```bash
tar --zstd -cf - verzeichnis/ | age -r age1... > backup.tar.zst.age
age -d backup.tar.zst.age | tar -xf -
```

Oder GnuPG:

```bash
tar --zstd -cf - verzeichnis/ | gpg --encrypt --recipient user@example.org > backup.tar.zst.gpg
```

> [!danger]
> Verschlüsselung ohne Schlüsselmanagement ist kein belastbares Backup. Private Schlüssel, Wiederherstellungsweg und Passwortverlustszenario getrennt dokumentieren und testen.

## Splitten und Streaming

Archiv splitten:

```bash
tar --zstd -cf - verzeichnis/ | split -b 4G - backup.tar.zst.part-
```

Zusammenführen/entpacken:

```bash
cat backup.tar.zst.part-* | tar -xf -
```

Über SSH ohne Zwischenarchiv:

```bash
tar -C /quelle -cf - . | zstd -T0 | ssh backup 'cat > /srv/backup/data.tar.zst'
```

Direkt remote entpacken:

```bash
tar -C /quelle -cf - . | ssh ziel 'tar -C /restore -xf -'
```

Bei instabilen Verbindungen ist `rsync` oder ein resumefähiges Backupwerkzeug meist besser.

## Rezepte

Quellcode-Release:

```bash
tar --exclude-vcs --exclude='*.tmp' -czf projekt-1.0.tar.gz projekt-1.0/
```

Schnelles modernes Backup:

```bash
sudo tar --acls --xattrs --selinux --sparse \
  -I 'zstd -T0 -6' -cpf backup-$(date +%F).tar.zst /srv/daten
```

Log lesen ohne Entpacken:

```bash
zstdcat app.log.zst | grep -nEi 'error|panic'
```

Restore testen:

```bash
mkdir restore-test
sudo tar --acls --xattrs --selinux -xpf backup.tar.zst -C restore-test
sudo diff -qr /quelle restore-test/quelle
```

## Quellen
- [GNU tar Manual](https://www.gnu.org/software/tar/manual/)
- [Zstandard](https://facebook.github.io/zstd/)
- [XZ Utils](https://tukaani.org/xz/)
- [7-Zip](https://www.7-zip.org/)

## Verwandte Notizen
- [[rsync – Premium-Spickzettel]]
- [[POSIX-ACL – Premium-Spickzettel]]
- [[Dateisysteme – Premium-Spickzettel]]
