---
title: "Magisk – Premium-Spickzettel"
aliases: ["Magisk Root", "MagiskSU", "Zygisk", "Android Boot Image Patching"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [android, magisk, root, bootloader, avb, zygisk, security]
source: "https://github.com/topjohnwu/Magisk"
---

# Magisk – Premium-Spickzettel

> [!abstract] Zweck
> Sicherheitsorientierte Praxisreferenz zu Magisk: Architektur, Voraussetzungen, Bootloader/AVB, Patchen eines eigenen Firmware-Images, Module, Zygisk, Updates, Backup, Bootloop-Recovery und saubere Deinstallation – ohne Umgehungsanleitungen für App-Integritätsprüfungen.

> [!danger] Root verändert das Sicherheitsmodell
> Magisk gewährt Prozessen kontrollierbaren Root-Zugriff und verändert den Bootpfad. Fehler können Datenverlust, Bootloops oder ein nicht startendes Gerät verursachen. Bootloader-Entsperrung löscht bei vielen Geräten sämtliche Nutzerdaten und kann Garantie-, Unternehmens- oder Sicherheitsvorgaben berühren.

> [!warning] Keine Integritäts- oder Schutzumgehung
> Dieser Spickzettel behandelt legitime Administration eigener Geräte. Er enthält bewusst keine Anleitung zum Umgehen von Play Integrity, Banking-, DRM-, MDM-, Anti-Cheat- oder Unternehmensschutzmechanismen.

## Inhalt

- [[#Was Magisk ist]]
- [[#Bedrohungs- und Vertrauensmodell]]
- [[#Voraussetzungen]]
- [[#Boot, Partitionen und AVB]]
- [[#Vorbereitung und Backups]]
- [[#Grundprinzip der Installation]]
- [[#Patchen des eigenen Boot-Images]]
- [[#Flashen und erster Start]]
- [[#Root-Berechtigungen verwalten]]
- [[#Module]]
- [[#Zygisk]]
- [[#Updates]]
- [[#Bootloop und Recovery]]
- [[#Deinstallation]]
- [[#Sicherheitscheckliste]]
- [[#Diagnose]]
- [[#Schnellreferenz]]

## Was Magisk ist

Magisk ist eine Android-Werkzeugsammlung mit mehreren Komponenten:

| Komponente | Zweck |
|---|---|
| Magisk App | Installation, Status, Root-Anfragen, Module |
| MagiskSU | Root-Berechtigungen für Apps/Prozesse |
| MagiskBoot | Boot-Images entpacken, patchen und neu packen |
| Module | systemlose beziehungsweise bootnahe Erweiterungen |
| Zygisk | Code im Zygote-Prozessraum für kompatible Module |

„Systemless“ bedeutet nicht „spurlos“ und nicht „risikofrei“. Änderungen liegen typischerweise außerhalb einer direkten `/system`-Dateimodifikation, beeinflussen aber weiterhin Boot, Laufzeit und Vertrauenszustand.

## Bedrohungs- und Vertrauensmodell

Mit Root kann eine zugelassene App unter anderem:

- Dateien anderer Apps lesen,
- Systemeinstellungen verändern,
- Netzwerkverkehr beeinflussen,
- Prozesse instrumentieren,
- Schlüssel oder Tokens abgreifen,
- Sicherheitskontrollen deaktivieren.

Daher:

```text
Root-Anfrage = Administratorfreigabe
Magisk-Modul = Code mit sehr hohen Rechten
Boot-Image = sicherheitskritisches Artefakt
```

Nur Quellen nutzen, deren Code, Herausgeber und Updateweg nachvollziehbar sind.

## Voraussetzungen

Vor Beginn klären:

- exaktes Gerätemodell und Region,
- Buildnummer und Android-Sicherheitsstand,
- Bootloader entsperrbar?
- offizielles Factory-/OTA-Image verfügbar?
- verwendet das Gerät `boot`, `init_boot` oder `vendor_boot` für den relevanten Ramdisk-Pfad?
- A/B-Slots?
- funktionierendes `adb` und `fastboot`?
- vollständiges Datenbackup?
- Wiederherstellungsweg mit Originalimage?

Inventar:

```bash
adb shell getprop ro.product.model
adb shell getprop ro.product.device
adb shell getprop ro.build.fingerprint
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.security_patch
adb shell getprop ro.boot.slot_suffix
```

Bootloaderstatus ist herstellerspezifisch. Fastboot-Informationen:

```bash
adb reboot bootloader
fastboot devices
fastboot getvar product
fastboot getvar current-slot
fastboot getvar unlocked
```

Nicht jedes Gerät nutzt klassisches Fastboot; einige verwenden Fastbootd oder proprietäre Werkzeuge.

## Boot, Partitionen und AVB

Vereinfachtes Modell:

```text
Boot ROM
  -> Bootloader
      -> Android Verified Boot / vbmeta
          -> boot / init_boot / vendor_boot
              -> Kernel + Ramdisk
                  -> Android userspace
```

Relevante Partitionen variieren:

| Partition | Typischer Inhalt |
|---|---|
| `boot` | Kernel und/oder generische Ramdisk |
| `init_boot` | Ramdisk bei neueren Gerätearchitekturen |
| `vendor_boot` | vendor-spezifische Ramdisks/DTB |
| `vbmeta` | Verified-Boot-Metadaten |
| `recovery` | separate Recovery bei älteren Layouts |
| `super` | Container für dynamische Partitionen |

> [!danger] Kein universeller Flashbefehl
> `fastboot flash boot ...` ist nur korrekt, wenn genau dieses Gerät und diese Firmware `boot` als Ziel verlangen. Bei falscher Partition oder falschem Build droht ein Bootfehler. Immer die offizielle Magisk-Anleitung und Gerätespezifik prüfen.

Android Verified Boot bindet signierte Metadaten und Partitionen in eine Vertrauenskette ein. Ein entsperrter Bootloader zeigt dem Nutzer, dass die Vertrauenskette verändert werden darf; das ist nicht gleichbedeutend mit einem weiterhin „locked“ verifizierten Zustand.

## Vorbereitung und Backups

### Pflichtbackup

Mindestens:

- Fotos und Dokumente,
- 2FA-Recovery-Codes,
- Messenger-/App-Backups,
- Passwortmanager-Synchronisation prüfen,
- Geräteeinstellungen dokumentieren,
- Original-Firmware herunterladen,
- Original-`boot`/`init_boot`-Image separat sichern.

Prüfsumme des Firmwarepakets:

```bash
sha256sum factory-image.zip
```

Arbeitsverzeichnis:

```bash
mkdir -p ~/android/device-build123/{original,patched,logs}
chmod 700 ~/android/device-build123
```

Originalimage unverändert aufbewahren:

```bash
cp init_boot.img ~/android/device-build123/original/
sha256sum ~/android/device-build123/original/init_boot.img \
  > ~/android/device-build123/original/SHA256SUMS
```

### Firmware muss exakt passen

Nicht nur Modellname, sondern auch:

- Buildnummer,
- Region/Carrier,
- Android-Version,
- Patchstand,
- Slot-/Partitionlayout.

Ein Image aus einem „ähnlichen“ Build ist kein verlässlicher Ersatz.

## Grundprinzip der Installation

Der sichere generische Ablauf:

```text
passendes offizielles Firmwareimage beschaffen
        |
relevantes boot/init_boot/vendor_boot extrahieren
        |
auf demselben Android-Gerät mit offizieller Magisk-App patchen
        |
gepatchte Datei zurück zum Rechner übertragen
        |
Prüfsummen und Dateinamen dokumentieren
        |
über den gerätespezifischen Bootloaderweg flashen/testen
        |
Start prüfen, erst dann Module installieren
```

> [!important] Auf dem Zielgerät patchen
> Magisk empfiehlt, das Image auf demselben Gerät zu patchen, auf dem es verwendet wird. Keine vorgepatchten Images aus Foren oder Dateihostern übernehmen.

## Patchen des eigenen Boot-Images

### Datei auf das Gerät kopieren

```bash
adb push ./init_boot.img /sdcard/Download/
```

In der Magisk-App typischer Ablauf:

1. **Install**.
2. **Select and Patch a File**.
3. passendes `boot.img`, `init_boot.img` oder dokumentiertes Ziel wählen.
4. Patchvorgang abwarten.
5. erzeugten Dateinamen notieren.

Datei zurückholen:

```bash
adb shell ls -lh /sdcard/Download/magisk_patched-*.img
adb pull /sdcard/Download/magisk_patched-*.img ./patched/
sha256sum ./patched/magisk_patched-*.img
```

Eigene Benennung:

```bash
cp ./patched/magisk_patched-*.img \
  ./patched/init_boot-build123-magisk.img
```

Metadaten protokollieren:

```text
Gerät:
Build:
Originalimage SHA-256:
Gepatchtes Image SHA-256:
Magisk-Version:
Zielpartition:
Slot:
Datum:
```

## Flashen und erster Start

### Vor dem Flash

```bash
adb devices -l
adb reboot bootloader
fastboot devices
fastboot getvar current-slot
```

Ein gerätespezifisch dokumentiertes Beispiel könnte lauten:

```bash
fastboot flash init_boot init_boot-build123-magisk.img
fastboot reboot
```

Oder bei A/B-Partitionen explizit einen Slot betreffen. Das darf nicht geraten werden.

### Testboot, sofern unterstützt

Manche Geräte unterstützen:

```bash
fastboot boot patched_boot.img
```

Das lädt ein Image temporär, ohne es dauerhaft zu flashen. Nicht alle Geräte/Partitionstypen erlauben dies; `init_boot` wird häufig anders behandelt.

### Nach dem Start

1. vollständigen Boot abwarten,
2. Magisk-App öffnen,
3. installierte Version und Ramdisk-/Zygisk-Status prüfen,
4. ADB-Verbindung testen,
5. **noch keine Module** installieren,
6. Neustart testen,
7. erst danach schrittweise erweitern.

```bash
adb wait-for-device
adb shell getprop sys.boot_completed
adb shell su -c id
```

Root-Dialog nur bewusst bestätigen.

## Root-Berechtigungen verwalten

Grundregeln:

- standardmäßig verweigern,
- nur Apps mit nachvollziehbarem Bedarf erlauben,
- keine dauerhafte Freigabe für unbekannte Tools,
- Logs und letzte Anfragen regelmäßig prüfen,
- ungenutzte Root-Apps deinstallieren,
- Netzwerkzugriff zusätzlich kontrollieren.

Test:

```bash
adb shell
su
id
exit
exit
```

Erwartet nach Freigabe:

```text
uid=0(root) gid=0(root) ...
```

> [!warning] Shell-History und Secrets
> Root-Shell-Kommandos können sensible Pfade und Werte in History oder Logs hinterlassen. Secrets nicht als Klartextargumente eingeben.

## Module

Module laufen mit sehr hohen Rechten und können früh im Bootprozess eingreifen.

Vor Installation:

1. Quellcode/Repository prüfen.
2. Kompatibilität zu Android- und Magisk-Version prüfen.
3. letzte Updates und offene Sicherheitsprobleme prüfen.
4. Wiederherstellungsweg kennen.
5. nur **ein Modul pro Neustart** ändern.

Inventar in einer Root-Shell:

```bash
su -c 'ls -la /data/adb/modules'
su -c 'find /data/adb/modules -maxdepth 2 -type f -name module.prop -print'
```

Typische Modulstruktur:

```text
module-id/
├── module.prop
├── service.sh
├── post-fs-data.sh
├── system.prop
└── disable
```

Ein Modul deaktivieren, sofern Zugriff besteht:

```bash
adb shell su -c 'touch /data/adb/modules/MODULID/disable'
```

Danach neu starten.

> [!danger] ZIP nicht blind flashen
> Ein Modul-Archiv ist ausführbarer privilegierter Code. Dateiname, Signatur/Hash, Quelle und Inhalt prüfen.

## Zygisk

Zygote startet einen großen Teil der Android-App-Prozesse. Zygisk ermöglicht kompatiblen Modulen, Code in diesem Kontext auszuführen.

Konsequenzen:

- sehr mächtig,
- große Angriffsfläche,
- inkompatible Module können App-Crashes oder Bootprobleme verursachen,
- Updates von Android Runtime und Magisk können Kompatibilität ändern.

Zygisk nur aktivieren, wenn ein vertrauenswürdiger, klar begründeter Anwendungsfall besteht.

Nach Änderung:

```bash
adb logcat -b crash -d
adb shell su -c 'ls -la /data/adb/modules'
```

Keine Verwendung zur Umgehung von Integritäts- oder Zugriffsprüfungen.

## Updates

### Android-OTA

OTA-Mechanismen unterscheiden sich stark. Vor jedem Update:

- Changelog und Magisk-Kompatibilität prüfen,
- passendes neues Factory-/OTA-Image herunterladen,
- Originalimage des neuen Builds extrahieren,
- Backup und Akkustand prüfen,
- Module deaktivieren, wenn sie kritisch eingreifen,
- Wiederherstellungswerkzeuge bereithalten.

Bei A/B-Geräten existieren Magisk-Workflows für Updates auf den inaktiven Slot; sie sind versions- und geräteabhängig. Nicht aus einer alten Anleitung übernehmen.

### Magisk-Update

1. offizielle Quelle,
2. Release Notes lesen,
3. funktionierendes Originalimage bereithalten,
4. App aktualisieren,
5. Installationsmethode gemäß aktueller offizieller Anleitung,
6. Neustart,
7. Root, ADB, Module und Logs prüfen.

> [!warning] App und installierte Magisk-Version
> Die Version der Manager-App und die im Bootimage installierte Magisk-Komponente sind getrennte Zustände. Nach einem App-Update ist das Bootimage nicht automatisch aktualisiert.

## Bootloop und Recovery

### Erstdiagnose

Symptome unterscheiden:

| Zustand | Bedeutung |
|---|---|
| Bootanimation endlos | Kernel/userspace/Modulproblem |
| sofort Bootloader | Bootimage/AVB/Partition falsch |
| Recovery startet | Systemstart fehlgeschlagen |
| Gerät nicht erkannt | Kabel/Treiber/Bootmodus prüfen |
| ADB kurz verfügbar | Gelegenheit zum Modul-Deaktivieren |

### Sicherer Rückfallplan

1. nicht wiederholt beliebige Images flashen,
2. exakten Build und Slot prüfen,
3. Originalimage aus eigener Sicherung verwenden,
4. nur betroffene Partition zurücksetzen,
5. offizielle Recovery-/Factory-Anleitung beachten.

Generisches Beispiel – **Partition an Gerät anpassen**:

```bash
fastboot devices
fastboot getvar current-slot
fastboot flash init_boot original/init_boot.img
fastboot reboot
```

### Module deaktivieren

Wenn ADB und Root kurz verfügbar sind:

```bash
adb wait-for-device
adb shell su -c 'touch /data/adb/modules/MODULID/disable'
adb reboot
```

Oder alle Module kontrolliert deaktivieren:

```bash
adb shell su -c '
for d in /data/adb/modules/*; do
  [ -d "$d" ] && touch "$d/disable"
done
'
```

Nicht löschen, solange eine reversible Deaktivierung genügt.

### Logs sichern

```bash
adb logcat -b all -d > boot-failure-logcat.txt
adb shell su -c 'dmesg' > boot-failure-dmesg.txt
fastboot getvar all 2> fastboot-vars.txt
```

`fastboot getvar all` kann Seriennummern enthalten; vor Weitergabe bereinigen.

## Deinstallation

Bevorzugte Wege:

1. Magisk-App: vollständige Deinstallation gemäß aktueller Anleitung.
2. Originales passendes Boot-/Init-Boot-Image zurückflashen.
3. danach normalen Boot und OTA-Zustand prüfen.

Wichtig:

- Bootloader bleibt durch Magisk-Deinstallation nicht automatisch wieder gesperrt.
- Bootloader erst dann relocken, wenn **vollständig originale, signierte, passende Firmware** installiert ist.
- Falsches Relocking kann ein Gerät unbootbar machen.

> [!danger] Bootloader nicht voreilig sperren
> Ein gesperrter Bootloader mit modifizierten oder inkonsistenten Partitionen kann die Wiederherstellung deutlich erschweren.

## Sicherheitscheckliste

### Vorher

- [ ] Gerät/Build eindeutig dokumentiert
- [ ] vollständiges Backup getestet
- [ ] Originalimage und SHA-256 vorhanden
- [ ] ADB/Fastboot funktionieren
- [ ] Akku ausreichend
- [ ] Bootloaderfolgen verstanden
- [ ] Recoverypfad dokumentiert

### Nachher

- [ ] Hostrechner-Autorisierung kontrolliert
- [ ] Root nur minimal freigegeben
- [ ] keine unbekannten Module
- [ ] Neustart erfolgreich
- [ ] Sicherheitsupdates beobachtet
- [ ] Originalimage weiterhin verfügbar
- [ ] Gerät nicht mehr für besonders sensible Unternehmens-/Finanzanwendungen eingeplant, sofern Richtlinien dies ausschließen

## Diagnose

### ADB/Fastboot

```bash
adb devices -l
fastboot devices
```

Falls ADB funktioniert, Fastboot nicht:

- anderer Treiber/USB-Modus,
- Fastbootd statt Bootloader-Fastboot,
- Kabel/Port,
- Herstellerwerkzeug erforderlich.

### Magisk-Status

```bash
adb shell su -c id
adb shell su -c 'ls -la /data/adb'
adb shell su -c 'ls -la /data/adb/modules'
```

### Typische Ursachen

| Problem | Ursache | Nächster Schritt |
|---|---|---|
| App zeigt „nicht installiert“ | falsches/unverändertes Image gebootet | Slot/Build/Partition prüfen |
| kein Root-Dialog | App nicht erkannt oder Anfrage blockiert | Magisk-App, Logs, `su` prüfen |
| Bootloop nach Modul | inkompatibles Modul | `disable` setzen / Originalimage |
| Bootloaderwarnung | entsperrter Zustand | erwartbar; Sicherheitsmodell beachten |
| OTA schlägt fehl | modifizierte Bootpartition/Slot | offizieller Updateworkflow |
| Fastboot `partition not found` | falscher Partitionsname | Geräte-Doku, `getvar`, kein Raten |
| Imagegröße unpassend | falsches Image/Build | sofort stoppen, Original prüfen |
| Apps verweigern Dienst | Integritäts-/Richtlinienprüfung | nicht umgehen; unmodifiziertes Gerät nutzen |

### Prüfreihenfolge

```text
Gerätemodell -> Build -> Slot -> Zielpartition -> Original-Hash
-> gepatchter Hash -> Fastbootstatus -> Bootlog -> Module -> Rückfallimage
```

## Schnellreferenz

```bash
adb shell getprop ro.build.fingerprint
adb shell getprop ro.boot.slot_suffix
adb reboot bootloader
fastboot devices
fastboot getvar product
fastboot getvar current-slot
fastboot getvar unlocked
sha256sum original.img patched.img
adb push original.img /sdcard/Download/
adb pull /sdcard/Download/magisk_patched-*.img .
adb shell su -c id
adb shell su -c 'ls /data/adb/modules'
```

Merksatz:

```text
Exakter Build + eigenes Originalimage + dokumentierte Partition
+ ein Schritt pro Neustart + getesteter Rückfallweg
```

## Quellen
- [Offizielles Magisk-Repository](https://github.com/topjohnwu/Magisk)
- [Offizielle Magisk-Installationsanleitung](https://topjohnwu.github.io/Magisk/install.html)
- [Android Verified Boot](https://source.android.com/docs/security/features/verifiedboot)
- [Boot Flow](https://source.android.com/docs/core/architecture/bootloader)

## Verwandte Notizen
- [[USB-Debugging-und-ADB-Premium-Spickzettel]]
- [[Haven – Android SSH Client – Premium-Spickzettel]]
- [[dmesg-Premium-Spickzettel]]
- [[Linux-Dateisysteme-Premium-Spickzettel]]
