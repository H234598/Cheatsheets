---
title: "SSH – Cheatsheet"
aliases: ["OpenSSH Cheatsheet", "Secure Shell", "SSH Client Server"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [ssh, openssh, linux, security, network, remote-access]
source: "https://www.openssh.com/manual.html"
---

# SSH – Cheatsheet

> [!abstract] Zweck
> Ausführlicher OpenSSH-Spickzettel für Client, Server, Schlüssel, Config, Agent, Hostkeys, ProxyJump, Portweiterleitungen, Multiplexing, SFTP/SCP, Härtung, Logs und systematische Diagnose.

> [!danger] Vertrauenskette nicht überspringen
> Eine funktionierende Verschlüsselung schützt nicht vor einem falschen Server. Hostkey-Fingerprints über einen unabhängigen Kanal prüfen. `StrictHostKeyChecking=no` und globale Wildcard-Ausnahmen sind keine dauerhafte Lösung.

## Inhalt

- [[#Grundmodell]]
- [[#Client-Grundlagen]]
- [[#Schlüssel erzeugen und installieren]]
- [[#Client-Konfiguration]]
- [[#Agent und Schlüsselverwaltung]]
- [[#Hostkeys und known_hosts]]
- [[#ProxyJump und Bastion Hosts]]
- [[#Portweiterleitungen]]
- [[#SCP, SFTP und rsync]]
- [[#Multiplexing und Keepalive]]
- [[#Server konfigurieren]]
- [[#Autorisierung und Dateirechte]]
- [[#Härtung]]
- [[#Diagnose]]
- [[#Schnellreferenz]]

## Grundmodell

SSH kombiniert:

1. Serverauthentisierung über Hostkey.
2. Verschlüsselten Transport.
3. Clientauthentisierung, z. B. Public Key, Zertifikat, Passwort oder MFA/PAM.
4. Sitzungskanäle für Shell, Subsysteme und Portweiterleitungen.

Wichtige Dateien:

| Zweck | Client | Server |
|---|---|---|
| Konfiguration | `~/.ssh/config`, `/etc/ssh/ssh_config` | `/etc/ssh/sshd_config`, `sshd_config.d/*.conf` |
| Benutzerkeys | `~/.ssh/id_*` | `~/.ssh/authorized_keys` |
| bekannte Hosts | `~/.ssh/known_hosts` | Hostkeys unter `/etc/ssh/ssh_host_*` |
| Logs | Client `-v` | Journal/Auth-Log |

## Client-Grundlagen

```bash
ssh user@server.example.org
ssh -p 2222 user@server
ssh -i ~/.ssh/id_ed25519 user@server
ssh user@server 'uname -a'
```

TTY erzwingen oder verbieten:

```bash
ssh -t user@server 'sudo systemctl status nginx'
ssh -T git@github.com
```

Umgebungs-/Optionstest:

```bash
ssh -G alias | less
```

Verbose:

```bash
ssh -v user@server
ssh -vv user@server
ssh -vvv user@server
```

Escape-Sequenzen innerhalb einer Sitzung beginnen nach Zeilenanfang mit `~`:

| Sequenz | Wirkung |
|---|---|
| `~.` | Verbindung sofort trennen |
| `~?` | Hilfe |
| `~C` | Kommandozeile für Forwarding, falls erlaubt |
| `~^Z` | SSH suspendieren |

Wurde direkt vorher Text eingegeben, zuerst Enter drücken.

## Schlüssel erzeugen und installieren

Ed25519:

```bash
ssh-keygen -t ed25519 -a 64 -C 'admin@workstation'
```

RSA für Legacy-Kompatibilität, ausreichend groß:

```bash
ssh-keygen -t rsa -b 3072 -o -a 64 -C 'legacy-purpose'
```

Fingerprint:

```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub
ssh-keygen -E sha256 -lf hostkey.pub
```

Public Key kopieren:

```bash
ssh-copy-id user@server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server
```

Manuell:

```bash
cat ~/.ssh/id_ed25519.pub | \
  ssh user@server 'umask 077; mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys'
```

> [!warning]
> Private Keys niemals kopieren, mailen oder auf Zielservern verteilen. Nur `.pub` in `authorized_keys` eintragen.

Passphrase ändern:

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
```

Public Key aus Private Key rekonstruieren:

```bash
ssh-keygen -y -f ~/.ssh/id_ed25519 > ~/.ssh/id_ed25519.pub
```

## Client-Konfiguration

```sshconfig
Host web-prod
    HostName web01.example.org
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_web_prod
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

Nutzung:

```bash
ssh web-prod
scp datei web-prod:/tmp/
rsync -a ./release/ web-prod:/srv/app/
```

Wildcard:

```sshconfig
Host *.corp.example.org
    User admin
    IdentityFile ~/.ssh/id_corp
    IdentitiesOnly yes

Host *
    HashKnownHosts yes
    AddKeysToAgent yes
```

Reihenfolge: Für jede Option zählt im Regelfall der **erste gefundene Wert**. Spezifische Hosts daher vor `Host *` setzen.

Includes:

```sshconfig
Include ~/.ssh/config.d/*.conf
```

Effektive Konfiguration:

```bash
ssh -G web-prod | sort
```

## Agent und Schlüsselverwaltung

Agent starten, falls Desktop/System nicht bereits einen bereitstellt:

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

Anzeigen:

```bash
ssh-add -l
ssh-add -L
```

Zeitlich begrenzt:

```bash
ssh-add -t 1h ~/.ssh/id_admin
```

Entfernen:

```bash
ssh-add -d ~/.ssh/id_ed25519
ssh-add -D
```

> [!danger] Agent Forwarding
> `ssh -A` erlaubt dem entfernten Host, während der Sitzung den lokalen Agenten anzusprechen. Ein kompromittierter Zwischenhost kann Signaturen anfordern. Bevorzugt `ProxyJump`; Agent Forwarding nur gezielt für vertrauenswürdige Systeme.

Hostbezogen:

```sshconfig
Host trusted-build
    ForwardAgent yes
```

## Hostkeys und known_hosts

Fingerprint beim Server lokal anzeigen:

```bash
sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Clienteintrag suchen:

```bash
ssh-keygen -F server.example.org
```

Veralteten Eintrag entfernen:

```bash
ssh-keygen -R server.example.org
ssh-keygen -R '[server.example.org]:2222'
```

Key vorab scannen:

```bash
ssh-keyscan -t ed25519 server.example.org
```

> [!warning]
> `ssh-keyscan` verschafft nur den präsentierten Key; es authentisiert ihn nicht. Fingerprint über Inventar, Konsole, DNSSEC/SSHFP oder einen anderen vertrauenswürdigen Kanal bestätigen.

Hashed known_hosts:

```bash
ssh-keygen -H -f ~/.ssh/known_hosts
```

Hostkey-Rotation kann mit `UpdateHostKeys yes` erleichtert werden, setzt aber einen bereits vertrauenswürdigen Kanal voraus.

## ProxyJump und Bastion Hosts

Direkt:

```bash
ssh -J bastion.example.org user@intern.example.org
```

Mit Benutzern/Ports:

```bash
ssh -J jumpuser@bastion.example.org:2222 app@10.20.30.40
```

Config:

```sshconfig
Host bastion
    HostName bastion.example.org
    User jumpuser
    IdentityFile ~/.ssh/id_bastion

Host app-intern
    HostName 10.20.30.40
    User app
    IdentityFile ~/.ssh/id_app
    ProxyJump bastion
```

Mehrere Sprünge:

```sshconfig
ProxyJump edge,core
```

`ProxyCommand` ist für Spezialfälle weiterhin möglich:

```sshconfig
ProxyCommand ssh -W %h:%p bastion
```

## Portweiterleitungen

### Lokal: Zugriff auf Remote-Dienst

```bash
ssh -L 127.0.0.1:15432:db.internal:5432 bastion
```

Dann lokal `127.0.0.1:15432` verwenden.

### Remote: lokalen Dienst am Server bereitstellen

```bash
ssh -R 127.0.0.1:18080:127.0.0.1:8080 server
```

Ob externe Clients zugreifen dürfen, hängt von Bind-Adresse, `GatewayPorts` und Firewall ab.

### Dynamisch: SOCKS-Proxy

```bash
ssh -D 127.0.0.1:1080 bastion
```

Nur Tunnel, keine Shell:

```bash
ssh -N -T -L 15432:db:5432 bastion
```

Im Hintergrund:

```bash
ssh -fN -L 15432:db:5432 bastion
```

Fehler statt stiller Forwarding-Probleme:

```bash
ssh -o ExitOnForwardFailure=yes -N -L 15432:db:5432 bastion
```

> [!warning]
> Bind-Adresse `0.0.0.0` oder `*` kann Tunnel im Netz exponieren. Standardmäßig an Loopback binden und Firewall/Authentisierung des Zielprotokolls beachten.

## SCP, SFTP und rsync

SCP:

```bash
scp datei user@server:/tmp/
scp -r verzeichnis user@server:/tmp/
scp -P 2222 datei user@server:/tmp/
```

Moderne OpenSSH-Versionen verwenden für `scp` standardmäßig SFTP-Semantik; Legacy-SCP lässt sich je Version mit `-O` erzwingen, sollte aber nur bei Bedarf genutzt werden.

SFTP interaktiv:

```bash
sftp user@server
```

Wichtige SFTP-Kommandos:

```text
pwd / lpwd
ls / lls
cd / lcd
get / put
reget / reput
mkdir / lmkdir
progress
```

Batch:

```bash
sftp -b batch.txt user@server
```

rsync:

```bash
rsync -aHAX --info=progress2 ./daten/ server:/srv/daten/
```

## Multiplexing und Keepalive

Config:

```sshconfig
Host *.corp.example.org
    ControlMaster auto
    ControlPath ~/.ssh/cm-%C
    ControlPersist 10m
```

Verbindung prüfen/stoppen:

```bash
ssh -O check host
ssh -O exit host
```

Keepalive:

```sshconfig
ServerAliveInterval 30
ServerAliveCountMax 3
TCPKeepAlive yes
```

- `ServerAlive*` läuft im verschlüsselten Protokoll und erkennt hängende Sessions.
- `TCPKeepAlive` ist Betriebssystem-TCP und kann spoofbar/zu träge sein.

## Server konfigurieren

Syntax prüfen:

```bash
sudo sshd -t
```

Effektive Konfiguration:

```bash
sudo sshd -T | less
sudo sshd -T -C user=alice,host=client,addr=192.0.2.10
```

Drop-in:

```ini
# /etc/ssh/sshd_config.d/20-hardening.conf
PermitRootLogin prohibit-password
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
AllowGroups ssh-users
X11Forwarding no
AllowTcpForwarding local
```

Danach:

```bash
sudo sshd -t && sudo systemctl reload sshd
```

Auf Debian/Ubuntu heißt der Dienst häufig `ssh`, auf Fedora/RHEL `sshd`.

> [!danger]
> Eine bestehende administrative Sitzung offen lassen und eine **zweite** Sitzung testen, bevor Passwortauthentisierung, Rootzugriff oder Allow-/Deny-Regeln verschärft werden.

Ports prüfen:

```bash
sudo ss -ltnp | grep sshd
sudo firewall-cmd --list-services
sudo nft list ruleset
```

## Autorisierung und Dateirechte

Typische Rechte:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

Eigentümer:

```bash
chown -R "$USER:$USER" ~/.ssh
```

SELinux:

```bash
restorecon -RFv ~/.ssh
ls -laZ ~/.ssh
```

Optionen pro Key in `authorized_keys`:

```text
from="192.0.2.0/24",restrict,command="/usr/local/bin/backup-only" ssh-ed25519 AAAA...
```

Nützliche Einschränkungen je OpenSSH-Version:

- `restrict`
- `no-agent-forwarding`
- `no-port-forwarding`
- `no-pty`
- `no-X11-forwarding`
- `permitopen="host:port"`
- `command="..."`
- `from="..."`

## Härtung

- Ed25519/ECDSA/RSA-SHA2 statt veralteter Algorithmen.
- Passwortlogin nach getesteter Key-/MFA-Lösung deaktivieren.
- Rootlogin begrenzen oder sperren.
- Benutzer/Gruppen explizit zulassen.
- Nicht benötigte Forwardings und X11 deaktivieren.
- Fail2ban/Rate Limits als Ergänzung, nicht Ersatz für starke Authentisierung.
- Regelmäßig Hostkeys, Benutzerkeys und `authorized_keys` inventarisieren.
- SSH-Zertifikate/CA für größere Flotten erwägen.
- Konfiguration mit `sshd -t` und `sshd -T` prüfen.
- Logs zentral erfassen und Zeit synchronisieren.

Keine pauschalen Cipher-/MAC-Listen aus alten Blogposts übernehmen. OpenSSH-Defaults entwickeln sich; nur aus Compliance-/Kompatibilitätsgrund bewusst überschreiben.

Algorithmen anzeigen:

```bash
ssh -Q key
ssh -Q kex
ssh -Q cipher
ssh -Q mac
```

## Diagnose

Clientseite:

```bash
ssh -vvv -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 user@server
ssh -G server | less
nc -vz server 22
```

Serverseite:

```bash
sudo sshd -t
sudo sshd -T | less
sudo journalctl -u sshd -b --since '-10 min'
sudo ss -ltnp | grep ':22'
sudo firewall-cmd --list-all
sudo ausearch -m AVC -ts recent
```

Typische Fehler:

| Meldung | Häufige Ursache |
|---|---|
| `Connection timed out` | Routing/Firewall/Port falsch |
| `Connection refused` | Dienst lauscht nicht oder falscher Port |
| `No route to host` | Route oder ICMP/Firewall-Rückmeldung |
| `Host key verification failed` | geänderter/falscher Hostkey |
| `Permission denied (publickey)` | Key nicht angeboten/akzeptiert, Rechte, Benutzer, Policy |
| `Too many authentication failures` | Agent bietet zu viele Keys; `IdentitiesOnly yes` |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | legitime Neuinstallation oder MITM – erst verifizieren |
| sofortiger Disconnect | Shell, Account, PAM, ForceCommand, MaxStartups |
| Tunnel offen, Dienst nicht erreichbar | Zieladresse aus Sicht des SSH-Servers falsch |

Prüfreihenfolge:

1. DNS/IP und Port.
2. TCP-Erreichbarkeit.
3. Hostkey-Fingerprint.
4. Effektive Clientconfig mit `ssh -G`.
5. Verbose Authentisierung.
6. `authorized_keys`, Rechte, Eigentümer, SELinux.
7. Effektive Serverconfig und Match-Blöcke.
8. Serverlogs/PAM/Firewall.
9. Zielressource bei Forwardings.

## Schnellreferenz

```bash
ssh host
ssh -J bastion intern
ssh -L 8443:web:443 bastion
ssh -D 1080 bastion
ssh-keygen -t ed25519 -a 64
ssh-copy-id host
ssh-add -l
ssh-keygen -F host
ssh-keygen -R host
ssh -G host
ssh -vvv host
sudo sshd -t
sudo sshd -T
```

## Quellen
- [OpenSSH Manual Pages](https://www.openssh.com/manual.html)
- [ssh(1)](https://man.openbsd.org/ssh)
- [sshd_config(5)](https://man.openbsd.org/sshd_config)

## Verwandte Notizen
- [[rsync – Cheatsheet]]
- [[Linux-Netzwerk – Cheatsheet]]
- [[firewalld – Cheatsheet]]
- [[Haven Android SSH-Client – Cheatsheet]]
