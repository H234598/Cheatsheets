---
title: "Fedora/RHEL – Shortcuts und Kommandos"
aliases: ["Fedora Shortcuts", "RHEL Schnellreferenz", "Red Hat Commands"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [fedora, rhel, linux, shortcuts, commands]
source: "https://docs.fedoraproject.org/en-US/quick-docs/"
---

# Fedora/RHEL – Shortcuts und Kommandos

> [!abstract] Zweck
> Kompakte Unterseite mit den häufigsten Fedora-/RHEL-Befehlen für Systemstatus, Dienste, Logs, Pakete, SELinux, Firewall, Netzwerk, Benutzer, Storage, Kernel und Rettung.

## System identifizieren

```bash
cat /etc/os-release
hostnamectl
uname -a
uname -r
uname -m
uptime
```

## Zustand auf einen Blick

```bash
systemctl --failed
journalctl -p warning..alert -b
free -h
df -hT
findmnt -D
lsblk -f
ip -brief address
ip route
ss -lntup
```

## Systemd

```bash
systemctl status NAME
systemctl is-active NAME
systemctl is-enabled NAME
sudo systemctl start|stop|restart|reload NAME
sudo systemctl enable|disable NAME
sudo systemctl enable --now NAME
sudo systemctl edit NAME
systemctl cat NAME
systemctl list-dependencies NAME
systemctl list-timers --all
```

```bash
sudo systemctl daemon-reload
sudo systemctl reset-failed NAME
```

## Journal

```bash
journalctl -b
journalctl -b -1
journalctl -u NAME -b
journalctl -u NAME -f
journalctl --since 'today'
journalctl --since '-30 min'
journalctl -p err..alert
journalctl _PID=1234
journalctl -k -b
```

Platz:

```bash
journalctl --disk-usage
sudo journalctl --vacuum-time=30d
```

## DNF

```bash
sudo dnf upgrade --refresh
sudo dnf install PAKET
sudo dnf remove PAKET
dnf search BEGRIFF
dnf info PAKET
dnf list --installed
dnf provides '*/DATEI'
dnf repoquery PAKET
dnf repolist --all
dnf history
dnf history info last
sudo dnf clean all
```

## RPM

```bash
rpm -q PAKET
rpm -qi PAKET
rpm -ql PAKET
rpm -qc PAKET
rpm -qf /PFAD/DATEI
rpm -qp DATEI.rpm
rpm -qpl DATEI.rpm
rpm -K DATEI.rpm
rpm -Va
```

## SELinux

```bash
getenforce
sestatus
ls -lZ /PFAD
ps -eZ | head
sudo ausearch -m AVC,USER_AVC -ts recent
sudo restorecon -Rv /PFAD
semanage fcontext -l | grep MUSTER
getsebool -a | grep httpd
sudo setsebool -P BOOLEAN on
semanage port -l | grep http
```

Nur Diagnose:

```bash
sudo setenforce 0
sudo setenforce 1
```

Nie als Dauerlösung.

## Firewalld

```bash
firewall-cmd --state
firewall-cmd --get-active-zones
firewall-cmd --get-default-zone
firewall-cmd --zone=public --list-all
firewall-cmd --get-services
sudo firewall-cmd --zone=public --add-service=https
sudo firewall-cmd --zone=public --add-port=8443/tcp
sudo firewall-cmd --runtime-to-permanent
sudo firewall-cmd --reload
sudo firewall-cmd --check-config
```

## Netzwerk

```bash
nmcli general status
nmcli device status
nmcli connection show
nmcli -f NAME,UUID,TYPE,DEVICE connection show
ip -brief link
ip -brief address
ip route
ip neigh
resolvectl status
ss -lntup
ping -c 4 HOST
tracepath HOST
```

Verbindung:

```bash
sudo nmcli connection up NAME
sudo nmcli connection down NAME
sudo nmcli device reapply IFACE
```

## Benutzer und Gruppen

```bash
id USER
getent passwd USER
getent group GROUP
sudo useradd -m USER
sudo passwd USER
sudo usermod -aG wheel,GROUP USER
sudo userdel -r USER
sudo groupadd GROUP
sudo gpasswd -a USER GROUP
sudo visudo -c
```

## Dateien und Rechte

```bash
stat DATEI
namei -l /PFAD/DATEI
ls -lZ DATEI
getfacl DATEI
sudo chown USER:GROUP DATEI
chmod 640 DATEI
sudo restorecon -v DATEI
```

## Storage

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,FSVER,LABEL,UUID,MOUNTPOINTS
blkid
findmnt
findmnt -T /PFAD
df -hT
du -xhd1 /VAR | sort -h
sudo fdisk -l
sudo pvs
sudo vgs
sudo lvs -a -o +devices
```

## Prozesse und Ressourcen

```bash
ps auxf
ps -eo pid,ppid,user,stat,%cpu,%mem,etime,cmd --sort=-%cpu | head
top
systemd-cgtop
pidstat 1
vmstat 1
iostat -xz 1
lsof -p PID
strace -f -p PID
```

Zusatztools können Pakete erfordern.

## Ports und Sockets

```bash
ss -lntup
ss -s
sudo lsof -nP -iTCP -sTCP:LISTEN
sudo fuser -v 8080/tcp
```

## Kernel und Hardware

```bash
uname -r
dmesg --level=err,warn
journalctl -k -b
lscpu
lsmem
lspci -nnk
lsusb -t
lsmod
modinfo MODUL
sudo modprobe MODUL
```

## Boot

```bash
systemd-analyze
systemd-analyze blame
systemd-analyze critical-chain
journalctl -b -1
sudo grubby --default-kernel
sudo grubby --info=ALL
lsinitrd | less
```

## Schnelle Fehleraufnahme

```bash
{
  date -Is
  cat /etc/os-release
  uname -a
  uptime
  systemctl --failed
  df -hT
  free -h
  ip -brief address
  ip route
} | tee system-snapshot.txt
```

Keine Geheimnisse/PII in Supportpakete aufnehmen; Ausgabe vor Weitergabe prüfen.

## Quellen
- [Fedora Quick Docs](https://docs.fedoraproject.org/en-US/quick-docs/)
- [RHEL System Administration](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/)
- [Linux man-pages](https://www.man7.org/linux/man-pages/)

## Verwandte Notizen
- [[Fedora-RHEL-Cheatsheet]]
- [[Systemd-Cheatsheet]]
- [[SELinux-Cheatsheet]]
- [[firewalld-Cheatsheet]]
