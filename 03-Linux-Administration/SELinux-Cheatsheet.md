---
title: "SELinux – Cheatsheet"
aliases: ["SELinux Cheatsheet", "AVC Diagnose", "semanage restorecon"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [selinux, linux, security, fedora, rhel, mac]
source: "https://docs.fedoraproject.org/en-US/quick-docs/selinux-getting-started/"
---

# SELinux – Cheatsheet

> [!abstract] Zweck
> Ausführliche Praxisreferenz für SELinux: Modi, Kontexte, Typen, Booleans, Ports, Dateilabels, AVC-Analyse, eigene Policies, Container und sichere Fehlersuche.

> [!danger]
> SELinux nicht als erste Reaktion deaktivieren. Enforcing deckt falsche Pfade, Rechte, unerwartete Netzwerkzugriffe und Policyverletzungen auf. Die korrekte Lösung ist meist Label, Boolean, Porttyp, Anwendungsdesign oder eine eng begrenzte lokale Policy.

## Inhalt

- [[#Grundmodell]]
- [[#Status und Modi]]
- [[#Kontexte lesen]]
- [[#Dateikontexte]]
- [[#Booleans]]
- [[#Porttypen]]
- [[#AVC-Diagnose]]
- [[#Eigene Policy]]
- [[#SELinux und Container]]
- [[#Fehlerbilder und Prüfreihenfolge]]

## Grundmodell

SELinux ist Mandatory Access Control zusätzlich zu klassischen Unix-Rechten.

```text
Zugriff erlaubt nur wenn:
DAC-Rechte erlauben
UND
SELinux-Policy erlaubt
UND
weitere Mechanismen wie ACL/Capabilities erlauben
```

Kontextformat:

```text
user:role:type:level
```

Beispiel:

```text
system_u:object_r:httpd_sys_content_t:s0
```

In der Type-Enforcement-Praxis sind besonders **Domain** des Prozesses und **Type** des Zielobjekts relevant.

```text
httpd_t  --read-->  httpd_sys_content_t
```

## Status und Modi

```bash
getenforce
sestatus
cat /etc/selinux/config
```

| Modus | Wirkung |
|---|---|
| Enforcing | Policy wird erzwungen und Verstöße protokolliert |
| Permissive | Verstöße werden protokolliert, aber nicht blockiert |
| Disabled | SELinux nicht aktiv; erneute Aktivierung kann Relabel erfordern |

Temporär:

```bash
sudo setenforce 0
sudo setenforce 1
```

> [!warning]
> Nur als enger A/B-Diagnosetest. Ergebnis „funktioniert permissive“ beweist SELinux-Beteiligung, aber noch nicht die richtige Policybehebung.

Domain permissive statt global, sofern Tool/Policy unterstützt:

```bash
sudo semanage permissive -a myservice_t
sudo semanage permissive -l
sudo semanage permissive -d myservice_t
```

## Kontexte lesen

Dateien:

```bash
ls -lZ /var/www
stat -c '%C %n' /var/www/html/index.html
```

Prozesse:

```bash
ps -eZ | head
ps -efZ | grep httpd
```

Sockets:

```bash
ss -lntupZ
```

Benutzerzuordnung:

```bash
id -Z
semanage login -l
semanage user -l
```

Kontext temporär ändern:

```bash
sudo chcon -t httpd_sys_content_t /srv/web/index.html
```

> [!warning]
> `chcon` ist nicht dauerhaft gegen `restorecon`/Relabel. Für persistente Pfadzuordnung `semanage fcontext` verwenden.

## Dateikontexte

Erwarteten Kontext anzeigen:

```bash
matchpathcon /srv/web/index.html
```

Standard wiederherstellen:

```bash
sudo restorecon -v /srv/web/index.html
sudo restorecon -Rv /srv/web
```

Dauerhafte Regel:

```bash
sudo semanage fcontext -a \
  -t httpd_sys_content_t \
  '/srv/web(/.*)?'
sudo restorecon -Rv /srv/web
```

Schreibbarer Webinhalt:

```bash
sudo semanage fcontext -a \
  -t httpd_sys_rw_content_t \
  '/srv/web/uploads(/.*)?'
sudo restorecon -Rv /srv/web/uploads
```

Regeln:

```bash
semanage fcontext -l | grep '/srv/web'
```

Ändern/löschen:

```bash
sudo semanage fcontext -m -t NEUER_TYP '/srv/web(/.*)?'
sudo semanage fcontext -d '/srv/web(/.*)?'
```

### Relabel

Ganzes Dateisystem relabeln nur geplant:

```bash
sudo fixfiles -F onboot
sudo reboot
```

Oder je Plattform dokumentierter Autorelabelmechanismus. Dauer, Platz, Konsole und kritische Dienste beachten.

## Booleans

Anzeigen:

```bash
getsebool -a
getsebool -a | grep httpd
semanage boolean -l | grep httpd
```

Temporär:

```bash
sudo setsebool httpd_can_network_connect on
```

Persistent:

```bash
sudo setsebool -P httpd_can_network_connect on
```

> [!important]
> Boolean beschreibt bewusst erlaubte Funktionsklasse. Namen und Beschreibung lesen; nicht alle passenden Treffer aktivieren. `-P` kompiliert/speichert Policy und kann dauern.

## Porttypen

Anzeigen:

```bash
semanage port -l | grep http_port_t
```

Eigenen TCP-Port dem erlaubten Typ zuordnen:

```bash
sudo semanage port -a -t http_port_t -p tcp 8443
```

Falls Eintrag existiert und Typ geändert werden soll:

```bash
sudo semanage port -m -t http_port_t -p tcp 8443
```

Löschen:

```bash
sudo semanage port -d -t http_port_t -p tcp 8443
```

Firewalld und Listener zusätzlich prüfen; SELinux-Porttyp öffnet keine Firewall.

## AVC-Diagnose

### Ereignisse finden

```bash
sudo ausearch -m AVC,USER_AVC -ts recent
sudo ausearch -m AVC -ts today -i
sudo journalctl -t setroubleshoot --since '-1 hour'
```

Auditlog:

```bash
sudo grep 'avc:  denied' /var/log/audit/audit.log | tail
```

Falls setroubleshoot verfügbar:

```bash
sudo sealert -a /var/log/audit/audit.log
```

### AVC lesen

Wichtige Felder:

```text
scontext   Quellprozess/Domain
tcontext   Zielobjekt/Type
tclass     Objektklasse, z. B. file, dir, tcp_socket
{ read }   verweigerte Berechtigung
name/path  Ziel, sofern protokolliert
permissive Enforcingzustand für Ereignis
```

Diagnosefragen:

1. Sollte der Prozess diesen Zugriff fachlich haben?
2. Ist Quellprozess in erwarteter Domain?
3. Hat Zielpfad erwarteten Typ?
4. Existiert ein passender Boolean?
5. Ist ein alternativer Standardpfad vorgesehen?
6. Ist Port korrekt typisiert?
7. Ist die Anwendung kompromittiert oder falsch konfiguriert?

### `audit2why` und `audit2allow`

```bash
sudo ausearch -m AVC -ts recent | audit2why
```

Policyvorschlag:

```bash
sudo ausearch -m AVC -ts recent | audit2allow -M local-myservice
```

> [!danger]
> Ausgabe von `audit2allow` nie blind installieren. Sie bildet beobachtetes Verhalten ab – einschließlich Fehlkonfiguration oder Angriff. `.te` lesen, Zugriffe minimieren, in Testumgebung verifizieren.

## Eigene Policy

Generierter Modulumfang prüfen:

```bash
cat local-myservice.te
semodule -i local-myservice.pp
semodule -l | grep local-myservice
semodule -r local-myservice
```

Besser: Anwendung in eigener Domain mit klaren Dateitypen/Entrypoints modellieren, wenn sie dauerhaft betrieben wird. Werkzeuge wie `sepolicy generate` können Ausgangspunkt sein, ersetzen keine Policyreview.

```bash
sepolicy manpage -a
sepolicy transition -s init_t -t myservice_t
```

Verfügbarkeit hängt von installierten Policy-Tools ab.

## SELinux und Container

Container-Runtimes nutzen Labels zur Isolation. Volumeoptionen:

```text
:z   gemeinsames relabeltes Volume
:Z   privates eindeutiges Label
```

Beispiel Podman:

```bash
podman run --rm -v /srv/data:/data:Z IMAGE
```

> [!warning]
> `:Z`/`:z` kann Hostpfade relabeln. Nicht blind auf Systemverzeichnisse oder von anderen Diensten verwendete Pfade anwenden.

Containerstatus:

```bash
ps -eZ | grep container
ls -Zd /srv/data
podman inspect CONTAINER
```

Booleans und Netzwerkzugriffe je Use Case prüfen; `--privileged` ist keine normale SELinux-Lösung.

## Fehlerbilder und Prüfreihenfolge

### Dienst darf Datei nicht lesen

```bash
namei -l /srv/app/config.yml
ls -lZ /srv/app/config.yml
ps -eZ | grep dienst
matchpathcon /srv/app/config.yml
sudo ausearch -m AVC -ts recent -i
```

Dann `semanage fcontext + restorecon` statt `chmod 777`/SELinux off.

### Dienst darf Port nicht binden

```bash
ss -lntup
semanage port -l | grep -E 'http|8443'
sudo ausearch -m AVC -ts recent -i
```

Porttyp ergänzen, Firewalld separat öffnen.

### Kein AVC sichtbar

- Auditdienst/Backlog?
- Ereignis im Journal?
- `dontaudit` unterdrückt Meldung?
- klassisches DAC-Recht oder Anwendungskonfiguration statt SELinux?
- richtige Uhrzeit/Boot?

Zum Debuggen kann `semodule -DB` dontaudit vorübergehend deaktivieren:

```bash
sudo semodule -DB
# reproduzieren
sudo semodule -B
```

Nur kontrolliert; Logvolumen beachten.

### Universelle Prüfreihenfolge

```bash
getenforce
sestatus
id -Z
ps -eZ | grep PROZESS
ls -lZ /PFAD
matchpathcon /PFAD
sudo ausearch -m AVC,USER_AVC -ts recent -i
```

Entscheidung:

```text
falsches Label → semanage fcontext + restorecon
vorgesehene optionale Fähigkeit → passenden Boolean prüfen
ungewöhnlicher Port → semanage port
wirklich neue legitime Zugriffsklasse → minimale lokale Policy
fachlich nicht legitimer Zugriff → Anwendung/Architektur korrigieren
```

## Quellen
- [Fedora SELinux Getting Started](https://docs.fedoraproject.org/en-US/quick-docs/selinux-getting-started/)
- [RHEL Using SELinux](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_selinux/)
- [SELinux Project Wiki](https://selinuxproject.org/page/Main_Page)

## Verwandte Notizen
- [[Fedora-RHEL-Cheatsheet]]
- [[firewalld-Cheatsheet]]
- [[POSIX-ACL-Cheatsheet]]
- [[nginx-Cheatsheet]]
