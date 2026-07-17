---
title: "Fedora und RHEL – Eigenheiten und Premium-Spickzettel"
aliases: ["Fedora RHEL Cheatsheet", "Red Hat Linux Eigenheiten", "Fedora Administration", "Fedora-RHEL – Premium-Spickzettel"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [fedora, rhel, linux, systemd, selinux, dnf, administration]
source: "https://docs.fedoraproject.org/"
---

# Fedora und RHEL – Eigenheiten und Premium-Spickzettel

> [!abstract] Zweck
> Ausführliche Orientierung für Fedora und Red Hat Enterprise Linux: Releasemodell, RPM/DNF, systemd, SELinux, firewalld, NetworkManager, Dateipfade, Kernel/Boot, Subscription, Updates, Logs und Diagnose.

> [!abstract] Charakter
> Fedora ist die schnelllebigere Community-Distribution mit frühem Zugang zu neuen Linux-Technologien. RHEL ist auf lange, planbare Enterprise-Lebenszyklen, Zertifizierung und Support ausgerichtet. Beide teilen viele Werkzeuge und Konventionen, unterscheiden sich aber bei Releasegeschwindigkeit, Repositories, Support, Paketständen und Upgradewegen.

## Inhalt

- [[#System identifizieren]]
- [[#Die wichtigsten Eigenheiten]]
- [[#Paketmodell und Repositories]]
- [[#Systemd und Journal]]
- [[#SELinux]]
- [[#Firewalld und nftables]]
- [[#NetworkManager]]
- [[#Dateisystem- und Konfigurationspfade]]
- [[#Benutzer, sudo und Authentisierung]]
- [[#Kernel, Boot und dracut]]
- [[#RHEL-Subscription und zusätzliche Repositories]]
- [[#Updates und Releasewechsel]]
- [[#Diagnose-Reihenfolge]]

Unterseiten:

- [[Fedora-RHEL-Shortcuts-und-Kommandos]]
- [[Systemd-Premium-Spickzettel]]
- [[SELinux-Premium-Spickzettel]]
- [[firewalld-Premium-Spickzettel]]
- [[dnf-Premium-Spickzettel]]
- [[RPM-Premium-Spickzettel]]

## System identifizieren

```bash
cat /etc/os-release
hostnamectl
uname -r
uname -m
rpm -E '%{rhel}' 2>/dev/null || true
rpm -E '%{fedora}' 2>/dev/null || true
```

Paket- und Plattformdetails:

```bash
rpm --eval '%{_arch} %{_libdir} %{_sysconfdir}'
dnf repolist
systemctl --version
getenforce
firewall-cmd --state
nmcli general status
```

> [!tip]
> Bei Supportfällen immer Distribution, genaue Version, Architektur, Kernel, Paketversion und Repositoryherkunft nennen. „RHEL-artig“ reicht nicht, da Fedora, RHEL, CentOS Stream und kompatible Derivate unterschiedliche Stände haben.

## Die wichtigsten Eigenheiten

| Bereich | Fedora/RHEL-typisch |
|---|---|
| Pakete | RPM-Datenbank; Transaktionen über DNF |
| Dienste | systemd-Units und `journalctl` |
| MAC-Sicherheit | SELinux standardmäßig relevant, häufig enforcing |
| Firewall | firewalld als dynamische Verwaltung, nftables im Unterbau |
| Netzwerk | NetworkManager und `nmcli` |
| Boot | GRUB 2, BLS-Konfigurationen, dracut-Initramfs |
| Bibliothekspfade | `/usr/lib64` auf x86_64 häufig wichtig |
| Adminrechte | `sudo`; Rootkonto je Installation unterschiedlich behandelt |
| Logs | Journal plus anwendungsspezifische Dateien unter `/var/log` |
| Enterprise | Subscription/Content Access, zertifizierte Repositories, Errata |

### Konfiguration nicht gegen Plattformdefaults bekämpfen

- SELinux-Kontext korrigieren statt Schutz dauerhaft deaktivieren.
- firewalld-Zone/Service nutzen statt unkoordinierten nftables-Regelsatz parallel.
- NetworkManager-Verbindungen mit `nmcli` oder Keyfiles verwalten statt fremde Legacy-Dateien vorauszusetzen.
- systemd-Overrides statt Vendor-Unit in `/usr/lib/systemd/system` direkt ändern.
- Pakete über DNF/RPM verwalten statt Dateien manuell nach `/usr` zu kopieren.

## Paketmodell und Repositories

Schichten:

```text
DNF                         Transaktionen, Repos, Abhängigkeiten
└── libdnf / Solver
    └── RPM                 Paketformat, Datenbank, Scripts, Signaturen
```

Grundbefehle:

```bash
sudo dnf install paket
sudo dnf remove paket
sudo dnf upgrade --refresh
dnf info paket
dnf repoquery paket
dnf provides '*/dateiname'
rpm -q paket
rpm -ql paket
rpm -qf /pfad/datei
```

Repositorys:

```bash
dnf repolist --all
dnf repoinfo <repoid>
dnf config-manager --set-enabled <repoid>
```

> [!warning]
> Repositories verschiedener Distributionen oder Hauptversionen nicht mischen. Drittanbieter-Repo vor Aktivierung auf Signierschlüssel, Releasepfad, Wartung und Konflikte prüfen.

### Paketgruppen und Development Tools

```bash
dnf group list
dnf group info 'Development Tools'
sudo dnf group install 'Development Tools'
```

## Systemd und Journal

Dienste:

```bash
systemctl status dienst
systemctl is-active dienst
systemctl is-enabled dienst
sudo systemctl enable --now dienst
sudo systemctl restart dienst
```

Logs:

```bash
journalctl -u dienst -b
journalctl -u dienst -f
journalctl -p warning..alert -b
journalctl --since '1 hour ago'
```

Vendor-Unit anzeigen:

```bash
systemctl cat dienst
systemctl show dienst
```

Override:

```bash
sudo systemctl edit dienst
sudo systemctl daemon-reload
sudo systemctl restart dienst
```

Details in [[Systemd-Premium-Spickzettel]].

## SELinux

Status:

```bash
getenforce
sestatus
ls -Z /pfad
ps -eZ | head
```

Fehler suchen:

```bash
sudo ausearch -m AVC,USER_AVC -ts recent
sudo journalctl -t setroubleshoot --since '1 hour ago'
```

Kontext wiederherstellen:

```bash
sudo restorecon -Rv /var/www/meine-app
```

Dauerhafte eigene Pfadzuordnung:

```bash
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/web(/.*)?'
sudo restorecon -Rv /srv/web
```

> [!danger]
> `setenforce 0` ist höchstens ein kurzer Diagnosetest in kontrollierter Umgebung, keine Behebung. Ursache anhand AVC, Pfadkontext, Boolean, Porttyp oder Policy lösen.

Details in [[SELinux-Premium-Spickzettel]].

## Firewalld und nftables

```bash
firewall-cmd --state
firewall-cmd --get-active-zones
firewall-cmd --zone=public --list-all
sudo firewall-cmd --zone=public --add-service=https
sudo firewall-cmd --runtime-to-permanent
```

Oder permanent zuerst:

```bash
sudo firewall-cmd --permanent --zone=public --add-service=https
sudo firewall-cmd --reload
```

> [!warning]
> Runtime- und Permanent-Konfiguration sind getrennt. Vor `--reload` prüfen, ob eine nur zur Laufzeit vorgenommene Notfallregel verloren gehen würde.

Unterbau:

```bash
sudo nft list ruleset
```

Nicht parallel unkoordiniert `nft`-Regeln und firewalld verwalten. Details in [[firewalld-Premium-Spickzettel]].

## NetworkManager

Status:

```bash
nmcli general status
nmcli device status
nmcli connection show
ip -brief address
ip route
resolvectl status
```

Verbindung aktivieren:

```bash
sudo nmcli connection up 'Wired connection 1'
```

Statische IPv4-Adresse:

```bash
sudo nmcli connection modify 'System eth0' \
  ipv4.method manual \
  ipv4.addresses 192.0.2.10/24 \
  ipv4.gateway 192.0.2.1 \
  ipv4.dns '192.0.2.53 192.0.2.54'
sudo nmcli connection up 'System eth0'
```

DHCP:

```bash
sudo nmcli connection modify 'System eth0' ipv4.method auto
sudo nmcli connection up 'System eth0'
```

> [!note]
> Verbindungsname und Gerätename sind nicht dasselbe. Mit `nmcli -f NAME,UUID,TYPE,DEVICE connection show` eindeutig prüfen.

Ausführlicher in [[Netzwerk-Konfiguration-Linux-Windows-BSD]].

## Dateisystem- und Konfigurationspfade

| Pfad | Zweck |
|---|---|
| `/etc` | lokale Systemkonfiguration |
| `/usr/lib/systemd/system` | Vendor-Units, nicht direkt bearbeiten |
| `/etc/systemd/system` | lokale Units und Overrides |
| `/usr/lib/sysctl.d` | Vendor-sysctl |
| `/etc/sysctl.d` | lokale sysctl-Konfiguration |
| `/usr/lib/tmpfiles.d` | Vendor-tmpfiles |
| `/etc/tmpfiles.d` | lokale Overrides |
| `/var/lib` | persistenter Dienstzustand |
| `/var/log` | klassische Logdateien |
| `/run` | flüchtiger Laufzeitzustand |
| `/etc/NetworkManager/system-connections` | Connection Profiles/Keyfiles |
| `/etc/selinux` | SELinux-Konfiguration |
| `/etc/firewalld` | dauerhafte firewalld-Konfiguration |

### Drop-in-Priorität

Viele Komponenten nutzen `/usr/lib/...` für Vendor und `/etc/...` für lokale Overrides. Direkte Vendor-Dateiänderungen werden bei Updates überschrieben.

Beispiele:

```bash
systemd-delta
sysctl --system
systemd-tmpfiles --cat-config
```

## Benutzer, sudo und Authentisierung

```bash
id benutzer
getent passwd benutzer
getent group wheel
sudo usermod -aG wheel benutzer
sudo visudo
```

Sudo-Dateien:

```text
/etc/sudoers
/etc/sudoers.d/
```

Syntax prüfen:

```bash
sudo visudo -c
```

RHEL/Fedora integrieren häufig SSSD für LDAP/AD/IdM:

```bash
systemctl status sssd
sssctl domain-list
sssctl user-checks benutzer
getent passwd benutzer
id benutzer
```

Cache nicht blind löschen; erst Identitätsquelle, DNS, Zeit, Kerberos und Logs prüfen.

## Kernel, Boot und dracut

### Kernel

```bash
uname -r
rpm -q kernel-core
sudo grubby --default-kernel
sudo grubby --info=ALL
```

Kernelkommandozeile:

```bash
cat /proc/cmdline
```

### Initramfs

```bash
lsinitrd | less
sudo dracut --force
```

Für bestimmten Kernel:

```bash
sudo dracut --force /boot/initramfs-$(uname -r).img $(uname -r)
```

> [!danger]
> Initramfs/Bootloaderänderungen können das System unbootbar machen. Konsole, vorherigen Kernel und Rettungsweg sicherstellen.

### Bootdiagnose

```bash
systemd-analyze
systemd-analyze blame
systemd-analyze critical-chain
journalctl -b -1 -p warning..alert
```

## RHEL-Subscription und zusätzliche Repositories

RHEL-Systeme können über Subscription Management/Content Access verwaltet werden:

```bash
sudo subscription-manager status
sudo subscription-manager identity
sudo subscription-manager repos --list-enabled
```

Registrierung und Attach-Verhalten hängen von Organisation und aktuellem Red-Hat-Modell ab. Keine persönlichen Zugangsdaten in Skripten; Activation Keys und Organisationsprozess verwenden.

### EPEL

EPEL bietet zusätzliche Pakete für Enterprise-Linux. Vor Aktivierung:

- passende Hauptversion
- offizieller Installationsweg
- Supportgrenze zu RHEL
- Konflikte/Abhängigkeiten
- Patch- und Ausfallprozess

prüfen.

## Updates und Releasewechsel

### Normales Update

```bash
sudo dnf upgrade --refresh
sudo dnf needs-restarting
sudo dnf needs-restarting -r
```

`needs-restarting` kann Zusatzpaket/Plugin benötigen.

Transaktionen:

```bash
dnf history
dnf history info last
```

### Fedora Release Upgrade

Fedora verwendet einen dokumentierten DNF-System-Upgrade-Prozess. Vorher:

```text
[ ] vollständiges Backup
[ ] Drittanbieter-Repos prüfen/deaktivieren
[ ] freien Platz, besonders /boot
[ ] aktuelle Updates und Reboot
[ ] Paketkonflikte/Retired Packages
[ ] funktionierende Konsole/Recovery
```

Befehle und Zielrelease stets aus der aktuellen Fedora-Dokumentation übernehmen.

### RHEL Major Upgrade

Nicht als normales `dnf upgrade` behandeln. Unterstützten Upgradepfad, Leapp-/Migrationsdokumentation, Applikationsfreigaben, Drittanbieteragenten und Rollback planen.

## Diagnose-Reihenfolge

### Systemischer Schnellcheck

```bash
cat /etc/os-release
uname -r
uptime
systemctl --failed
journalctl -p warning..alert -b
getenforce
firewall-cmd --state
nmcli general status
dnf repolist
findmnt -D
free -h
df -hT
```

### Dienst startet nicht

```bash
systemctl status dienst --no-pager -l
journalctl -u dienst -b --no-pager -n 200
systemctl cat dienst
systemctl show dienst -p ExecStart,User,Group,Environment,FragmentPath,DropInPaths
```

Dann:

1. exakten Exitcode und ersten Fehler lesen
2. Konfiguration mit Diensttool validieren
3. Datei-/Verzeichnisrechte und SELinux-Kontext
4. Portbelegung und Firewall
5. Dependencies/Mounts/Netzwerk/Secrets
6. letzte Paket- oder Configänderung
7. gezielt korrigieren, nicht alle Schutzmechanismen abschalten

### Paketproblem

```bash
dnf check
dnf repoquery --duplicates
dnf repoquery --unsatisfied
rpm -Va
```

`rpm -Va` erzeugt viele legitime Konfigurationsabweichungen; Ausgabe interpretieren, nicht blind „reparieren“.

### Goldene Regeln

```text
Vendor unter /usr, lokale Overrides unter /etc.
Systemd-Override statt Vendor-Unit bearbeiten.
SELinux-AVC analysieren statt SELinux abschalten.
Firewalld-Zone und Runtime/Permanent unterscheiden.
DNF-Transaktion statt manuelle RPM-Dateikopie.
NetworkManager-Verbindung statt nur flüchtigem ip-Befehl.
Vor Major Upgrade: Backup, Kompatibilität, Konsole, Rollback.
```

## Quellen
- [Fedora Documentation](https://docs.fedoraproject.org/)
- [RHEL Documentation](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/)
- [Fedora DNF Quick Reference](https://docs.fedoraproject.org/en-US/quick-docs/dnf/)
- [Fedora SELinux Getting Started](https://docs.fedoraproject.org/en-US/quick-docs/selinux-getting-started/)

## Verwandte Notizen
- [[Fedora-RHEL-Shortcuts-und-Kommandos]]
- [[Systemd-Premium-Spickzettel]]
- [[SELinux-Premium-Spickzettel]]
- [[firewalld-Premium-Spickzettel]]
- [[dnf-Premium-Spickzettel]]
