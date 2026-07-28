---
title: "nginx – Cheatsheet"
aliases: ["Nginx Cheatsheet", "nginx Webserver", "nginx Reverse Proxy"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [nginx, webserver, reverse-proxy, tls, linux, http]
source: "https://nginx.org/en/docs/"
---

# nginx – Cheatsheet

> [!abstract] Zweck
> Ausführliche Betriebsreferenz für nginx: Paketierung, Konfigurationsmodell, Serverblöcke, Reverse Proxy, TLS, Static Files, FastCGI, Header, Caching, Rate Limits, Logs, Härtung, Reload und Diagnose.

> [!danger] Konfiguration vor Reload testen
> Änderungen immer mit `nginx -t` prüfen. Ein `reload` übernimmt gültige Konfiguration normalerweise ohne harte Unterbrechung; ein `restart` kann Verbindungen abbrechen. Zertifikate, Includes und Berechtigungen gehören in den Test.

## Inhalt

- [[#Architektur und wichtige Pfade]]
- [[#Installation und Dienst]]
- [[#Konfigurationsmodell]]
- [[#Serverblöcke und Static Files]]
- [[#Reverse Proxy]]
- [[#TLS und HTTP2]]
- [[#FastCGI und PHP-FPM]]
- [[#Header und Client-IP]]
- [[#Caching, Kompression und Performance]]
- [[#Rate Limits und Zugriffsschutz]]
- [[#Logs und Logrotation]]
- [[#Sicherheit]]
- [[#Reload, Upgrade und Rollback]]
- [[#Diagnose]]
- [[#Schnellreferenz]]

## Architektur und wichtige Pfade

nginx verwendet ein Master-/Worker-Modell:

```text
Masterprozess
├── liest Konfiguration
├── bindet Ports
├── startet/reloaded Worker
└── verwaltet Signale
    ├── Worker 1
    ├── Worker 2
    └── ...
```

Typische Pfade, distributionsabhängig:

| Zweck | Debian/Ubuntu | Fedora/RHEL |
|---|---|---|
| Hauptdatei | `/etc/nginx/nginx.conf` | `/etc/nginx/nginx.conf` |
| Site-Definitionen | `/etc/nginx/sites-available/`, `sites-enabled/` | häufig `/etc/nginx/conf.d/*.conf` |
| Webroot | `/var/www/html` | `/usr/share/nginx/html` |
| Logs | `/var/log/nginx/` | `/var/log/nginx/` |
| Dienst | `nginx.service` | `nginx.service` |

Kompilierungsoptionen und Pfade:

```bash
nginx -V 2>&1 | tr ' ' '\n' | less
```

Version:

```bash
nginx -v
nginx -V
```

## Installation und Dienst

Fedora/RHEL:

```bash
sudo dnf install nginx
sudo systemctl enable --now nginx
```

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install nginx
sudo systemctl enable --now nginx
```

Status:

```bash
systemctl status nginx
sudo ss -ltnp | grep nginx
curl -I http://127.0.0.1/
```

Firewall, Fedora/RHEL:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Konfigurationsmodell

Vereinfachte Hierarchie:

```nginx
main {
    events { }
    http {
        upstream backend { }
        server {
            location / { }
        }
    }
}
```

Konfiguration testen:

```bash
sudo nginx -t
sudo nginx -T | less
```

`nginx -T` testet und gibt die expandierte Konfiguration inklusive Includes aus. Geheimnisse/Interne Hostnamen vor Weitergabe prüfen.

Wichtige Kontexte:

| Direktive | Typischer Kontext |
|---|---|
| `worker_processes` | main |
| `worker_connections` | events |
| `log_format`, `gzip`, `upstream` | http |
| `listen`, `server_name` | server |
| `proxy_pass`, `root`, `try_files` | location |

> [!important] Vererbung ist direktivenspezifisch
> nginx-Direktiven werden nicht alle gleich vererbt. Bei unerwartetem Verhalten die Dokumentation der konkreten Direktive und die effektive Konfiguration prüfen.

## Serverblöcke und Static Files

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name www.example.org example.org;

    root /srv/www/example/public;
    index index.html;

    access_log /var/log/nginx/example.access.log;
    error_log  /var/log/nginx/example.error.log warn;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

Verzeichnis vorbereiten:

```bash
sudo install -d -o root -g nginx -m 0750 /srv/www/example
sudo install -d -o deploy -g nginx -m 0750 /srv/www/example/public
```

SELinux-Kontext:

```bash
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/www/example(/.*)?'
sudo restorecon -RFv /srv/www/example
```

Schreibverzeichnis nur gezielt:

```bash
sudo semanage fcontext -a -t httpd_sys_rw_content_t '/srv/www/example/uploads(/.*)?'
sudo restorecon -RFv /srv/www/example/uploads
```

`root` versus `alias`:

```nginx
location /assets/ {
    root /srv/www/example;
    # /assets/a.css → /srv/www/example/assets/a.css
}

location /downloads/ {
    alias /srv/files/public/;
    # /downloads/a.zip → /srv/files/public/a.zip
}
```

Bei `alias` sind Slash- und Regex-Semantik besonders sorgfältig zu testen.

SPA-Fallback:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

Nicht für APIs verwenden, da echte 404 sonst als HTML zurückkommen können.

## Reverse Proxy

Upstream:

```nginx
upstream app_backend {
    least_conn;
    server 127.0.0.1:3000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

Server:

```nginx
server {
    listen 443 ssl;
    server_name app.example.org;

    location / {
        proxy_pass http://app_backend;
        proxy_http_version 1.1;

        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

`proxy_pass`-Slashsemantik:

```nginx
location /api/ {
    proxy_pass http://backend/;
}
```

Hier wird `/api/x` typischerweise zu `/x`. Ohne abschließenden Slash:

```nginx
location /api/ {
    proxy_pass http://backend;
}
```

bleibt der URI typischerweise `/api/x`. Immer mit realen Requests testen.

WebSocket:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

location /socket/ {
    proxy_pass http://app_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
}
```

Große Uploads:

```nginx
client_max_body_size 100m;
proxy_request_buffering off;
```

Nur dort setzen, wo erforderlich. Anwendungslimits und Speicher-/Timeoutfolgen berücksichtigen.

## TLS und HTTP2

```nginx
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name example.org;

    ssl_certificate     /etc/letsencrypt/live/example.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:SSL:20m;
    ssl_session_timeout 1d;

    add_header Strict-Transport-Security 'max-age=31536000' always;
}
```

HTTP → HTTPS:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name example.org www.example.org;
    return 301 https://example.org$request_uri;
}
```

> [!danger] HSTS
> HSTS bindet Browser an HTTPS. `includeSubDomains` und `preload` erst aktivieren, wenn **alle** betroffenen Hosts dauerhaft korrekt per HTTPS erreichbar sind. Fehlkonfiguration kann Nutzer aussperren.

Zertifikat prüfen:

```bash
sudo nginx -t
openssl x509 -in /etc/letsencrypt/live/example.org/fullchain.pem -noout -subject -issuer -dates
openssl s_client -connect example.org:443 -servername example.org -showcerts </dev/null
```

OCSP-Stapling ist CA-/Ketten- und Resolver-abhängig; nur nach vollständigem Test konfigurieren.

## FastCGI und PHP-FPM

```nginx
location ~ \.php$ {
    include fastcgi_params;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    fastcgi_pass unix:/run/php-fpm/www.sock;
}
```

Robuster Schutz, nur existierende Skripte:

```nginx
location ~ \.php$ {
    try_files $uri =404;
    include fastcgi_params;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    fastcgi_pass unix:/run/php-fpm/www.sock;
}
```

Socket und Rechte:

```bash
systemctl status php-fpm
ss -lx | grep php
namei -l /run/php-fpm/www.sock
```

SELinux bei Upstream-Netzwerkzugriff:

```bash
getsebool httpd_can_network_connect
sudo setsebool -P httpd_can_network_connect on
```

Nur aktivieren, wenn nginx tatsächlich Netzwerk-Upstreams erreichen muss.

## Header und Client-IP

Sicherheitsheader – an Anwendung anpassen:

```nginx
add_header X-Content-Type-Options nosniff always;
add_header Referrer-Policy strict-origin-when-cross-origin always;
add_header X-Frame-Options SAMEORIGIN always;
```

CSP nicht blind kopieren; Anwendungsressourcen inventarisieren und zunächst Report-Only testen.

Hinter vertrauenswürdigem Load Balancer:

```nginx
set_real_ip_from 10.0.0.0/8;
real_ip_header X-Forwarded-For;
real_ip_recursive on;
```

> [!danger]
> `set_real_ip_from` nur auf bekannte Proxy-Netze begrenzen. Sonst kann ein Client die geloggte/ausgewertete IP fälschen.

Forwarded Header zum Backend nicht unkontrolliert vom Client übernehmen, sondern neu setzen.

## Caching, Kompression und Performance

Static Cache Header:

```nginx
location ~* \.(?:css|js|png|jpg|jpeg|gif|svg|woff2)$ {
    expires 7d;
    add_header Cache-Control 'public, immutable';
    try_files $uri =404;
}
```

`immutable` nur für versionierte/gehashte Assets.

Gzip:

```nginx
gzip on;
gzip_comp_level 5;
gzip_min_length 1024;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript application/xml image/svg+xml;
```

Proxy Cache – nur mit klarer Cache-Key-/Auth-/Cookie-Strategie:

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:20m max_size=1g inactive=60m;

location /public-api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 1m;
    add_header X-Cache-Status $upstream_cache_status;
    proxy_pass http://app_backend;
}
```

> [!danger]
> Personalisierte oder authentisierte Antworten dürfen nicht versehentlich zwischen Benutzern geteilt werden. `Authorization`, Cookies, `Vary`, Cache-Key und `Set-Cookie` explizit behandeln.

Workerbasis:

```nginx
worker_processes auto;

events {
    worker_connections 1024;
    multi_accept on;
}
```

Maximale Verbindungen hängen zusätzlich von File-Descriptor-Limits, Upstream-Verbindungen und TLS ab.

```bash
systemctl show nginx -p LimitNOFILE
cat /proc/$(cat /run/nginx.pid)/limits
```

## Rate Limits und Zugriffsschutz

Request Rate:

```nginx
limit_req_zone $binary_remote_addr zone=perip:10m rate=10r/s;

location /login {
    limit_req zone=perip burst=20 nodelay;
    proxy_pass http://app_backend;
}
```

Verbindungen:

```nginx
limit_conn_zone $binary_remote_addr zone=addr:10m;
limit_conn addr 20;
```

Rate Limiting muss Proxy-/Client-IP korrekt sehen und kann NAT-Nutzer gemeinsam treffen. Monitoring und realistische Bursts verwenden.

Basic Auth:

```bash
htpasswd -c /etc/nginx/.htpasswd alice
```

```nginx
auth_basic 'Intern';
auth_basic_user_file /etc/nginx/.htpasswd;
```

Basic Auth nur über TLS.

IP-Allowlist:

```nginx
allow 192.0.2.0/24;
deny all;
```

## Logs und Logrotation

Standard:

```bash
sudo tail -F /var/log/nginx/access.log
sudo tail -F /var/log/nginx/error.log
```

Strukturiertes JSON-ähnliches Log, korrektes JSON-Escaping:

```nginx
log_format json escape=json '{'
  '"time":"$time_iso8601",'
  '"remote_addr":"$remote_addr",'
  '"request":"$request",'
  '"status":$status,'
  '"bytes":$body_bytes_sent,'
  '"request_time":$request_time,'
  '"upstream_time":"$upstream_response_time"'
'}';
```

Aktivieren:

```nginx
access_log /var/log/nginx/access.json json;
```

Fehlerstufen:

```nginx
error_log /var/log/nginx/error.log warn;
```

Temporär Debug erfordert passenden Build und erzeugt viele/sensible Logs.

Logrotate prüfen:

```bash
cat /etc/logrotate.d/nginx
sudo logrotate -d /etc/logrotate.conf
```

## Sicherheit

- nginx/OS aktuell halten.
- Unnötige Module vermeiden.
- Webroot nicht für Worker schreibbar machen.
- Uploads außerhalb ausführbarer Pfade speichern.
- Directory Listing nur bewusst (`autoindex off` ist Standard).
- Dotfiles sperren, ACME-Ausnahme beachten:

```nginx
location ~ /\.(?!well-known/) {
    deny all;
}
```

- Methoden begrenzen nur mit Verständnis der Anwendung:

```nginx
limit_except GET HEAD POST {
    deny all;
}
```

- Server-Tokens reduzieren:

```nginx
server_tokens off;
```

Dies ist keine echte Sicherheitsgrenze.

- TLS-Key-Dateien restriktiv halten.
- Temporär-/Cacheverzeichnisse und SELinux/AppArmor beachten.
- Request Smuggling vermeiden: Proxykette aktuell halten, Header nicht widersprüchlich umschreiben.
- Backends möglichst nur intern/Loopback erreichbar machen.

## Reload, Upgrade und Rollback

Test und Reload:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Signal direkt:

```bash
sudo nginx -s reload
```

Konfiguration sichern:

```bash
sudo cp -a /etc/nginx /etc/nginx.backup.$(date +%F-%H%M%S)
```

Besser versionieren:

```bash
sudo git -C /etc/nginx status
```

Vor Änderungen:

1. `nginx -T` sichern.
2. Zertifikat-/Keypfade prüfen.
3. Konfiguration testen.
4. lokalen Hostheader-Test durchführen.
5. reloaden.
6. Logs und echte Requests prüfen.
7. alten Stand für Rollback bereithalten.

## Diagnose

Effektive Konfiguration:

```bash
sudo nginx -T > /tmp/nginx-effective.txt
```

Ports/Prozesse:

```bash
systemctl status nginx
sudo ss -ltnp | grep nginx
ps -ef | grep '[n]ginx'
```

Lokaler vHost-Test:

```bash
curl -v --resolve example.org:443:127.0.0.1 https://example.org/
curl -I -H 'Host: example.org' http://127.0.0.1/
```

Upstream direkt:

```bash
curl -v http://127.0.0.1:3000/health
```

Dateirechte/Pfad:

```bash
namei -l /srv/www/example/public/index.html
sudo -u nginx test -r /srv/www/example/public/index.html && echo lesbar
```

SELinux:

```bash
ls -laZ /srv/www/example
sudo ausearch -m AVC -ts recent
```

Typische Statuscodes:

| Code | Häufige nginx-Ursache |
|---:|---|
| 400 | ungültige Header/Request, TLS auf HTTP-Port |
| 403 | Rechte, `deny`, fehlender Index, SELinux |
| 404 | falscher `root`/`alias`/`try_files`/URI-Rewrite |
| 413 | `client_max_body_size` |
| 499 | Client brach Verbindung ab |
| 502 | Upstream nicht erreichbar/Socketrechte/Protokoll falsch |
| 503 | Upstream/Rate Limit/Maintenance |
| 504 | Upstream-Timeout |

Prüfreihenfolge 502/504:

1. Upstreamprozess und Listener.
2. direkte Anfrage vom nginx-Host.
3. Unix-Socketrechte/SELinux.
4. `proxy_pass`-Schema, Host und Port.
5. DNS-Auflösung aus nginx-Kontext.
6. Timeouts und Backendlogs.
7. Ressourcenlimits.

## Schnellreferenz

```bash
nginx -v
sudo nginx -t
sudo nginx -T | less
sudo systemctl reload nginx
sudo journalctl -u nginx -b
sudo tail -F /var/log/nginx/error.log
sudo ss -ltnp | grep nginx
curl -v --resolve host:443:127.0.0.1 https://host/
```

## Quellen
- [nginx Documentation](https://nginx.org/en/docs/)
- [nginx Admin Guide](https://docs.nginx.com/nginx/admin-guide/)
- [Mozilla TLS Configuration Generator](https://ssl-config.mozilla.org/)

## Verwandte Notizen
- [[Apache HTTP Server – Cheatsheet]]
- [[Ruby on Rails – Cheatsheet]]
- [[OpenSSL-Cheatsheet]]
- [[SELinux – Cheatsheet]]
