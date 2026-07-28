---
title: Haven – Android SSH Client – Cheatsheet
aliases:
- GlassHaven
- Haven SSH Client
- Android SSH VNC RDP SFTP
- Haven Android SSH-Client – Cheatsheet
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags:
- android
- ssh
- sftp
- vnc
- rdp
- mosh
- remote-access
source: https://github.com/openssh-haven/haven
---

# Haven – Android SSH Client – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für den freien Android-Remote-Client Haven: Verbindungsprofile, SSH-Schlüssel, Hostkey-Prüfung, SFTP, Portweiterleitungen, Mosh/Eternal Terminal, VNC/RDP, Tastaturbedienung, Android-Hintergrundlimits und Diagnose.

> [!note] Begriffsklärung
> Mit **Haven** ist hier die quelloffene Android-App von **GlassHaven** gemeint. Sie bündelt SSH-Terminal, SFTP sowie – je nach Protokoll und Server – VNC, RDP, Mosh und weitere Remote-Funktionen. Menünamen können sich zwischen App-Versionen leicht ändern.

> [!danger] Hostkey-Warnungen ernst nehmen
> Eine verschlüsselte SSH-Verbindung ist nur dann vertrauenswürdig, wenn der Hostkey zum richtigen Server gehört. Einen geänderten Fingerprint nicht blind akzeptieren: Serverwechsel, Neuinstallation und ein möglicher Man-in-the-Middle-Angriff sehen zunächst ähnlich aus.

## Inhalt

- [[#Einsatzmodell]]
- [[#Installation und Vertrauensquelle]]
- [[#Erstes SSH-Profil]]
- [[#SSH-Schlüssel erzeugen und importieren]]
- [[#Hostkeys und Fingerprints]]
- [[#Terminalbedienung auf Android]]
- [[#SFTP und Dateitransfer]]
- [[#Portweiterleitungen und Bastion Hosts]]
- [[#Mosh, Eternal Terminal und Multiplexer]]
- [[#VNC, RDP und Wayland-Desktops]]
- [[#Android-Hintergrundbetrieb]]
- [[#Sicherheit und Datenschutz]]
- [[#Diagnose]]
- [[#Schnellreferenz]]

## Einsatzmodell

Haven ist ein **Client**. Die Zielsysteme müssen die jeweiligen Dienste bereits anbieten:

| Funktion | Serverseite | Typischer Port |
|---|---|---:|
| SSH-Terminal | OpenSSH/SSH-Server | TCP 22 |
| SFTP | SSH-Subsystem `sftp` | TCP 22 |
| Mosh | `mosh-server` plus SSH-Start | SSH 22, danach UDP-Bereich |
| Eternal Terminal | `etserver` | konfigurationsabhängig |
| VNC | VNC-Server | häufig TCP 5900+n |
| RDP | Windows RDP oder xrdp | TCP/UDP 3389 |
| Wayland-Remote-Desktop | passender Compositor/Server | implementierungsabhängig |

Grundprinzip:

```text
Android + Haven
      |
      +-- SSH/SFTP ----> Linux/BSD/Netzwerkgerät
      +-- RDP ---------> Windows/xrdp
      +-- VNC ---------> VNC-Server
      +-- Mosh/ET -----> instabilere oder mobile Netze
```

> [!tip] VPN statt offene Adminports
> Für private Netze ist ein VPN wie WireGuard meist besser als SSH, VNC oder RDP direkt aus dem Internet freizugeben. Danach verbindet Haven sich auf die interne Adresse.

## Installation und Vertrauensquelle

Bevorzugte Bezugsquellen:

1. Projektseite beziehungsweise offizielles GitHub-Repository.
2. F-Droid-Repository, dessen Signatur und Paketkennung geprüft wurden.
3. Keine zufälligen APK-Spiegel.

Paketkennung nach aktuellem Projektstand:

```text
sh.haven.app
```

Nach Installation prüfen:

- App-Berechtigungen nur nach Bedarf erteilen.
- Benachrichtigungen erlauben, wenn Sitzungen im Hintergrund stabil bleiben sollen.
- Akkuoptimierung nur für einen konkreten Bedarf lockern.
- Exporte mit Profilen oder Schlüsseln verschlüsselt und kontrolliert behandeln.

## Erstes SSH-Profil

Benötigte Felder:

| Feld | Beispiel | Hinweis |
|---|---|---|
| Name | `web-prod` | sprechender Profilname |
| Host | `web01.example.org` | DNS-Name bevorzugt |
| Port | `22` | Sonderport nur bei Serverkonfiguration |
| Benutzer | `admin` | nicht automatisch `root` |
| Authentisierung | Schlüssel | Passwort nur falls erforderlich |
| Startkommando | leer oder `tmux attach` | optional |

Server vorab von einem Desktop testen:

```bash
ssh -vvv admin@web01.example.org
```

Auf dem Server:

```bash
sudo systemctl status sshd 2>/dev/null || sudo systemctl status ssh
sudo ss -lntp | grep ':22 '
```

### Sinnvolle Profiltrennung

Nicht ein Universalprofil für alles verwenden:

```text
prod-readonly
prod-admin
lab-root
home-nas
bastion-corp
```

Dadurch bleiben Benutzer, Keys und Sicherheitsniveau nachvollziehbar.

## SSH-Schlüssel erzeugen und importieren

### Empfohlener Schlüsseltyp

Für moderne OpenSSH-Systeme:

```bash
ssh-keygen -t ed25519 -a 64 -C 'android-haven'
```

Public Key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Auf Zielserver installieren:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server
```

Oder kontrolliert manuell:

```bash
install -d -m 700 ~/.ssh
cat >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Import in Haven

Typischer Ablauf:

1. Privaten Schlüssel über einen sicheren lokalen Weg auf das Android-Gerät bringen.
2. In Havens Schlüsselverwaltung importieren.
3. Passphrase verwenden.
4. Schlüssel einem oder wenigen Profilen zuordnen.
5. Temporäre Importdatei sicher löschen.

> [!warning] Privater Schlüssel ist kein Passwortzettel
> Den privaten Schlüssel nicht per unverschlüsselter E-Mail, Messenger-Cloud oder öffentlich synchronisiertem Ordner transportieren. Besser: lokal über USB, verschlüsselten Container oder einmaligen sicheren Transfer.

### Besser: separater Mobil-Schlüssel

Für das Smartphone einen eigenen Key erzeugen:

```text
id_ed25519_laptop
id_ed25519_phone_haven
id_ed25519_automation
```

Vorteile:

- selektiv widerrufbar,
- Geräteverlust betrifft nicht alle Zugänge,
- Audit-Logs sind besser zuzuordnen.

### `authorized_keys` einschränken

Beispiel für einen nur aus dem VPN erlaubten Key:

```text
from="10.8.0.0/24",no-agent-forwarding,no-X11-forwarding ssh-ed25519 AAAA... android-haven
```

Für reine SFTP-Konten sind serverseitig `ForceCommand internal-sftp`, Chroot und eingeschränkte Rechte sinnvoll.

## Hostkeys und Fingerprints

Serverfingerprint lokal anzeigen:

```bash
sudo ssh-keygen -E sha256 -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Remote vorab einsammeln – noch **ohne** Vertrauensbeweis:

```bash
ssh-keyscan -t ed25519 server.example.org
ssh-keyscan -t ed25519 server.example.org | ssh-keygen -lf -
```

Fingerprint über einen unabhängigen Kanal vergleichen:

- Serverkonsole,
- internes CMDB/Inventar,
- Administrator telefonisch,
- signierte Dokumentation.

Bei legitimer Serverneuinstallation:

1. alten Fingerprint dokumentieren,
2. neuen Fingerprint separat verifizieren,
3. alten Hostkey-Eintrag im Client gezielt ersetzen,
4. nicht die gesamte Known-Hosts-Datenbank löschen.

## Terminalbedienung auf Android

### Steuerzeichen

Mobile Tastaturen zeigen nicht alle Terminaltasten. Wichtig sind:

| Taste | Wirkung |
|---|---|
| `Ctrl+C` | laufenden Vordergrundprozess unterbrechen |
| `Ctrl+D` | EOF / Shell verlassen |
| `Ctrl+L` | Bildschirm neu zeichnen |
| `Ctrl+R` | Shell-History durchsuchen |
| `Ctrl+Z` | Prozess suspendieren |
| `Tab` | vervollständigen |
| `Esc` | Vim/Neovim Normal Mode, viele TUI-Funktionen |
| Pfeile | History beziehungsweise Navigation |

Haven bietet je nach Version Zusatzleiste, Makros und externe Tastaturunterstützung. Sinnvolle Makros:

```text
Ctrl+C
Ctrl+L
Esc
Tab
|
~
/
```

### Shell für kleine Displays vorbereiten

```bash
export TERM=xterm-256color
stty rows 40 cols 100
```

Die Größe sollte normalerweise automatisch ausgehandelt werden. `stty` nur zur Diagnose setzen.

Kurzer Prompt spart Platz:

```bash
export PS1='\u@\h:\W\$ '
```

### Multiplexer verwenden

Auf dem Server:

```bash
tmux new -s mobile
tmux attach -t mobile
```

Damit überlebt der Arbeitszustand einen App-Wechsel oder Netzabbruch.

## SFTP und Dateitransfer

SFTP läuft innerhalb von SSH. Es braucht normalerweise keinen separaten FTP-Port.

Server prüfen:

```bash
sftp user@server
```

OpenSSH-Konfiguration:

```text
Subsystem sftp internal-sftp
```

Typische Operationen in Havens Dateibrowser:

- Verzeichnis wechseln,
- hoch- und herunterladen,
- umbenennen,
- neue Ordner anlegen,
- Rechte anzeigen oder ändern, sofern unterstützt.

> [!danger] Zielpfad kontrollieren
> Vor Uploads in Produktionssysteme Pfad, Besitzer und freie Kapazität prüfen. Eine Datei im falschen Webroot oder Konfigurationsordner kann unmittelbar wirksam werden.

Serverseitige Kontrollen:

```bash
pwd
id
ls -ld /ziel /ziel/datei
findmnt -T /ziel
df -hT /ziel
```

Große oder wiederholte Transfers besser mit `rsync`, `rclone` oder Syncthing von einem geeigneten Host aus durchführen.

## Portweiterleitungen und Bastion Hosts

Nicht jede Haven-Version bildet jede OpenSSH-Option exakt gleich ab. Die Konzepte:

### Lokale Weiterleitung

```bash
ssh -L 8080:127.0.0.1:8080 user@server
```

Android öffnet lokal Port 8080; der Zielserver erreicht dort seinen eigenen Port 8080.

### Zugriff auf internes Ziel über Bastion

Desktop-Referenz:

```bash
ssh -J jump.example.org internal.example.org
```

Falls Haven Jump Hosts unterstützt:

1. Bastion als eigenes Profil anlegen.
2. Zielprofil über diese Bastion routen.
3. getrennte Hostkeys und Keys beibehalten.

### SOCKS-Proxy

```bash
ssh -D 1080 user@server
```

Nur nutzen, wenn die Android-App oder ein lokaler Proxy-Client den SOCKS-Port kontrolliert verwenden kann. Nicht versehentlich den gesamten Geräteverkehr ohne DNS-/Leak-Konzept routen.

> [!warning] Remote Forwarding
> `-R` kann einen Dienst auf der Serverseite veröffentlichen. `GatewayPorts`, Bind-Adresse und Firewall entscheiden, ob nur localhost oder das Netz zugreifen kann. Vor Nutzung bewusst prüfen.

## Mosh, Eternal Terminal und Multiplexer

### Mosh

Mosh eignet sich für wechselnde Netze und hohe Latenz. Ablauf:

1. SSH startet `mosh-server`.
2. Danach läuft die Sitzung überwiegend über UDP.
3. Client-IP-Wechsel kann toleriert werden.

Serverinstallation:

```bash
sudo dnf install mosh
sudo apt install mosh
```

Firewall-Beispiel – Bereich bewusst eingrenzen:

```bash
sudo firewall-cmd --permanent --add-port=60000-61000/udp
sudo firewall-cmd --reload
```

Besser einen kleineren, dokumentierten Bereich konfigurieren, sofern Client und Server das unterstützen.

### Eternal Terminal

Eternal Terminal hält Shell-Sitzungen bei Unterbrechungen stabil. Server und Client müssen kompatibel konfiguriert sein. Dienststatus und Port prüfen:

```bash
systemctl status et
ss -lntup
```

### tmux, zellij, screen, byobu

Diese Werkzeuge laufen **auf dem Server**. Sie ergänzen SSH/Mosh/ET, ersetzen aber nicht Transportverschlüsselung und Authentisierung.

```bash
tmux new -As main
zellij attach --create main
screen -DR main
```

## VNC, RDP und Wayland-Desktops

### RDP

Windows:

```powershell
Get-Service TermService
Test-NetConnection localhost -Port 3389
```

Linux mit xrdp:

```bash
systemctl status xrdp
ss -lntp | grep 3389
```

Sicherheitsgrundsätze:

- RDP nicht unnötig direkt ins Internet stellen.
- NLA/MFA/VPN verwenden, wenn verfügbar.
- Zertifikatswarnungen prüfen.
- Kontosperr- und Brute-Force-Schutz aktivieren.

### VNC

VNC ist häufig nicht eigenständig sicher verschlüsselt. Bevorzugt:

```text
VNC über VPN
oder
VNC über SSH-Tunnel
```

Typischer lokaler Tunnel:

```bash
ssh -L 5901:127.0.0.1:5901 user@server
```

Danach VNC-Client auf `127.0.0.1:5901` richten.

### Wayland

Wayland selbst ist kein universelles Remote-Desktop-Protokoll. Es braucht einen passenden Compositor-, Portal- oder Servermechanismus. Prüfen:

```bash
echo "$XDG_SESSION_TYPE"
loginctl show-session "$XDG_SESSION_ID" -p Type -p Remote
```

## Android-Hintergrundbetrieb

Android kann Netzwerk-Sockets und Hintergrundprozesse drosseln. Symptome:

- Sitzung trennt beim Display-Aus,
- Upload bleibt stehen,
- Mosh/SSH reconnectet häufig,
- Benachrichtigungsdienst wird beendet.

Prüfen:

1. App nicht durch einen Hersteller-„Cleaner“ automatisch beenden lassen.
2. Benachrichtigungsberechtigung aktivieren.
3. Akkuoptimierung nur für Haven lockern, wenn nötig.
4. WLAN-Schlaf-/VPN-Verhalten testen.
5. Serverseitig `tmux` oder `zellij` nutzen.
6. SSH-Keepalives maßvoll konfigurieren.

ServerAlive-Referenz:

```sshconfig
ServerAliveInterval 30
ServerAliveCountMax 3
```

Zu aggressive Intervalle erhöhen Funk- und Akkuverbrauch.

## Sicherheit und Datenschutz

Checkliste:

- Gerätesperre mit starker PIN/Passphrase.
- Android aktuell halten.
- Haven nur aus vertrauenswürdiger Quelle.
- Schlüssel mit Passphrase.
- separater Key pro Gerät und Zweck.
- keine Passwörter in Profilnamen, Notizen oder Makros.
- Hostkeys verifizieren.
- Agent Forwarding standardmäßig aus.
- Root-Login vermeiden.
- VPN/Bastion für Adminnetze.
- verlorenes Gerät sofort: Keys aus `authorized_keys`, Zertifikate/Tokens widerrufen.

> [!warning] Zwischenablage
> Kennwörter und Secrets können in Zwischenablage-History, Tastatur-Cloud oder Accessibility-Diensten landen. Besser Passwortmanager-Autofill beziehungsweise kurzlebige Tokens verwenden und Zwischenablage anschließend leeren.

## Diagnose

### Universelle Prüfreihenfolge

1. Ist das Ziel per DNS/IP erreichbar?
2. Ist der Port erreichbar?
3. Läuft der Serverdienst?
4. Stimmt der Hostkey?
5. Stimmt Benutzer/Authentisierung?
6. Akzeptiert der Server den Algorithmus?
7. Blockiert VPN, Firewall oder Mobilfunkprovider?
8. Beendet Android die App im Hintergrund?

### DNS und Netz

Von einem Vergleichsgerät:

```bash
getent ahosts server.example.org
ping -c 3 server.example.org
nc -vz server.example.org 22
```

### Serverlogs

Fedora/RHEL:

```bash
sudo journalctl -u sshd -b --no-pager
sudo journalctl -u sshd -f
```

Debian/Ubuntu:

```bash
sudo journalctl -u ssh -b
sudo tail -f /var/log/auth.log
```

### Typische Fehler

| Meldung/Symptom | Wahrscheinliche Ursache | Nächster Schritt |
|---|---|---|
| `Connection timed out` | Route/Firewall/Port falsch | DNS, VPN, Porttest |
| `Connection refused` | Dienst lauscht nicht | `ss -lntp`, Dienststatus |
| `No route to host` | Routing oder ICMP-Fehler | Gateway/VPN/Firewall |
| `Host key has changed` | Server neu oder Angriff | Fingerprint separat prüfen |
| `Permission denied (publickey)` | Key/Benutzer/Rechte | `authorized_keys`, Logs |
| Passwort wird immer abgelehnt | Passwortauth aus/MFA/PAM | `sshd -T`, Auth-Logs |
| Sitzung stirbt beim Sperren | Android-Drosselung | Akku/Benachrichtigung, tmux |
| SFTP fehlt | Subsystem deaktiviert | `sshd_config`, Logs |
| Mosh startet, verbindet aber nicht | UDP blockiert | UDP-Portbereich/Firewall |
| schwarze VNC-Fläche | Session/Compositor/Rechte | Serverlog, Displaynummer |

### Serverseitige SSH-Sollwerte prüfen

```bash
sudo sshd -t
sudo sshd -T | grep -E '^(port|passwordauthentication|pubkeyauthentication|permitrootlogin|allowtcpforwarding)'
```

## Schnellreferenz

```text
Profil: Host + Port + Benutzer + dedizierter Key
Vertrauen: Hostkey über unabhängigen Kanal prüfen
Stabilität: tmux/zellij; bei Mobilnetzen Mosh erwägen
Dateien: SFTP für einzelne Transfers, rsync/rclone für große Jobs
Sicherheit: VPN/Bastion, kein Root-Login, kein blindes Hostkey-Akzeptieren
Fehler: DNS -> Port -> Dienst -> Hostkey -> Auth -> Serverlog -> Android-Akku
```

## Quellen
- [GlassHaven/Haven auf GitHub](https://github.com/openssh-haven/haven)
- [Haven bei F-Droid](https://f-droid.org/packages/sh.haven.app/)
- [OpenSSH Manual Pages](https://www.openssh.com/manual.html)
- [Mosh](https://mosh.org/)

## Verwandte Notizen
- [[SSH – Cheatsheet]]
- [[USB-Debugging-und-ADB-Cheatsheet]]
- [[Linux-Netzwerk-Cheatsheet]]
- [[Wireshark-Cheatsheet]]
