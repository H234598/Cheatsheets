---
title: "USB-Debugging und ADB – Cheatsheet"
aliases: ["Android Debug Bridge", "ADB Cheatsheet", "USB Debugging Android", "Android-USB-Debugging-Cheatsheet"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [android, adb, usb, debugging, developer-tools, security]
source: "https://developer.android.com/tools/adb"
---

# USB-Debugging und ADB – Cheatsheet

> [!abstract] Zweck
> Ausführliche Referenz für Android USB-Debugging und ADB: sichere Aktivierung, RSA-Autorisierung, Geräteerkennung, Shell, Dateien, APKs, Logcat, Portweiterleitungen, Wireless Debugging, Linux-udev, Windows-Treiber und Fehlerdiagnose.

> [!danger] Nur eigene oder autorisierte Geräte
> ADB kann Apps installieren, Dateien übertragen, Logs lesen, Portweiterleitungen aufbauen und – abhängig von Build und Rechten – tief in ein Gerät eingreifen. Ausschließlich an eigenen Geräten oder mit ausdrücklicher Berechtigung verwenden.

## Inhalt

- [[#Grundmodell]]
- [[#Platform Tools installieren]]
- [[#Entwickleroptionen und USB-Debugging]]
- [[#RSA-Autorisierung]]
- [[#Geräte erkennen und auswählen]]
- [[#ADB-Server verwalten]]
- [[#Shell und Systeminformationen]]
- [[#Dateien übertragen]]
- [[#Apps installieren und verwalten]]
- [[#Logcat und Bugreports]]
- [[#Portweiterleitungen]]
- [[#Wireless Debugging]]
- [[#Screenshots und Bildschirmaufnahme]]
- [[#Linux-udev und Berechtigungen]]
- [[#Windows-Treiber]]
- [[#Sicherheit nach der Arbeit]]
- [[#Diagnose]]
- [[#Schnellreferenz]]

## Grundmodell

ADB besteht aus drei Teilen:

```text
adb Client (Kommandozeile)
          |
          v
adb Server auf dem Rechner, meist TCP 5037 lokal
          |
     USB oder Netzwerk
          |
          v
adbd auf dem Android-Gerät
```

Der lokale Server verwaltet mehrere Geräte und Emulatoren.

Wichtige Begriffe:

| Begriff | Bedeutung |
|---|---|
| `adb` | Clientprogramm aus Android Platform Tools |
| ADB-Server | lokaler Vermittlungsprozess auf dem Entwicklungsrechner |
| `adbd` | Daemon auf Android |
| Serial | eindeutige Geräte-/Emulatorkennung |
| RSA-Prompt | Bestätigung, dass dieser Rechner debuggen darf |
| USB-Modus | Laden, Dateiübertragung, PTP usw.; unabhängig von ADB, aber Treiber können variieren |

## Platform Tools installieren

### Fedora

Distributionspaket:

```bash
sudo dnf install android-tools
adb version
```

### Debian/Ubuntu

```bash
sudo apt update
sudo apt install adb fastboot
adb version
```

### macOS mit Homebrew

```bash
brew install android-platform-tools
adb version
```

### Windows

Offizielle Android SDK Platform Tools entpacken, z. B.:

```powershell
$env:Path += ';C:\Tools\platform-tools'
adb version
```

Dauerhaft über Windows-Umgebungsvariablen oder einen Paketmanager eintragen.

> [!tip] Versionen nicht wild mischen
> Mehrere `adb`-Installationen in PATH führen oft zu Server-/Client-Versionskonflikten. Pfad prüfen:
>
> ```bash
> command -v -a adb
> adb version
> ```

## Entwickleroptionen und USB-Debugging

Typischer Android-Ablauf:

1. **Einstellungen → Über das Telefon**.
2. **Build-Nummer** mehrfach antippen, bis Entwickleroptionen aktiv sind.
3. Geräte-PIN bestätigen.
4. **System → Entwickleroptionen** öffnen.
5. **USB-Debugging** aktivieren.
6. Gerät entsperrt mit dem Rechner verbinden.

Hersteller verschieben die Menüs. Suchfunktion der Einstellungen nutzen.

USB-Kabel:

- muss Daten übertragen können,
- möglichst kurz und zuverlässig,
- Hubs/Docks bei Problemen zunächst umgehen,
- verschmutzte oder lockere USB-C-Buchsen ausschließen.

## RSA-Autorisierung

Beim ersten Kontakt zeigt Android einen Fingerprint-Dialog. Nur akzeptieren, wenn der Rechner vertrauenswürdig ist.

Status:

```bash
adb devices -l
```

Beispiele:

```text
R58N...        device       product:... model:... transport_id:1
R58N...        unauthorized usb:...
R58N...        offline
```

Bedeutung:

| Status | Interpretation |
|---|---|
| `device` | verbunden und autorisiert |
| `unauthorized` | RSA-Dialog nicht bestätigt oder Schlüssel verworfen |
| `offline` | Transport vorhanden, Protokoll hängt |
| kein Gerät | USB, Treiber, udev, Port oder Debugging prüfen |

Autorisierungen auf Android zurücksetzen:

```text
Entwickleroptionen → USB-Debugging-Autorisierungen widerrufen
```

Danach ADB neu starten und erneut verbinden.

Hostkeys liegen typischerweise unter:

```text
~/.android/adbkey
~/.android/adbkey.pub
```

Diese Dateien sind Vertrauensnachweise. Nicht unkontrolliert kopieren.

## Geräte erkennen und auswählen

Auflisten:

```bash
adb devices
adb devices -l
```

Ein bestimmtes Gerät:

```bash
adb -s SERIAL shell
adb -s SERIAL push datei /sdcard/Download/
```

USB-Gerät bevorzugen:

```bash
adb -d shell
```

Emulator bevorzugen:

```bash
adb -e shell
```

Transport-ID:

```bash
adb -t 1 shell
```

Bei genau einem Gerät reicht:

```bash
adb shell
```

> [!warning] Mehrere Geräte
> Ohne `-s` bricht ADB bei mehreren Zielen oft mit `more than one device/emulator` ab. In Skripten die Serial explizit setzen.

## ADB-Server verwalten

```bash
adb start-server
adb kill-server
adb reconnect
adb reconnect device
adb reconnect offline
```

Server-Port lokal prüfen:

```bash
ss -lntp | grep 5037
```

Mit Diagnoseausgabe:

```bash
ADB_TRACE=usb,transport adb devices
```

Nur kurz verwenden; Trace kann viele technische Details enthalten.

## Shell und Systeminformationen

Interaktive Shell:

```bash
adb shell
```

Einzelkommando:

```bash
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
adb shell uname -a
```

Nützliche Informationen:

```bash
adb shell getprop
adb shell dumpsys battery
adb shell dumpsys meminfo
adb shell dumpsys diskstats
adb shell df -h
adb shell ip addr
adb shell ip route
adb shell settings get global airplane_mode_on
```

Pakete:

```bash
adb shell pm list packages
adb shell pm list packages -3
adb shell pm path com.example.app
adb shell dumpsys package com.example.app
```

Aktuelle Activity:

```bash
adb shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity'
```

Prozesse:

```bash
adb shell ps -A
adb shell top -o PID,USER,CPU,RES,NAME -n 1
```

> [!note] Rechte
> Auf normalen Produktionsgeräten läuft `adbd` nicht als Root. `adb root` funktioniert typischerweise nur auf Emulatoren, `userdebug`- oder `eng`-Builds.

## Dateien übertragen

Vom Rechner zum Gerät:

```bash
adb push ./bericht.pdf /sdcard/Download/
```

Vom Gerät zum Rechner:

```bash
adb pull /sdcard/Download/log.txt ./
```

Fortschritt/Metadaten:

```bash
adb push -p datei.bin /sdcard/Download/
adb pull -a /sdcard/DCIM/Camera/ ./Camera-Backup/
```

Standardpfade variieren:

```text
/sdcard/
/storage/emulated/0/
/sdcard/Download/
/sdcard/DCIM/
```

App-internes Verzeichnis ist ohne passende Rechte nicht frei lesbar. Bei debuggable App:

```bash
adb shell run-as com.example.app ls -la
adb exec-out run-as com.example.app cat files/config.json > config.json
```

## Apps installieren und verwalten

APK installieren:

```bash
adb install app.apk
```

Bestehende App aktualisieren und Daten behalten:

```bash
adb install -r app.apk
```

Downgrade – nur wenn Plattform/App es erlaubt:

```bash
adb install -r -d app.apk
```

Test-APK:

```bash
adb install -t app-debug.apk
```

Split APKs:

```bash
adb install-multiple base.apk split_config.de.apk split_config.arm64_v8a.apk
```

Deinstallieren:

```bash
adb uninstall com.example.app
```

Daten behalten:

```bash
adb uninstall -k com.example.app
```

App stoppen/starten:

```bash
adb shell am force-stop com.example.app
adb shell monkey -p com.example.app -c android.intent.category.LAUNCHER 1
```

Daten löschen:

```bash
adb shell pm clear com.example.app
```

> [!danger] Datenverlust
> `pm clear` löscht App-Daten. Vorher Paketname und Backupstrategie prüfen.

## Logcat und Bugreports

Live-Logs:

```bash
adb logcat
```

Zeitformat und Filter:

```bash
adb logcat -v threadtime
adb logcat -v color
adb logcat ActivityManager:I MyApp:D '*:S'
```

Nur aktuelle Pufferinhalte:

```bash
adb logcat -d > logcat.txt
```

Puffer leeren:

```bash
adb logcat -c
```

Bestimmte PID:

```bash
PID=$(adb shell pidof com.example.app | tr -d '\r')
adb logcat --pid="$PID"
```

Crashpuffer:

```bash
adb logcat -b crash -d
```

Kernelzugriff ist auf Produktionsgeräten eingeschränkt. Alternativen:

```bash
adb shell dmesg
adb shell dumpsys dropbox
```

Bugreport:

```bash
adb bugreport bugreport.zip
```

> [!warning] Personenbezogene Daten
> Bugreports und Logcat können Kontonamen, URLs, Netzdetails, App-Inhalte und Identifikatoren enthalten. Vor Weitergabe prüfen und sicher speichern.

## Portweiterleitungen

### Host zu Gerät: `forward`

```bash
adb forward tcp:8080 tcp:8080
adb forward --list
adb forward --remove tcp:8080
adb forward --remove-all
```

Beispiel: Browser auf dem Rechner erreicht einen Dienst auf dem Gerät unter `localhost:8080`.

### Gerät zu Host: `reverse`

```bash
adb reverse tcp:3000 tcp:3000
adb reverse --list
adb reverse --remove tcp:3000
adb reverse --remove-all
```

Eine App auf dem Gerät kann dann `127.0.0.1:3000` nutzen, um den Entwicklungsserver des Rechners zu erreichen.

> [!warning] Bind-Adresse des Entwicklungsservers
> `adb reverse` vermeidet eine öffentliche LAN-Freigabe. Ohne Reverse nicht blind auf `0.0.0.0` lauschen, wenn localhost genügt.

## Wireless Debugging

Moderne Android-Versionen unterstützen Pairing über WLAN.

Typischer Ablauf:

1. Gerät und Rechner im selben vertrauenswürdigen Netz.
2. Entwickleroptionen → **Wireless Debugging**.
3. **Gerät mit Pairing-Code koppeln**.
4. IP:Pairing-Port und Code verwenden.

```bash
adb pair 192.0.2.10:37123
adb connect 192.0.2.10:43210
adb devices -l
```

Trennen:

```bash
adb disconnect 192.0.2.10:43210
adb disconnect
```

Älteres TCP/IP-Verfahren, zunächst per USB:

```bash
adb tcpip 5555
adb connect DEVICE_IP:5555
```

Danach wieder auf USB zurück:

```bash
adb usb
```

> [!danger] Kein offenes ADB im Fremdnetz
> ADB über TCP nicht dauerhaft in öffentlichen oder unkontrollierten Netzen betreiben. Nach der Arbeit Wireless Debugging deaktivieren und Pairings entfernen.

## Screenshots und Bildschirmaufnahme

Screenshot direkt auf den Rechner:

```bash
adb exec-out screencap -p > screenshot.png
```

Auf dem Gerät speichern:

```bash
adb shell screencap -p /sdcard/Download/screenshot.png
adb pull /sdcard/Download/screenshot.png
```

Bildschirmaufnahme:

```bash
adb shell screenrecord /sdcard/Download/demo.mp4
```

Mit Zeitlimit:

```bash
adb shell screenrecord --time-limit 30 /sdcard/Download/demo.mp4
adb pull /sdcard/Download/demo.mp4
```

Geräte-/App-Schutz kann vertrauliche Inhalte in Screenshots blockieren. Nicht umgehen.

## Linux-udev und Berechtigungen

USB-Gerät finden:

```bash
lsusb
journalctl -k -f
```

ADB als Benutzer testen:

```bash
adb kill-server
adb devices -l
```

Wenn nur Root das Gerät sieht, udev-Regel beziehungsweise Distributionspaket prüfen. Beispielstruktur:

```udev
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0660", GROUP="plugdev", TAG+="uaccess"
```

Danach:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Gerät neu verbinden. Vendor-ID muss zum tatsächlichen Hersteller passen.

> [!warning] Keine pauschalen Weltrechte
> `MODE="0666"` für alle Android-Geräte ist bequem, aber unnötig weit. `uaccess` oder eine kontrollierte Gruppe bevorzugen.

Fedora nutzt häufig ACLs über `uaccess`; Debian-Derivate teils `plugdev`. Vor eigenen Regeln vorhandene Pakete prüfen.

## Windows-Treiber

Geräte-Manager öffnen:

```powershell
Start-Process devmgmt.msc
```

Prüfen:

- erscheint das Gerät unter **Android Device**, **Portable Devices** oder **Andere Geräte**?
- ist der OEM-USB-Treiber installiert?
- kollidiert ein alter Universal-ADB-Treiber?
- funktioniert ein anderer USB-Port ohne Dock?

ADB-Prozess prüfen:

```powershell
Get-Process adb -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 5037 -ErrorAction SilentlyContinue
```

Server neu starten:

```powershell
adb kill-server
adb start-server
adb devices -l
```

## Sicherheit nach der Arbeit

1. Sensible Shell beenden.
2. Portweiterleitungen entfernen.
3. Wireless Debugging deaktivieren.
4. USB-Debugging deaktivieren, wenn es nicht regelmäßig benötigt wird.
5. Nicht mehr benötigte Rechner-Autorisierungen widerrufen.
6. Bugreports/Logs sicher löschen oder archivieren.
7. Gerät sperren.

Kommandos:

```bash
adb forward --remove-all
adb reverse --remove-all
adb disconnect
adb kill-server
```

## Diagnose

### Standardablauf

```bash
adb version
command -v adb
adb kill-server
adb start-server
adb devices -l
```

Dann:

1. Gerät entsperren.
2. USB-Debugging prüfen.
3. RSA-Dialog prüfen.
4. Datenkabel/Port wechseln.
5. `lsusb` beziehungsweise Geräte-Manager prüfen.
6. udev/Treiber prüfen.
7. andere ADB-Versionen/Prozesse beenden.
8. Gerät und Rechner neu verbinden.

### Typische Fehler

| Fehler | Ursache | Lösung |
|---|---|---|
| `unauthorized` | RSA nicht bestätigt | Display entsperren, Dialog bestätigen |
| `offline` | hängender Transport | `adb reconnect`, Kabel neu |
| kein Eintrag | Kabel/Treiber/udev | USB-Inventar und Rechte prüfen |
| `no permissions` | Linux-udev | Paket/Regel/uaccess prüfen |
| `more than one device` | mehrere Ziele | `adb -s SERIAL ...` |
| `cannot bind 5037` | anderer Server/Prozess | Prozess und ADB-Version prüfen |
| `INSTALL_FAILED_VERSION_DOWNGRADE` | ältere Version | korrekte Version; `-d` nur bewusst |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Signatur anders | richtige Signatur oder kontrollierte Neuinstallation |
| `run-as: package not debuggable` | Release-App | Debug-Build verwenden |
| Wireless verbindet nicht | Pairing- und Connect-Port verwechselt | beide Anzeigen exakt nutzen |

### USB-Kernellog unter Linux

```bash
sudo journalctl -k -f
# Gerät ab- und anstecken
```

Auf Meldungen achten:

- Disconnect/Reconnect-Schleifen,
- Strom-/Descriptorfehler,
- falsche Geschwindigkeit,
- defekter Hub oder Kabel.

## Schnellreferenz

```bash
adb devices -l
adb -s SERIAL shell
adb push file /sdcard/Download/
adb pull /sdcard/Download/file .
adb install -r app.apk
adb logcat -v threadtime
adb bugreport bugreport.zip
adb forward tcp:8080 tcp:8080
adb reverse tcp:3000 tcp:3000
adb pair IP:PAIRPORT
adb connect IP:ADBPORT
adb exec-out screencap -p > screenshot.png
adb forward --remove-all
adb reverse --remove-all
adb disconnect
```

## Quellen
- [Android Debug Bridge – offizielle Dokumentation](https://developer.android.com/tools/adb)
- [SDK Platform Tools Release Notes](https://developer.android.com/tools/releases/platform-tools)
- [Run apps on a hardware device](https://developer.android.com/studio/run/device)

## Verwandte Notizen
- [[Haven – Android SSH Client – Cheatsheet]]
- [[Magisk-Cheatsheet]]
- [[dmesg-Cheatsheet]]
- [[Windows-Terminal-Cheatsheet]]
