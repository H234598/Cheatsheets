---
title: "OpenSSL – Premium-Spickzettel"
aliases: ["OpenSSL Cheatsheet", "TLS und PKI mit OpenSSL", "OpenSSL CLI"]
created: 2026-07-16
modified: 2026-07-17
type: reference
status: fertig
origin: "Premium Spickzettel I – vollständig überarbeitet"
reviewed: 2026-07-17
tags: [openssl, tls, pki, x509, csr, rsa, ec, pkcs12, zertifikate, security]
source: "https://docs.openssl.org/master/man1/openssl/"
---

# OpenSSL – Premium-Spickzettel

> [!abstract] Zweck
> Praxisreferenz für OpenSSL 3.x: Provider, Zufallsdaten, Hashes, Schlüssel, CSR, X.509-Zertifikate, Zertifikatsketten, PKCS#7/PKCS#12, TLS-Diagnose, Signaturen, Verschlüsselung, Konvertierung und sichere Standardabläufe.

> [!warning] Kryptografie ist Kontextarbeit
> Algorithmen, Schlüssellängen, Zertifikatsprofile und Laufzeiten müssen zur PKI-Policy und zum Schutzbedarf passen. Beispiele sind robuste Ausgangspunkte, aber keine pauschale Freigabe. Private Schlüssel niemals in Tickets, Chat, Shell-History oder ungeschützte Backups kopieren.

## Inhalt

- [[#Version, Konfiguration und Provider]]
- [[#Zufallsdaten, Hashes und HMAC]]
- [[#Private und öffentliche Schlüssel]]
- [[#CSR erstellen und prüfen]]
- [[#Zertifikate anzeigen und prüfen]]
- [[#Selbstsignierte Zertifikate und lokale CA]]
- [[#Zertifikatsketten]]
- [[#PKCS12 und PKCS7]]
- [[#Formate konvertieren]]
- [[#TLS-Server prüfen]]
- [[#TLS-Testserver]]
- [[#Signieren und Verifizieren]]
- [[#Symmetrische Dateiverschlüsselung]]
- [[#Schlüssel, CSR und Zertifikat vergleichen]]
- [[#Fehlerdiagnose]]
- [[#Schnellreferenz]]

## Version, Konfiguration und Provider

```bash
openssl version
openssl version -a
openssl help
openssl list -commands
openssl list -providers
openssl list -cipher-algorithms
openssl list -digest-algorithms
openssl list -public-key-algorithms
```

Konfigurationsdateien ermitteln:

```bash
openssl version -d
openssl version -a | grep -Ei 'OPENSSLDIR|MODULESDIR|ENGINESDIR'
```

Hilfe:

```bash
openssl x509 -help
openssl req -help
openssl pkey -help
openssl s_client -help
```

OpenSSL 3 nutzt Provider:

| Provider | Zweck |
|---|---|
| `default` | übliche moderne Algorithmen |
| `base` | grundlegende Kodier-/Hilfsfunktionen |
| `legacy` | alte Verfahren für Migration/Kompatibilität |
| `fips` | validierter Modus bei passender Installation/Policy |

```bash
openssl list -providers -verbose
```

> [!danger]
> Den Legacy-Provider nicht pauschal aktivieren, nur damit alte Dateien „wieder gehen“. Ursache und Migrationsplan dokumentieren.

## Zufallsdaten, Hashes und HMAC

Zufallswerte:

```bash
openssl rand 32
openssl rand -hex 32
openssl rand -base64 32
```

Hashes:

```bash
openssl dgst -sha256 datei.iso
openssl sha256 datei.iso
openssl dgst -sha512 datei.iso
```

Hashdatei prüfen:

```bash
printf '%s  %s\n' 'ERWARTETER_SHA256' 'datei.iso' | sha256sum -c -
```

HMAC:

```bash
openssl dgst -sha256 -hmac 'testschluessel' datei.txt
```

Für echte Geheimnisse nicht als Argument übergeben. Besser Secret-Datei mit restriktiven Rechten oder Secret-Manager verwenden.

## Private und öffentliche Schlüssel

### RSA

```bash
umask 077
openssl genpkey \
  -algorithm RSA \
  -pkeyopt rsa_keygen_bits:3072 \
  -aes-256-cbc \
  -out server-rsa.key
```

Prüfen:

```bash
openssl pkey -in server-rsa.key -check -noout
openssl pkey -in server-rsa.key -text -noout | less
```

### EC

```bash
umask 077
openssl genpkey \
  -algorithm EC \
  -pkeyopt ec_paramgen_curve:P-256 \
  -aes-256-cbc \
  -out server-ec.key
```

### Ed25519 für Signaturen

```bash
openssl genpkey -algorithm ED25519 -out signing-ed25519.key
```

### Öffentlichen Schlüssel extrahieren

```bash
openssl pkey -in server-rsa.key -pubout -out server.pub.pem
openssl pkey -pubin -in server.pub.pem -text -noout
```

Schlüssel ohne Passphrase nur dort, wo der Dienst nicht interaktiv starten kann und Dateirechte/Hostschutz ausreichend sind:

```bash
openssl pkey -in encrypted.key -out unencrypted.key
chmod 600 unencrypted.key
```

> [!warning]
> Eine unverschlüsselte Schlüsseldatei verlagert Schutz vollständig auf Dateirechte, Backup, Host und Prozessgrenzen.

## CSR erstellen und prüfen

### CSR mit SAN über Kommandozeile

```bash
openssl req -new \
  -key server-rsa.key \
  -out server.csr \
  -subj '/C=DE/O=Beispiel GmbH/CN=server.example.org' \
  -addext 'subjectAltName=DNS:server.example.org,DNS:server,IP:192.0.2.10' \
  -addext 'keyUsage=digitalSignature,keyEncipherment' \
  -addext 'extendedKeyUsage=serverAuth'
```

Prüfen:

```bash
openssl req -in server.csr -text -noout
openssl req -in server.csr -verify -noout
openssl req -in server.csr -subject -noout
```

### Reproduzierbar mit Konfigurationsdatei

`server.cnf`:

```ini
[ req ]
prompt = no
distinguished_name = dn
req_extensions = req_ext

[ dn ]
C = DE
O = Beispiel GmbH
CN = server.example.org

[ req_ext ]
subjectAltName = @alt_names
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth

[ alt_names ]
DNS.1 = server.example.org
DNS.2 = server
IP.1 = 192.0.2.10
```

```bash
openssl req -new -key server-rsa.key -out server.csr -config server.cnf
```

> [!important]
> Moderne TLS-Clients prüfen den Hostnamen im SAN. Ein passender Common Name allein reicht nicht als verlässliche Planung.

## Zertifikate anzeigen und prüfen

```bash
openssl x509 -in server.crt -text -noout
openssl x509 -in server.crt -subject -issuer -serial -dates -noout
openssl x509 -in server.crt -fingerprint -sha256 -noout
openssl x509 -in server.crt -ext subjectAltName -noout
openssl x509 -in server.crt -ext keyUsage -ext extendedKeyUsage -noout
```

Ablauf in Sekunden/Tagen prüfen:

```bash
openssl x509 -in server.crt -checkend 86400 -noout
echo $?
```

`0` bedeutet: länger als angegebene Sekunden gültig. `1`: läuft vorher ab oder ist ungültig.

DER:

```bash
openssl x509 -inform DER -in server.cer -text -noout
```

## Selbstsignierte Zertifikate und lokale CA

Kurzlebiges Testzertifikat:

```bash
openssl req -x509 -new \
  -key server-rsa.key \
  -sha256 \
  -days 30 \
  -out server-selfsigned.crt \
  -subj '/CN=server.example.org' \
  -addext 'subjectAltName=DNS:server.example.org' \
  -addext 'basicConstraints=critical,CA:FALSE' \
  -addext 'keyUsage=critical,digitalSignature,keyEncipherment' \
  -addext 'extendedKeyUsage=serverAuth'
```

> [!warning]
> Selbstsigniert ist nicht automatisch unsicher, aber ohne separat verteilten Vertrauensanker nicht vertrauenswürdig. Für mehrere Systeme ist eine korrekt betriebene interne CA besser.

Einfache lokale Root-CA nur für Labor/Entwicklung:

```bash
umask 077
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -aes-256-cbc -out root-ca.key
openssl req -x509 -new -key root-ca.key -sha256 -days 3650 \
  -subj '/C=DE/O=Lab/CN=Lab Root CA' \
  -addext 'basicConstraints=critical,CA:TRUE,pathlen:1' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign' \
  -out root-ca.crt
```

Root-Schlüssel offline halten; für echte PKI Intermediate-CA, Seriennummern, CRL/OCSP, Audit, Rollen und Recovery planen.

## Zertifikatsketten

Kette prüfen:

```bash
openssl verify \
  -CAfile root-ca.crt \
  -untrusted intermediate-ca.crt \
  server.crt
```

Mit Hostname und Zweck:

```bash
openssl verify \
  -CAfile root-ca.crt \
  -untrusted intermediate-ca.crt \
  -verify_hostname server.example.org \
  -purpose sslserver \
  server.crt
```

Fullchain für viele Webserver:

```bash
cat server.crt intermediate-ca.crt > fullchain.pem
```

Typische Serverreihenfolge:

```text
Endzertifikat
Intermediate 1
Intermediate 2
Root normalerweise nicht mitsenden
```

## PKCS12 und PKCS7

### PKCS#12 erzeugen

```bash
openssl pkcs12 -export \
  -out server.p12 \
  -inkey server-rsa.key \
  -in server.crt \
  -certfile intermediate-ca.crt \
  -name 'server.example.org'
```

Anzeigen:

```bash
openssl pkcs12 -in server.p12 -info -noout
```

Zertifikate extrahieren:

```bash
openssl pkcs12 -in server.p12 -clcerts -nokeys -out server.crt.pem
openssl pkcs12 -in server.p12 -cacerts -nokeys -out ca-chain.pem
```

Privaten Schlüssel extrahieren:

```bash
openssl pkcs12 -in server.p12 -nocerts -out server-encrypted.key
openssl pkcs12 -in server.p12 -nocerts -nodes -out server.key
chmod 600 server.key
```

### PKCS#7

```bash
openssl pkcs7 -in response.p7b -print_certs -text -noout
openssl pkcs7 -in response.p7b -print_certs -out chain.pem
openssl pkcs7 -inform DER -in response.p7b -print_certs -out chain.pem
```

## Formate konvertieren

PEM nach DER:

```bash
openssl x509 -in cert.pem -outform DER -out cert.der
```

DER nach PEM:

```bash
openssl x509 -inform DER -in cert.der -out cert.pem
```

PKCS#8:

```bash
openssl pkcs8 -topk8 -in old-rsa.key -out key-pkcs8.pem
openssl pkcs8 -topk8 -nocrypt -in old-rsa.key -out key-pkcs8-unencrypted.pem
```

> [!important]
> Dateiendung garantiert das Encoding nicht. Mit `file`, `head`, und dem passenden OpenSSL-Unterbefehl prüfen.

## TLS-Server prüfen

Standardtest mit SNI:

```bash
openssl s_client \
  -connect server.example.org:443 \
  -servername server.example.org </dev/null
```

Mit Hostname und Trust:

```bash
openssl s_client \
  -connect server.example.org:443 \
  -servername server.example.org \
  -verify_hostname server.example.org \
  -verify_return_error \
  -CAfile firma-ca.pem </dev/null
```

Kette anzeigen:

```bash
openssl s_client -connect server.example.org:443 \
  -servername server.example.org -showcerts </dev/null
```

TLS-Version:

```bash
openssl s_client -connect host:443 -servername host -tls1_2
openssl s_client -connect host:443 -servername host -tls1_3
```

STARTTLS:

```bash
openssl s_client -connect mail.example.org:25 -starttls smtp -servername mail.example.org
openssl s_client -connect mail.example.org:143 -starttls imap -servername mail.example.org
openssl s_client -connect ldap.example.org:389 -starttls ldap
```

OCSP-Stapling:

```bash
openssl s_client -connect host:443 -servername host -status </dev/null
```

Kompakte Zertifikatsinfo:

```bash
openssl s_client -connect host:443 -servername host </dev/null 2>/dev/null \
  | openssl x509 -subject -issuer -dates -fingerprint -sha256 -noout
```

> [!tip]
> Ohne `-servername` testest du bei virtuellen Hosts möglicherweise das falsche Zertifikat.

## TLS-Testserver

```bash
openssl s_server \
  -accept 8443 \
  -cert server.crt \
  -key server-rsa.key \
  -www
```

Mit Kette:

```bash
openssl s_server -accept 8443 \
  -cert server.crt -key server-rsa.key \
  -cert_chain intermediate-ca.crt -www
```

Nur Labor; keine Produktionsanwendung.

## Signieren und Verifizieren

```bash
openssl dgst -sha256 \
  -sign signing.key \
  -out datei.sig \
  datei.bin
```

```bash
openssl dgst -sha256 \
  -verify signing.pub.pem \
  -signature datei.sig \
  datei.bin
```

Ed25519 nutzt je nach Operation andere CLI-Semantik; immer die aktuelle `pkeyutl`-/`dgst`-Dokumentation prüfen.

## Symmetrische Dateiverschlüsselung

```bash
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -in klartext.txt -out geheim.bin
```

```bash
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in geheim.bin -out klartext.txt
```

> [!warning]
> `openssl enc` ist kein vollständiges modernes Containerformat mit komfortabler Metadaten-/Integritätsverwaltung. Für Backups und Datenaustausch eher etablierte Werkzeuge wie age, SOPS, GPG oder verschlüsselte Archiv-/Backupsoftware prüfen.

## Schlüssel, CSR und Zertifikat vergleichen

Algorithmusunabhängig Public Keys hashen:

```bash
openssl pkey -in server.key -pubout -outform DER 2>/dev/null | openssl sha256
openssl req -in server.csr -pubkey -noout 2>/dev/null | \
  openssl pkey -pubin -outform DER 2>/dev/null | openssl sha256
openssl x509 -in server.crt -pubkey -noout 2>/dev/null | \
  openssl pkey -pubin -outform DER 2>/dev/null | openssl sha256
```

Alle drei Werte müssen identisch sein.

## Fehlerdiagnose

| Fehler | Typische Ursache |
|---|---|
| `unable to get local issuer certificate` | Intermediate oder Trust Anchor fehlt |
| `self-signed certificate in certificate chain` | falscher Truststore oder unpassende Kette |
| `certificate has expired` | End-/Intermediate-/Root-Zertifikat abgelaufen |
| `hostname mismatch` | SAN enthält Zielhost nicht |
| `no peer certificate available` | Handshake vor Zertifikatsübertragung gescheitert |
| `bad decrypt` | falsches Passwort/Verfahren oder beschädigte Datei |
| `unsupported` / `legacy` | altes Verfahren/Provider-Migration |
| `key values mismatch` | Schlüssel und Zertifikat gehören nicht zusammen |
| `wrong tag` / ASN.1 | falsches Format oder `-inform` |

Universelle Prüfreihenfolge:

```bash
openssl version -a
file server.crt server.key
openssl x509 -in server.crt -text -noout
openssl pkey -in server.key -check -noout
openssl verify -CAfile root.pem -untrusted intermediate.pem server.crt
openssl s_client -connect host:443 -servername host -showcerts </dev/null
```

## Schnellreferenz

```bash
openssl version -a
openssl rand -hex 32
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out key.pem
openssl req -new -key key.pem -out request.csr
openssl req -in request.csr -text -noout
openssl x509 -in cert.pem -text -noout
openssl verify -CAfile root.pem -untrusted intermediate.pem cert.pem
openssl pkcs12 -in bundle.p12 -info -noout
openssl s_client -connect host:443 -servername host </dev/null
```

## Quellen

- [OpenSSL command line](https://docs.openssl.org/master/man1/openssl/)
- [openssl-pkey](https://docs.openssl.org/master/man1/openssl-pkey/)
- [openssl-req](https://docs.openssl.org/master/man1/openssl-req/)
- [openssl-x509](https://docs.openssl.org/master/man1/openssl-x509/)
- [openssl-verify](https://docs.openssl.org/master/man1/openssl-verify/)
- [openssl-s_client](https://docs.openssl.org/master/man1/openssl-s_client/)
- [openssl-pkcs12](https://docs.openssl.org/master/man1/openssl-pkcs12/)
- [OpenSSL migration guide](https://docs.openssl.org/master/man7/ossl-guide-migration/)

## Verwandte Notizen

- [[Keytool-Premium-Spickzettel]]
- [[HashiCorp-Vault-Premium-Spickzettel]]
- [[OpenBao-Premium-Spickzettel]]
- [[nginx-Premium-Spickzettel]]
- [[Apache-HTTP-Server-Premium-Spickzettel]]
