---
title: "Termux – Premium-Spickzettel"
aliases: ["Termux Cheatsheet", "Android Terminal Spickzettel", "Termux Administration"]
created: 2026-07-16
modified: 2026-07-17
type: reference
status: fertig
origin: "Premium Spickzettel I – vollständig überarbeitet"
reviewed: 2026-07-17
tags: [termux, android, linux, shell, ssh, automation, syncthing, termux-api]
source: "https://github.com/termux/termux-app"
---

# Termux – Premium-Spickzettel

> [!abstract] Zweck
> Praxisreferenz für Termux unter Android: Editionen und Installation, Paketverwaltung, Speicher, Shell, SSH, Git, Python, Compiler, PRoot, Android-Prozesslimits, Termux:API, Boot/Widget, Backups, sichere Automation und Diagnose.

> [!important] Grundmodell
> Termux ist eine Android-App mit eigener Linux-artiger Benutzerumgebung. Es ist standardmäßig weder eine klassische VM noch ein vollständiger Linux-Container und verwendet Androids Kernel sowie Bionic statt einer üblichen glibc-Distribution.

## Inhalt

- [[#Editionen, Installation und Signaturen]]
- [[#Umgebung und wichtige Pfade]]
- [[#Paketverwaltung]]
- [[#Android-Speicher]]
- [[#Shell, Dateien und Editoren]]
- [[#SSH-Client und SSH-Server]]
- [[#Git und Schlüssel]]
- [[#Python, Node.js und Compiler]]
- [[#PRoot-Distributionen]]
- [[#Wake Locks und Android-Prozesslimits]]
- [[#Termux API]]
- [[#Boot, Widget und Tasker]]
- [[#Backups und Wiederherstellung]]
- [[#Sichere Automation]]
- [[#Fehlerdiagnose]]
- [[#Schnellreferenz]]

## Editionen, Installation und Signaturen

Termux wird über unterschiedliche Vertriebswege angeboten. Wichtig ist nicht nur die Versionsnummer, sondern die **Signaturfamilie**:

```text
Haupt-App und Add-ons müssen aus kompatibler Quelle stammen.
F-Droid/GitHub/Google-Play-Varianten nicht ungeprüft mischen.
```

Prüfen:

```bash
termux-info
```

Vor einem Wechsel der Vertriebsquelle:

1. Home, Prefix und Nutzdaten sichern;
2. installierte Pakete exportieren;
3. Haupt-App und Add-ons inventarisieren;
4. alle Apps der alten Signaturfamilie deinstallieren;
5. neue Edition installieren;
6. Backup kontrolliert wiederherstellen;
7. API, Boot, Widget und SSH testen.

> [!warning]
> Ein Update über eine anders signierte Edition kann scheitern. Die Google-Play-Variante besitzt außerdem einen eigenen Entwicklungs-/Paketkontext; Anleitungen und Paketverfügbarkeit können abweichen.

## Umgebung und wichtige Pfade

```bash
printf 'HOME=%s\nPREFIX=%s\nTMPDIR=%s\n' \
  "$HOME" "$PREFIX" "$TMPDIR"
```

Typische Pfade:

| Zweck | Pfad |
|---|---|
| Home | `$HOME` |
| Prefix | `$PREFIX` |
| Programme | `$PREFIX/bin` |
| Konfiguration | `$PREFIX/etc` |
| Bibliotheken | `$PREFIX/lib` |
| Temporär | `$TMPDIR` |
| Shared Storage | `$HOME/storage/shared` nach Freigabe |
| App-Datenbasis | `/data/data/com.termux/files/` |

Systeminformationen:

```bash
termux-info
uname -a
getprop ro.build.version.release
getprop ro.product.manufacturer
getprop ro.product.model
```

> [!note]
> Pfade wie `/usr/bin`, `/bin`, `/etc` oder `/var` existieren nicht in der üblichen Linux-Bedeutung. Skripte portabel mit `#!/usr/bin/env bash` oder dem tatsächlichen Termux-Pfad schreiben.

## Paketverwaltung

Aktualisieren:

```bash
pkg update
pkg upgrade
```

Suchen, installieren, entfernen:

```bash
pkg search openssh
pkg install openssh git curl wget
pkg uninstall paketname
```

Informationen:

```bash
pkg show openssh
pkg list-installed
apt-cache policy openssh
```

Aufräumen:

```bash
apt autoremove
apt clean
```

Repository/Mirror wechseln:

```bash
termux-change-repo
```

Zusätzliche Repositories, sofern für die Edition verfügbar:

```bash
pkg install root-repo
pkg install x11-repo
```

Paketliste exportieren:

```bash
dpkg-query -W -f='${binary:Package}\n' | sort > "$HOME/packages.txt"
```

Wieder installieren, mit Prüfung:

```bash
xargs -r pkg install -y < "$HOME/packages.txt"
```

> [!warning]
> Nicht jede alte Paketliste ist auf einer anderen Android-, Architektur- oder Termux-Edition reproduzierbar. Erst Basisumgebung aktualisieren, dann schrittweise installieren.

## Android-Speicher

Freigabe anfordern:

```bash
termux-setup-storage
```

Danach:

```bash
ls -la "$HOME/storage"
```

Typische Symlinks:

| Link | Ziel |
|---|---|
| `$HOME/storage/shared` | gemeinsamer interner Speicher |
| `$HOME/storage/downloads` | Download |
| `$HOME/storage/dcim` | Kamera/DCIM |
| `$HOME/storage/pictures` | Bilder |
| `$HOME/storage/music` | Musik |
| `$HOME/storage/movies` | Videos |

Zugriff testen:

```bash
test -r "$HOME/storage/shared" && echo lesbar
test -w "$HOME/storage/shared" && echo schreibbar
```

> [!important]
> Shared Storage bildet Unix-Eigenschaften nur eingeschränkt ab. Ausführungsbits, Symlinks, Eigentümer, Locks, Sonderdateien und Groß-/Kleinschreibung können problematisch sein. Git-Repositories, virtuelle Umgebungen und ausführbare Skripte besser unter `$HOME` halten.

Robustes Spiegelmuster:

```bash
rsync -a --delete \
  --exclude='.git/' \
  "$HOME/repos/NOTIZEN/" \
  "$HOME/storage/shared/Documents/NOTIZEN/"
```

Scoped Storage und Herstelleranpassungen können den Zugriff zusätzlich beeinflussen.

## Shell, Dateien und Editoren

Grundpakete:

```bash
pkg install coreutils findutils grep sed gawk tar zip unzip rsync
pkg install nano vim neovim
```

Shell:

```bash
pkg install zsh
chsh -s zsh
```

Konfiguration:

```text
$HOME/.bashrc
$HOME/.zshrc
$HOME/.profile
```

Persönliche Programme:

```bash
mkdir -p "$HOME/.local/bin"
printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$HOME/.bashrc"
```

Shebang:

```bash
#!/usr/bin/env bash
```

Termux-spezifisch:

```bash
#!/data/data/com.termux/files/usr/bin/bash
```

> [!tip]
> `env` ist portabler innerhalb Termux/PRoot. Ein absoluter Termux-Pfad ist eindeutiger, funktioniert aber außerhalb dieser App nicht.

Dateien sicher bearbeiten:

```bash
cp -a datei.conf datei.conf.bak
nvim datei.conf
cmp -s datei.conf datei.conf.bak || diff -u datei.conf.bak datei.conf
```

## SSH-Client und SSH-Server

Installieren:

```bash
pkg install openssh
```

### Client

```bash
ssh user@server.example.org
ssh -p 2222 user@server.example.org
scp datei.txt user@server:/ziel/
rsync -av -e ssh quelle/ user@server:/ziel/
```

Schlüssel:

```bash
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -a 100 -f "$HOME/.ssh/id_ed25519"
```

Agent:

```bash
eval "$(ssh-agent -s)"
ssh-add "$HOME/.ssh/id_ed25519"
ssh-add -l
```

Konfiguration:

```sshconfig
Host meinserver
    HostName server.example.org
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

### Server

Passwort nur falls benötigt:

```bash
passwd
```

Start:

```bash
sshd
```

Termux-OpenSSH verwendet typischerweise Port `8022`:

```bash
whoami
ip addr
ss -ltnp
ssh -p 8022 TERMUX_USER@ANDROID_IP
```

Stoppen:

```bash
pkill sshd
```

Konfiguration prüfen:

```bash
sshd -T | less
```

Public-Key-Verzeichnis:

```bash
chmod 700 "$HOME/.ssh"
chmod 600 "$HOME/.ssh/authorized_keys"
```

> [!warning]
> Einen SSH-Server nicht ungeschützt in fremden Netzen betreiben. Public Keys, Firewall/VPN, kurze Laufzeit und bekannte Clients bevorzugen. Android kann Netzwerk und Hintergrundprozess trotzdem beenden.

## Git und Schlüssel

```bash
pkg install git openssh

git config --global user.name 'Name'
git config --global user.email 'mail@example.org'
git config --global init.defaultBranch main
git config --global pull.ff only
```

Klonen:

```bash
mkdir -p "$HOME/repos"
git clone git@github.com:ACCOUNT/REPO.git "$HOME/repos/REPO"
```

Status:

```bash
git -C "$HOME/repos/REPO" status
git -C "$HOME/repos/REPO" fetch --prune
git -C "$HOME/repos/REPO" pull --ff-only
```

> [!tip]
> Repository unter `$HOME/repos` halten und nur benötigte Dateien in Shared Storage spiegeln. Das reduziert Dateisystemprobleme.

Git-Credentials nicht als Klartext in Shellskripten oder Remote-URLs speichern. SSH-Keys, Credential Helper oder kurzlebige Tokens verwenden.

## Python, Node.js und Compiler

Python:

```bash
pkg install python
python --version
python -m venv "$HOME/venvs/projekt"
source "$HOME/venvs/projekt/bin/activate"
python -m pip install --upgrade pip
```

Venv beenden:

```bash
deactivate
```

Node.js:

```bash
pkg install nodejs-lts
node --version
npm --version
```

Compiler:

```bash
pkg install clang make cmake ninja pkg-config
clang --version
```

Rust:

```bash
pkg install rust
rustc --version
cargo --version
```

> [!warning]
> Nicht jedes Linux-Projekt lässt sich unverändert unter Android/Bionic bauen. Häufige Hindernisse: glibc-Annahmen, systemd, hartcodierte `/usr`-Pfade, Kernel-Features, Desktop-APIs und nicht unterstützte Architekturen.

Builddiagnose:

```bash
pkg-config --list-all | head
clang -v
ldd --version 2>&1 | head
uname -m
```

## PRoot-Distributionen

```bash
pkg install proot-distro
proot-distro list
proot-distro install debian
proot-distro login debian
```

Anmelden mit Bind-Mount, nur bewusst:

```bash
proot-distro login debian --bind "$HOME/storage/shared:/mnt/shared"
```

Backup/Restore:

```bash
proot-distro backup debian
proot-distro restore debian-backup.tar.gz
```

Entfernen:

```bash
proot-distro remove debian
```

> [!note]
> PRoot emuliert Teile einer Linux-Dateisystemumgebung ohne Root. Es bietet keinen eigenen Kernel, keine VM-Sicherheitsgrenze und meist kein vollwertiges systemd. Es kann langsamer sein als native Termux-Pakete.

## Wake Locks und Android-Prozesslimits

Wake Lock:

```bash
termux-wake-lock
```

Freigeben:

```bash
termux-wake-unlock
```

Android 12 und neuer kann Phantom-/Hintergrundprozesse sowie CPU-intensive Jobs beenden. Typisches Symptom:

```text
Process completed (signal 9)
```

Zusätzliche Ursachen:

- Akkuoptimierung;
- Hersteller-Taskkiller;
- hoher RAM-Druck/OOM;
- viele Kindprozesse;
- lange CPU-Last;
- gesperrter Bildschirm oder Netzwerkwechsel;
- thermische Begrenzung.

Gegenmaßnahmen:

- Akkuoptimierung für Termux und nötige Add-ons prüfen;
- Prozesse und Parallelität begrenzen;
- Wake Lock nur während notwendiger Jobs;
- Jobs checkpoint-/resume-fähig bauen;
- Logs und Statusdateien schreiben;
- Screen/tmux gegen Terminalabbruch nutzen;
- kritische Dauerjobs auf einem Server statt Smartphone betreiben.

> [!warning]
> Screen oder tmux verhindern **nicht**, dass Android den gesamten App-Prozess beendet.

## Termux API

Termux:API besteht aus Add-on-App und Clientpaket; beide müssen zur Haupt-App passen.

```bash
pkg install termux-api
```

Beispiele:

```bash
termux-battery-status
termux-wifi-connectioninfo
termux-location
termux-clipboard-get
printf '%s' 'Text' | termux-clipboard-set
termux-notification --title 'Job' --content 'Fertig'
termux-toast 'Hallo'
termux-vibrate -d 300
termux-tts-speak 'Aufgabe abgeschlossen'
```

Datei/Teilen:

```bash
termux-storage-get ziel-datei
termux-share datei.txt
```

Timeout für fehlerhafte/hängende API-Aufrufe:

```bash
timeout 15s termux-battery-status
```

> [!important]
> Funktionsumfang und Kompatibilität hängen von Edition, App-/Paketversion und Android-Version ab. Bei hängenden API-Aufrufen zuerst Signaturen, Versionen, Berechtigungen und aktuelle bekannte Issues der offiziellen Repositories prüfen.

> [!warning]
> Standort, Mikrofon, SMS, Kontakte, Zwischenablage und Benachrichtigungen sind sensible Daten. Nur minimal notwendige Android-Berechtigungen erteilen.

## Boot, Widget und Tasker

### Termux:Boot

```bash
mkdir -p "$HOME/.termux/boot"
```

Beispiel `$HOME/.termux/boot/start-sshd`:

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -eu
sshd
```

```bash
chmod 700 "$HOME/.termux/boot/start-sshd"
```

Die Boot-App nach Installation einmal öffnen und Android-Einschränkungen prüfen.

> [!warning]
> Kein dauerhafter Wake Lock ohne Abbruchlogik. SSH-Server beim Boot nur in vertrauenswürdigen Netz-/VPN-Szenarien starten.

### Termux:Widget

```bash
mkdir -p "$HOME/.shortcuts"
mkdir -p "$HOME/.shortcuts/tasks"
```

- `.shortcuts`: interaktive Skripte;
- `.shortcuts/tasks`: Hintergrundaufgaben.

Skripte wie Programme behandeln: Eingaben validieren, feste Pfade verwenden, Rechte begrenzen und keine Secrets aus Benachrichtigungen übernehmen.

### Tasker

Externe Befehlsausführung nur bewusst freigeben. Parameter aus Tasker als untrusted behandeln:

```bash
case "${1-}" in
  start|stop|status) action=$1 ;;
  *) printf 'ungültige Aktion\n' >&2; exit 2 ;;
esac
```

## Backups und Wiederherstellung

### Nutzdaten und Konfiguration

```bash
mkdir -p "$HOME/storage/shared/Download"
tar -czf "$HOME/storage/shared/Download/termux-home-$(date +%F).tar.gz" \
  -C "$HOME" .
```

Das Archiv kann SSH-Keys, Tokens und Konfiguration enthalten. Verschlüsseln und Zugriffsrechte beachten.

### Home und Prefix

```bash
termux-wake-lock
trap 'termux-wake-unlock 2>/dev/null || true' EXIT

tar -czf "$HOME/storage/shared/Download/termux-full-$(date +%F).tar.gz" \
  -C /data/data/com.termux/files \
  home usr
```

Währenddessen keine Paketinstallation oder schreibintensiven Prozesse.

### Wiederherstellung

Erst auf kompatibler frischer Installation testen:

```bash
cd /data/data/com.termux/files
tar -xzf "$HOME/storage/shared/Download/termux-full-2026-07-17.tar.gz"
```

Danach App vollständig neu starten und prüfen:

```bash
termux-info
pkg update
command -v bash python ssh git
```

> [!danger]
> Vollrestore über inkompatible Edition, Architektur, Android-Version oder Bootstrap kann die Umgebung beschädigen. Für langfristige Portabilität Konfiguration, Paketliste, Repositories und Nutzdaten zusätzlich reproduzierbar sichern.

## Sichere Automation

Robustes Muster:

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
umask 077

LOCK="$HOME/.cache/mein-job.lock"
LOG="$HOME/.local/state/mein-job.log"
mkdir -p "$(dirname "$LOCK")" "$(dirname "$LOG")"

exec 9>"$LOCK"
flock -n 9 || exit 0

termux-wake-lock
trap 'rc=$?; termux-wake-unlock 2>/dev/null || true; printf "%s exit=%s\n" "$(date -Is)" "$rc" >> "$LOG"' EXIT

printf '%s start\n' "$(date -Is)" >> "$LOG"
# eigentliche, idempotente Arbeit
printf '%s done\n' "$(date -Is)" >> "$LOG"
```

Benötigt:

```bash
pkg install util-linux
```

Zusätzlich:

- Timeouts setzen;
- Teilschritte idempotent;
- temporäre Dateien unter `$TMPDIR`;
- atomar schreiben: erst neue Datei, dann `mv`;
- Retry mit Obergrenze und Backoff;
- kein `eval` mit externen Daten;
- Secrets aus geschützter Datei oder Secret-Tool, nicht Argumentliste;
- Status für Wiederaufnahme speichern.

## Fehlerdiagnose

### Basisdaten

```bash
termux-info
uname -a
getprop ro.build.version.release
printf 'HOME=%s PREFIX=%s\n' "$HOME" "$PREFIX"
df -h
free -h
pkg list-installed
```

### Repository nicht erreichbar

```bash
termux-change-repo
pkg update
```

DNS/Netz:

```bash
getprop | grep -i dns
ping -c 2 1.1.1.1
getent hosts packages.termux.dev
curl -I https://packages.termux.dev/
```

### Storage fehlt

```bash
termux-setup-storage
ls -la "$HOME/storage"
```

Android-Berechtigung in Systemeinstellungen prüfen.

### `CANNOT LINK EXECUTABLE`

```bash
termux-info
pkg update
pkg upgrade
ldd "$(command -v problemprogramm)"
```

Häufig: gemischte Edition/Paketquelle, teilweises Upgrade, inkompatible Bibliothek oder beschädigtes Prefix. Nicht wahllos fremde `.so`-Dateien kopieren.

### Falscher Interpreter

```text
bad interpreter: /bin/bash
```

Beheben:

```bash
sed -i '1s|^#!.*bash$|#!/usr/bin/env bash|' skript.sh
```

### Signal 9

```bash
dmesg 2>/dev/null | tail
logcat -d | grep -Ei 'kill|phantom|oom|termux' | tail -n 100
```

Logcat kann sensible Daten enthalten; vor Weitergabe redigieren.

### SSH nicht erreichbar

```bash
pgrep -a sshd
ss -ltnp | grep 8022
sshd -T | grep -E 'port|passwordauthentication|pubkeyauthentication'
ip addr
```

Dann WLAN-Isolation, Firewall/VPN, Netzwerkwechsel und Android-Hintergrundstatus prüfen.

### Termux API hängt

```bash
command -v termux-battery-status
pkg show termux-api
pm list packages 2>/dev/null | grep termux || true
timeout 10s termux-battery-status
logcat -d | grep -i termux | tail -n 100
```

Haupt-App/Add-on aus derselben Signaturfamilie und aktuelle Issue-Lage prüfen.

## Schnellreferenz

```bash
termux-info
pkg update && pkg upgrade
pkg install git openssh rsync screen python
termux-setup-storage
termux-wake-lock
termux-wake-unlock
sshd
screen -S arbeit
```

Goldene Regeln:

```text
Editionen und Signaturen nicht mischen.
Repos und ausführbare Dateien unter $HOME, nicht Shared Storage.
Android kann Prozesse trotz screen/tmux beenden.
Wake Locks immer freigeben.
Backups vor Editionswechsel und Vollupgrade.
API- und Boot-Automation mit minimalen Berechtigungen.
```

## Quellen

- [Termux App – offizielles Repository](https://github.com/termux/termux-app)
- [Termux Packages](https://github.com/termux/termux-packages)
- [Termux Package Management](https://github.com/termux/termux-packages/wiki/Package-Management)
- [Termux:API](https://github.com/termux/termux-api)
- [Termux:API package](https://github.com/termux/termux-api-package)
- [Termux:Boot](https://github.com/termux/termux-boot)
- [Termux:Widget](https://github.com/termux/termux-widget)

## Verwandte Notizen

- [[GNU-Screen-Premium-Spickzettel]]
- [[SSH-Premium-Spickzettel]]
- [[USB-Debugging-und-ADB-Premium-Spickzettel]]
- [[Git-Premium-Spickzettel]]
- [[Syncthing-Premium-Spickzettel]]
- [[Neovim-Premium-Spickzettel]]
