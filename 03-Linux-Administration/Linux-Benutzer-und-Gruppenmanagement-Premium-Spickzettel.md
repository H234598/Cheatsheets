---
title: "Linux Benutzer- und Gruppenmanagement – Premium-Spickzettel"
aliases: ["useradd usermod", "Linux User Group Management", "passwd shadow groups", "Linux-Benutzer- und Gruppenmanagement – Premium-Spickzettel"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, users, groups, permissions, sudo, nss, pam]
source: "https://man7.org/linux/man-pages/man8/useradd.8.html"
---

# Linux Benutzer- und Gruppenmanagement – Premium-Spickzettel

> [!abstract] Zweck
> Ausführliche Referenz für lokale Linux-Benutzer und Gruppen: Dateien/NSS, useradd/usermod, Passwörter, Ablauf, Gruppen, sudo, Systemkonten, Login-Shells, UID/GID-Migration und Diagnose.

> [!important]
> Identität, Authentisierung und Autorisierung sind getrennt: NSS liefert „wer existiert“, PAM prüft Anmeldung, Gruppen/sudo/ACL/SELinux bestimmen Rechte. Bei LDAP/AD/SSSD nicht nur lokale `/etc/passwd` betrachten.

## Inhalt

- [[#Grunddateien und NSS]]
- [[#Benutzer anlegen]]
- [[#Benutzer ändern und löschen]]
- [[#Passwörter, Sperren und Ablauf]]
- [[#Gruppen]]
- [[#Systemkonten]]
- [[#sudo]]
- [[#Login, Shell und Home]]
- [[#UID-GID-Migration]]
- [[#Zentrale Identitäten und SSSD]]
- [[#Diagnose]]

## Grunddateien und NSS

| Datei | Inhalt |
|---|---|
| `/etc/passwd` | Benutzername, UID, primäre GID, GECOS, Home, Shell |
| `/etc/shadow` | Passwort-Hash und Ablaufdaten, root-lesbar |
| `/etc/group` | Gruppen und Mitglieder |
| `/etc/gshadow` | geschützte Gruppeninformationen |
| `/etc/nsswitch.conf` | Quellen/Reihenfolge für Benutzer, Gruppen, Hosts usw. |
| `/etc/login.defs` | Defaults/Bereiche für Accounttools |
| `/etc/default/useradd` | useradd-Defaults je Distribution |
| `/etc/skel` | Vorlage für neue Homes |

Nicht direkt mit normalem Editor ändern; verwenden:

```bash
sudo vipw
sudo vigr
sudo pwck
sudo grpck
```

Abfrage immer über NSS:

```bash
getent passwd alice
getent group admins
id alice
```

So werden auch LDAP/SSSD/NIS-Quellen berücksichtigt.

## Benutzer anlegen

Distributionunabhängig mit expliziten Optionen:

```bash
sudo useradd \
  --create-home \
  --shell /bin/bash \
  --comment 'Alice Admin' \
  alice
sudo passwd alice
```

Primäre Gruppe explizit:

```bash
sudo groupadd appteam
sudo useradd -m -g appteam -s /bin/bash alice
```

Zusatzgruppen:

```bash
sudo usermod -aG wheel,docker alice
```

> [!danger]
> Bei `usermod -G` ohne `-a` werden bestehende Zusatzgruppen ersetzt. Vorher `id alice`, danach erneut prüfen.

UID/GID explizit nur bei zentralem Plan:

```bash
sudo useradd -m -u 1500 -g 1500 alice
```

Dubletten/Reservierungsbereiche vermeiden.

Defaults:

```bash
useradd -D
```

## Benutzer ändern und löschen

```bash
sudo usermod -c 'Alice Example' alice
sudo usermod -s /bin/zsh alice
sudo usermod -d /home/alice-new -m alice
sudo usermod -l alice2 alice
```

Nach Loginnamewechsel:

- Homepfad
- Mailspool
- sudoers
- Cronjobs
- systemd User Units
- SSH keys/config
- Anwendungsdaten/DB-Referenzen
- zentrale Identität

prüfen.

Sperren:

```bash
sudo usermod -L alice
sudo usermod -U alice
```

Löschen:

```bash
sudo userdel alice
sudo userdel -r alice
```

> [!warning]
> `-r` entfernt Home und Mailspool, nicht automatisch alle Dateien/Jobs/Prozesse. Vor Offboarding inventarisieren und archivieren.

Dateien nach UID:

```bash
sudo find / -xdev -uid 1500 -ls 2>/dev/null
```

Laufende Prozesse:

```bash
pgrep -a -u alice
loginctl user-status alice
```

## Passwörter, Sperren und Ablauf

Status:

```bash
sudo passwd -S alice
sudo chage -l alice
```

Passwort ändern:

```bash
sudo passwd alice
```

Ablauf erzwingen:

```bash
sudo chage -d 0 alice
```

Parameter:

```bash
sudo chage -M 90 -m 1 -W 14 alice
sudo chage -E 2026-12-31 alice
```

Account Ablauf entfernen:

```bash
sudo chage -E -1 alice
```

Sperrmethoden unterscheiden:

- Passwort sperren verhindert Passwortauthentisierung, aber nicht zwingend SSH-Key, Token oder bestehende Sitzung.
- Accountablauf/PAM/SSSD kann vollständiger wirken.
- Shell `/sbin/nologin` verhindert interaktive Shell, nicht automatisch Dienstnutzung.

Offboarding:

```text
[ ] zentrale Identität deaktivieren
[ ] Tokens/SSH-Keys/Zertifikate widerrufen
[ ] aktive Sessions/Prozesse beenden
[ ] sudo/Gruppe/Anwendungsrollen entfernen
[ ] Cron/Timer/Servicekonten prüfen
[ ] Datenübergabe/Retention
[ ] Audit und Eigentümerwechsel
```

## Gruppen

```bash
sudo groupadd developers
sudo groupmod -n devteam developers
sudo groupdel devteam
```

Mitglied hinzufügen/entfernen:

```bash
sudo gpasswd -a alice developers
sudo gpasswd -d alice developers
```

Mitglieder:

```bash
getent group developers
id alice
groups alice
```

Neue Gruppenmitgliedschaft wirkt in neuen Login-Sitzungen. Temporär:

```bash
newgrp developers
```

`newgrp` startet Subshell mit neuer primärer Gruppe; Verhalten bewusst nutzen.

### Shared Directory

```bash
sudo install -d -m 2770 -o root -g developers /srv/project
```

Setgid-Bit `2` sorgt dafür, dass neue Objekte die Verzeichnisgruppe erben.

Zusätzlich Default ACL:

```bash
sudo setfacl -m g:developers:rwx /srv/project
sudo setfacl -m d:g:developers:rwx /srv/project
sudo setfacl -m d:m:rwx /srv/project
```

Details in [[POSIX-ACL-Premium-Spickzettel]].

## Systemkonten

```bash
sudo useradd --system \
  --home-dir /var/lib/myapp \
  --create-home \
  --shell /usr/sbin/nologin \
  myapp
```

Systemkonto:

- keine interaktive Anmeldung
- eigenes minimal berechtigtes Home/StateDirectory
- keine gemeinsame UID zwischen Diensten ohne Grund
- keine Passwortauthentisierung
- systemd `DynamicUser=` erwägen

Nicht jede Service-Identität braucht `/etc/passwd`-persistenten Benutzer.

## sudo

Immer editieren:

```bash
sudo visudo
sudo visudo -f /etc/sudoers.d/myapp
sudo visudo -c
```

Beispiel:

```sudoers
%ops ALL=(root) /usr/bin/systemctl status myapp.service, \
                /usr/bin/systemctl restart myapp.service
```

> [!warning]
> Argumentmatching und aufgerufene Programme können Escape-/Editor-/Dateischreibmöglichkeiten besitzen. Ein scheinbar enger Befehl kann Root-Shell ermöglichen. `sudoers(5)` und Programmverhalten prüfen.

NOPASSWD nur nach Risikoabwägung:

```sudoers
%deploy ALL=(deploy) NOPASSWD: /usr/local/sbin/deploy-approved
```

Besser Wrapper mit festen Argumenten, Logging und Validierung.

Rechte ansehen:

```bash
sudo -l
sudo -l -U alice
```

Cache löschen:

```bash
sudo -k
```

## Login, Shell und Home

Gültige Shells:

```bash
cat /etc/shells
chsh -s /bin/bash
```

Home-Rechte:

```bash
stat /home/alice
namei -l /home/alice/.ssh/authorized_keys
```

SSH:

```bash
chmod 700 /home/alice/.ssh
chmod 600 /home/alice/.ssh/authorized_keys
chown -R alice:alice /home/alice/.ssh
restorecon -Rv /home/alice/.ssh 2>/dev/null || true
```

Umask:

```bash
umask
```

Typisch `0022` oder kollaborativ `0002`. PAM/systemd/Shell/Anwendung können unterschiedliche Umask setzen.

## UID-GID-Migration

UID ändern:

```bash
old_uid=$(id -u alice)
sudo usermod -u 2500 alice
```

Primärgruppe:

```bash
old_gid=$(id -g alice)
sudo groupmod -g 2500 alice
```

Dateien korrigieren, pro Dateisystem/Mount geplant:

```bash
sudo find /home/alice -xdev -uid "$old_uid" -exec chown -h 2500 {} +
sudo find /home/alice -xdev -gid "$old_gid" -exec chgrp -h 2500 {} +
```

> [!danger]
> Nicht unbeschränkt über `/` laufen: Netzwerkfilesystems, Containerlayers, Backups und fremde Besitzer können betroffen sein. Prozesse stoppen, NFS-ID-Mapping, ACLs, xattrs und Anwendungsdatenbanken prüfen.

## Zentrale Identitäten und SSSD

```bash
getent passwd alice
id alice
systemctl status sssd
sssctl domain-list
sssctl user-checks alice
```

Kerberos:

```bash
kinit alice
klist
```

Diagnosekomponenten:

- DNS A/PTR/SRV
- Zeit/NTP
- CA/TLS
- Realm/Domain
- SSSD-Konfiguration und Rechte
- LDAP/Kerberos-Netzwerk
- Cache und Offlinezustand
- HBAC/Sudo/Access Provider

SSSD-Cache nicht als erste Maßnahme löschen. Logs und Quellverfügbarkeit sichern.

## Diagnose

### Benutzer existiert, Login scheitert

```bash
getent passwd alice
id alice
sudo passwd -S alice
sudo chage -l alice
getent shadow alice 2>/dev/null
```

Dann PAM/SSH/Loginlog:

```bash
journalctl -u sshd --since '-30 min'
journalctl _COMM=sshd --since '-30 min'
tail -n 100 /var/log/secure 2>/dev/null
```

Shell, Home, Lock, Ablauf, Access.conf, SSSD und SELinux prüfen.

### Gruppenrecht greift nicht

```bash
id alice
getent group developers
stat -c '%A %U %G %n' /srv/project
getfacl /srv/project
```

Neue Sitzung? ACL-Maske? Setgid? Parent-X-Recht? SELinux?

### „Permission denied“ trotz chmod

```bash
namei -l /pfad/datei
getfacl /pfad/datei
ls -lZ /pfad/datei
findmnt -T /pfad/datei
```

Parentverzeichnisse, ACL, SELinux, Read-only-Mount, NFS root squash und Capabilities.

### Universeller Prüfblock

```bash
getent passwd alice
id alice
sudo passwd -S alice
sudo chage -l alice
getent group wheel
sudo -l -U alice
```

## Quellen
- [useradd Manual](https://man7.org/linux/man-pages/man8/useradd.8.html)
- [usermod Manual](https://man7.org/linux/man-pages/man8/usermod.8.html)
- [passwd Manual](https://man7.org/linux/man-pages/man5/passwd.5.html)
- [sudoers Manual](https://www.sudo.ws/docs/man/sudoers.man/)

## Verwandte Notizen
- [[POSIX-ACL-Premium-Spickzettel]]
- [[SSH-Premium-Spickzettel]]
- [[SELinux-Premium-Spickzettel]]
- [[Fedora-RHEL-Premium-Spickzettel]]
