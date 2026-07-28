---
title: "Apache HTTP Server – Cheatsheet"
aliases: ["Apache httpd Cheatsheet", "httpd Webserver", "Apache2 Reverse Proxy"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [apache, httpd, webserver, reverse-proxy, tls, linux]
source: "https://httpd.apache.org/docs/2.4/"
---

# Apache HTTP Server – Cheatsheet

> [!abstract] Zweck
> Ausführliche Betriebsreferenz für Apache HTTP Server 2.4: Module, VirtualHosts, Verzeichnisse, Reverse Proxy, TLS, MPM, .htaccess, Logs, Härtung, SELinux, Reload und Diagnose.

> [!danger] Konfiguration immer testen
> Vor Reload oder Restart `apachectl configtest` beziehungsweise `httpd -t` ausführen. Includes, Zertifikate und Modulabhängigkeiten sind Teil des Tests.

## Inhalt

- [[#Namen, Pakete und Pfade]]
- [[#Dienst und Konfiguration]]
- [[#Module und MPM]]
- [[#VirtualHosts und DocumentRoot]]
- [[#Directory-Regeln und .htaccess]]
- [[#Reverse Proxy und Load Balancing]]
- [[#TLS und HTTP2]]
- [[#PHP und Anwendungsserver]]
- [[#Header, Rewrite und Redirects]]
- [[#Logs und Diagnoseinformationen]]
- [[#Performance]]
- [[#Sicherheit]]
- [[#SELinux und Dateirechte]]
- [[#Diagnose]]
- [[#Schnellreferenz]]

## Namen, Pakete und Pfade

| Element | Debian/Ubuntu | Fedora/RHEL |
|---|---|---|
| Paket | `apache2` | `httpd` |
| Dienst | `apache2.service` | `httpd.service` |
| Hauptkonfiguration | `/etc/apache2/apache2.conf` | `/etc/httpd/conf/httpd.conf` |
| Zusatzkonfig | `conf-available/enabled`, `sites-*` | `/etc/httpd/conf.d/*.conf` |
| Module | `mods-available/enabled` | `/etc/httpd/conf.modules.d/` |
| Standardwebroot | `/var/www/html` | `/var/www/html` |
| Logs | `/var/log/apache2/` | `/var/log/httpd/` |
| Laufzeituser | `www-data` | `apache` |

Version/Build:

```bash
apachectl -V
apachectl -M
httpd -V
httpd -M
```

## Dienst und Konfiguration

Fedora/RHEL:

```bash
sudo dnf install httpd
sudo systemctl enable --now httpd
sudo httpd -t
```

Debian/Ubuntu:

```bash
sudo apt install apache2
sudo systemctl enable --now apache2
sudo apachectl configtest
```

Reload:

```bash
sudo apachectl graceful
sudo systemctl reload httpd      # Fedora/RHEL
sudo systemctl reload apache2    # Debian/Ubuntu
```

Status:

```bash
systemctl status httpd
sudo ss -ltnp | grep httpd
curl -I http://127.0.0.1/
```

Effektive VHosts:

```bash
apachectl -S
httpd -S
```

Konfigurationsdump:

```bash
apachectl -t -D DUMP_RUN_CFG
apachectl -t -D DUMP_VHOSTS
```

## Module und MPM

Geladene Module:

```bash
apachectl -M
```

Debian-Modulverwaltung:

```bash
sudo a2enmod rewrite ssl proxy proxy_http headers http2
sudo a2dismod autoindex
```

Fedora/RHEL lädt Paketmodule über Dateien in `conf.modules.d`.

MPMs:

| MPM | Modell | Typische Nutzung |
|---|---|---|
| `event` | Prozesse + Threads, Keepalive effizient | Standard für moderne Proxy-/Static-Workloads |
| `worker` | Prozesse + Threads | ähnlich, weniger eventoptimiert |
| `prefork` | Prozesse ohne Threads | Legacy, z. B. altes mod_php |

Aktiv:

```bash
apachectl -V | grep -i 'Server MPM'
```

> [!important]
> MPM und PHP-Ausführungsmodell müssen zusammenpassen. Für moderne Setups PHP-FPM über `proxy_fcgi` statt eingebettetem mod_php bevorzugen.

## VirtualHosts und DocumentRoot

HTTP:

```apache
<VirtualHost *:80>
    ServerName www.example.org
    ServerAlias example.org
    DocumentRoot /srv/www/example/public

    ErrorLog  ${APACHE_LOG_DIR}/example-error.log
    CustomLog ${APACHE_LOG_DIR}/example-access.log combined

    <Directory /srv/www/example/public>
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
```

Fedora/RHEL ohne `${APACHE_LOG_DIR}` absolute Pfade verwenden.

Debian Site aktivieren:

```bash
sudo a2ensite example.conf
sudo apachectl configtest
sudo systemctl reload apache2
```

Deaktivieren:

```bash
sudo a2dissite 000-default.conf
```

VHost-Zuordnung testen:

```bash
apachectl -S
curl -I -H 'Host: www.example.org' http://127.0.0.1/
```

> [!tip]
> Immer einen bewussten Default-VHost konfigurieren. Sonst landet ein unbekannter Hostname im ersten geladenen VHost und kann Inhalte unerwartet offenlegen.

## Directory-Regeln und .htaccess

Apache trennt URL- und Dateisystemkontext:

```apache
<Directory /srv/www/example/public>
    Require all granted
</Directory>

<Location /internal>
    Require ip 192.0.2.0/24
</Location>

<FilesMatch "^\.env$">
    Require all denied
</FilesMatch>
```

`AllowOverride None` deaktiviert `.htaccess` und ist für kontrollierte Serverkonfiguration meist besser:

- schneller, da Apache nicht in jedem Pfad nach Dateien sucht
- zentral auditierbar
- weniger versteckte Konfiguration

Nur falls Anwendung es benötigt:

```apache
AllowOverride FileInfo AuthConfig
```

Nicht pauschal `AllowOverride All`.

Directory Listing:

```apache
Options -Indexes
```

Symlinks:

```apache
Options +FollowSymLinks
```

Sicherheits- und Performancefolgen prüfen; alternativ `SymLinksIfOwnerMatch`.

## Reverse Proxy und Load Balancing

Module:

```text
proxy proxy_http proxy_wstunnel headers
```

Einfach:

```apache
ProxyPreserveHost On
ProxyPass        / http://127.0.0.1:3000/
ProxyPassReverse / http://127.0.0.1:3000/
```

Gezielter Pfad:

```apache
ProxyPass        /api/ http://127.0.0.1:8080/
ProxyPassReverse /api/ http://127.0.0.1:8080/
```

Slashsemantik auf beiden Seiten konsistent halten und Redirects testen.

Forwarded Header:

```apache
RequestHeader set X-Forwarded-Proto "https"
```

`mod_proxy` setzt bestimmte Forwarded-Informationen selbst; Anwendung und gesamte Proxykette prüfen, nicht doppelt/widersprüchlich setzen.

WebSocket, moderne Versionen können Upgrade über `mod_proxy_http` handhaben; explizit klassisch:

```apache
ProxyPass /socket/ ws://127.0.0.1:3000/socket/
```

Load Balancer:

```apache
<Proxy "balancer://appcluster">
    BalancerMember "http://10.0.0.11:8080" route=node1
    BalancerMember "http://10.0.0.12:8080" route=node2
    ProxySet lbmethod=byrequests
</Proxy>

ProxyPass        /app/ "balancer://appcluster/"
ProxyPassReverse /app/ "balancer://appcluster/"
```

Balancer Manager nur stark geschützt und nicht öffentlich bereitstellen.

Timeouts:

```apache
ProxyTimeout 60
```

## TLS und HTTP2

```apache
<VirtualHost *:443>
    ServerName www.example.org

    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/www.example.org/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/www.example.org/privkey.pem

    Protocols h2 http/1.1

    Header always set Strict-Transport-Security "max-age=31536000"

    DocumentRoot /srv/www/example/public
</VirtualHost>
```

Module prüfen:

```bash
apachectl -M | grep -E 'ssl|http2'
```

TLS-Test:

```bash
openssl s_client -connect www.example.org:443 -servername www.example.org -showcerts </dev/null
curl -Iv --resolve www.example.org:443:127.0.0.1 https://www.example.org/
```

HTTP → HTTPS:

```apache
<VirtualHost *:80>
    ServerName www.example.org
    Redirect permanent / https://www.example.org/
</VirtualHost>
```

HSTS erst nach stabiler HTTPS-Bereitstellung aktivieren.

## PHP und Anwendungsserver

PHP-FPM über Unix-Socket:

```apache
<FilesMatch "\.php$">
    SetHandler "proxy:unix:/run/php-fpm/www.sock|fcgi://localhost/"
</FilesMatch>
```

Debian-Pfad kann etwa `/run/php/php8.x-fpm.sock` sein.

Status:

```bash
systemctl status php-fpm
systemctl status php8.3-fpm
ss -lx | grep php
```

Rails/Puma/Node/Java werden typischerweise als Reverse Proxy angebunden, nicht im Apache-Prozess ausgeführt.

## Header, Rewrite und Redirects

Header:

```apache
Header always set X-Content-Type-Options "nosniff"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set X-Frame-Options "SAMEORIGIN"
```

Redirect mit `mod_alias` ist für einfache Fälle klarer:

```apache
Redirect permanent /alt https://example.org/neu
```

Rewrite:

```apache
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
```

> [!warning]
> `%{HTTP_HOST}` stammt vom Request. Für kanonische Redirects besser festen vertrauenswürdigen Hostnamen verwenden, um Host-Header-Probleme zu vermeiden.

SPA-Fallback:

```apache
FallbackResource /index.html
```

Oder gezielt per Rewrite; API-Pfade ausschließen.

Konfiguration dumpen:

```bash
apachectl -t -D DUMP_RUN_CFG
```

## Logs und Diagnoseinformationen

Live:

```bash
sudo tail -F /var/log/httpd/error_log
sudo tail -F /var/log/httpd/access_log
sudo tail -F /var/log/apache2/error.log
```

LogLevel temporär gezielt:

```apache
LogLevel warn proxy:debug rewrite:trace3
```

Sehr hohe Rewrite-/SSL-Debuglevel erzeugen sensible und große Logs; nach Diagnose zurücksetzen.

Custom Logformat:

```apache
LogFormat "%v %a %l %u %t \"%r\" %>s %b %D" vhost_timing
CustomLog logs/access_log vhost_timing
```

`%D` ist Requestzeit in Mikrosekunden.

`mod_status`, nur geschützt:

```apache
<Location /server-status>
    SetHandler server-status
    Require local
</Location>
```

```bash
curl http://127.0.0.1/server-status?auto
```

## Performance

MPM-Status:

```bash
apachectl -V | grep MPM
```

Wichtige Parameter sind MPM-spezifisch, z. B.:

```apache
StartServers             2
MinSpareThreads         25
MaxSpareThreads         75
ThreadsPerChild         25
MaxRequestWorkers      150
MaxConnectionsPerChild 10000
```

Nicht blind erhöhen. RAM pro Prozess/Thread, Backendkapazität, File Descriptors und reale Concurrency messen.

KeepAlive:

```apache
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 2
```

`event` MPM handhabt Keepalive effizienter. Reverse-Proxy-Timeouts und Backendpools getrennt betrachten.

Kompression:

```apache
AddOutputFilterByType DEFLATE text/html text/plain text/css application/json application/javascript image/svg+xml
```

Caching statischer Inhalte:

```apache
<FilesMatch "\.(css|js|png|jpg|svg|woff2)$">
    Header set Cache-Control "public, max-age=604800, immutable"
</FilesMatch>
```

Nur für versionierte Assets `immutable`.

## Sicherheit

Basis:

```apache
ServerTokens Prod
ServerSignature Off
TraceEnable Off
```

Diese Optionen reduzieren Information, ersetzen aber kein Patchmanagement.

- Nur benötigte Module laden.
- `Options -Indexes`.
- `.git`, `.env`, Backups und Editorfiles sperren.
- `AllowOverride None`, wenn möglich.
- Schreibrechte auf Webroot vermeiden.
- Uploads separat und nicht ausführbar.
- Reverse Proxy kein offener Forward Proxy:

```apache
ProxyRequests Off
```

- `mod_status`, Balancer Manager und Adminpfade nur lokal/VPN/Auth.
- Requestlimits angemessen setzen:

```apache
LimitRequestBody 104857600
LimitRequestFields 100
LimitRequestFieldSize 8190
```

- Methoden nur anwendungsgerecht zulassen.
- TLS-Keyschutz und sichere Erneuerung.
- Security Header/CSP testen.
- Symlink- und UserDir-Funktionen nur bei Bedarf.

## SELinux und Dateirechte

Kontext für Inhalte:

```bash
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/www/example(/.*)?'
sudo restorecon -RFv /srv/www/example
```

Schreibbar:

```bash
sudo semanage fcontext -a -t httpd_sys_rw_content_t '/srv/www/example/uploads(/.*)?'
sudo restorecon -RFv /srv/www/example/uploads
```

Netzwerkzugriff zu Backend:

```bash
getsebool httpd_can_network_connect
sudo setsebool -P httpd_can_network_connect on
```

AVCs:

```bash
sudo ausearch -m AVC -ts recent
```

Dateipfad vollständig prüfen:

```bash
namei -l /srv/www/example/public/index.html
```

## Diagnose

Basis:

```bash
sudo apachectl configtest
sudo apachectl -S
sudo apachectl -M
sudo apachectl -V
systemctl status httpd
sudo journalctl -u httpd -b
sudo ss -ltnp | grep httpd
```

Debian entsprechend `apache2`.

Lokaler VHost:

```bash
curl -v -H 'Host: www.example.org' http://127.0.0.1/
curl -vk --resolve www.example.org:443:127.0.0.1 https://www.example.org/
```

Backend:

```bash
curl -v http://127.0.0.1:3000/health
```

Typische Fehler:

| Symptom | Häufige Ursache |
|---|---|
| 403 | `Require`, Dateirechte, SELinux, Directory-Kontext |
| 404 | falscher VHost/DocumentRoot/Rewrite |
| 500 | Syntax zur Laufzeit, `.htaccess`, Anwendung/FastCGI |
| 502/503 | Backend/Socket/Worker nicht verfügbar |
| falscher VHost | Reihenfolge, `ServerName`, DNS/Hostheader |
| Reload fehlschlägt | Modul/Direktive/Zertifikat/Include |
| hohe Last | MPM-Limit, langsames Backend, Keepalive, Bots |

Prüfreihenfolge:

1. `configtest`.
2. `apachectl -S` und Hostheader.
3. Listener/Firewall.
4. Error Log zum Requestzeitpunkt.
5. Directory-/Location-Regeln.
6. Pfadrechte und SELinux.
7. Backend direkt testen.
8. MPM/Worker-/Ressourcenstatus.
9. Module und Versionskompatibilität.

## Schnellreferenz

```bash
apachectl -V
apachectl -M
apachectl -S
apachectl configtest
apachectl graceful
systemctl reload httpd
journalctl -u httpd -b
curl -v -H 'Host: example.org' http://127.0.0.1/
```

## Quellen
- [Apache HTTP Server 2.4 Documentation](https://httpd.apache.org/docs/2.4/)
- [Apache Security Tips](https://httpd.apache.org/docs/2.4/misc/security_tips.html)
- [Mozilla TLS Configuration Generator](https://ssl-config.mozilla.org/)

## Verwandte Notizen
- [[nginx – Cheatsheet]]
- [[Ruby on Rails – Cheatsheet]]
- [[OpenSSL-Cheatsheet]]
- [[SELinux – Cheatsheet]]
