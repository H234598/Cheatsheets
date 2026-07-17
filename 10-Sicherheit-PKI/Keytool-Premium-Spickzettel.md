---
title: "Keytool – Premium-Spickzettel für Java-Keystores"
aliases: ["Keytool Cheatsheet", "Java Keystore Spickzettel", "PKCS12 und JKS verwalten"]
created: 2026-07-16
modified: 2026-07-17
type: reference
status: fertig
origin: "Premium Spickzettel I – vollständig überarbeitet"
reviewed: 2026-07-17
tags: [java, keytool, pki, zertifikate, keystore, jks, pkcs12, tls, security]
source: "https://docs.oracle.com/en/java/javase/25/docs/specs/man/keytool.html"
---

# Keytool – Premium-Spickzettel für Java-Keystores

> [!abstract] Zweck
> Referenz für Java `keytool`: PKCS#12/JKS, Schlüsselpaare, CSR, Zertifikate, Truststores, Import/Export, Konvertierung, Aliase, Passwörter, System-Truststore und Fehlerdiagnose. Gegen Java SE 25 gegengeprüft; konkrete JVM-Version beachten.

> [!warning] Vor jeder Änderung sichern
> Viele Befehle ändern die Datei unmittelbar.
>
> ```bash
> cp server.p12 server.p12.bak.$(date +%F-%H%M%S)
> ```

## Inhalt

- [[#Grundbegriffe und Formate]]
- [[#Hilfe und sichere Passwortübergabe]]
- [[#Schlüsselpaar und Keystore anlegen]]
- [[#Keystore prüfen]]
- [[#CSR erzeugen und prüfen]]
- [[#Zertifikate prüfen und importieren]]
- [[#Zertifikate exportieren]]
- [[#Keystores mergen und konvertieren]]
- [[#Aliase und Passwörter]]
- [[#Einträge löschen]]
- [[#Java-System-Truststore]]
- [[#Standardabläufe]]
- [[#OpenSSL-Interoperabilität]]
- [[#Fehlerdiagnose]]
- [[#Schnellreferenz]]

## Grundbegriffe und Formate

| Begriff | Bedeutung |
|---|---|
| Keystore | Datei mit Schlüsseln, Zertifikaten und/oder Secrets |
| Truststore | Keystore, der primär vertrauenswürdige CA-Zertifikate enthält |
| Alias | eindeutiger Name eines Eintrags |
| `PrivateKeyEntry` | privater Schlüssel plus Zertifikatskette |
| `trustedCertEntry` | Vertrauensanker/Zertifikat ohne privaten Schlüssel |
| `SecretKeyEntry` | symmetrischer Schlüssel |
| CSR | Zertifikatsantrag mit öffentlichem Schlüssel |
| PKCS#12 | standardisiertes Format, `.p12`/`.pfx` |
| JKS | älteres Java-spezifisches Format |

> [!tip]
> Für neue Keystores meist PKCS#12 verwenden. JKS nur bei konkreter Kompatibilitätsanforderung.

## Hilfe und sichere Passwortübergabe

```bash
keytool -help
keytool -genkeypair --help
keytool -importcert --help
keytool -importkeystore --help
keytool -J-version
java -version
```

Passwörter nicht ungeprüft in Kommandozeilenargumenten speichern. Je nach Befehl unterstützt `keytool` Passwortquellen wie:

```text
-storepass:env VARIABLENNAME
-storepass:file DATEI
-keypass:env VARIABLENNAME
```

Beispiel:

```bash
export KEYSTORE_PASS='...'
keytool -list -keystore server.p12 -storepass:env KEYSTORE_PASS
unset KEYSTORE_PASS
```

> [!warning]
> Umgebungsvariablen sind nicht in jeder Umgebung geheim. Für CI einen Secret Store und kurzlebige Runner verwenden.

## Schlüsselpaar und Keystore anlegen

### RSA mit SAN

```bash
keytool -genkeypair \
  -alias server \
  -keyalg RSA \
  -keysize 3072 \
  -sigalg SHA256withRSA \
  -validity 365 \
  -keystore server.p12 \
  -storetype PKCS12 \
  -dname 'CN=server.example.org,O=Firma,C=DE' \
  -ext 'SAN=dns:server.example.org,dns:server,ip:192.0.2.10' \
  -ext 'KU=digitalSignature,keyEncipherment' \
  -ext 'EKU=serverAuth'
```

### EC

```bash
keytool -genkeypair \
  -alias server-ec \
  -keyalg EC \
  -groupname secp256r1 \
  -sigalg SHA256withECDSA \
  -keystore server-ec.p12 \
  -storetype PKCS12 \
  -dname 'CN=server.example.org,O=Firma,C=DE' \
  -ext 'SAN=dns:server.example.org'
```

> [!note]
> `-validity` betrifft hier das zunächst erzeugte Zertifikat. Bei externer CA bestimmt die CA die endgültige Laufzeit/Extensions.

## Keystore prüfen

```bash
keytool -list -keystore server.p12
keytool -list -v -keystore server.p12
keytool -list -v -alias server -keystore server.p12
keytool -list -rfc -alias server -keystore server.p12
```

Store-Typ ausdrücklich:

```bash
keytool -list -v -storetype PKCS12 -keystore server.p12
```

Wichtige Prüfpunkte:

```text
Entry type = PrivateKeyEntry?
Alias korrekt?
Subject und Issuer?
SAN vollständig?
Key Usage / Extended Key Usage?
Gültigkeit?
SHA-256-Fingerprint?
Kettenlänge und Reihenfolge?
```

## CSR erzeugen und prüfen

```bash
keytool -certreq \
  -alias server \
  -keystore server.p12 \
  -file server.csr \
  -rfc \
  -ext 'SAN=dns:server.example.org,dns:server,ip:192.0.2.10' \
  -ext 'KU=digitalSignature,keyEncipherment' \
  -ext 'EKU=serverAuth'
```

```bash
keytool -printcertreq -v -file server.csr
```

Mit OpenSSL gegenprüfen:

```bash
openssl req -in server.csr -text -verify -noout
```

> [!important]
> Der private Schlüssel bleibt im Keystore. Die CA-Antwort muss zum öffentlichen Schlüssel genau dieses Alias passen.

## Zertifikate prüfen und importieren

Datei prüfen:

```bash
keytool -printcert -v -file server.cer
keytool -printcert -rfc -file server.cer
```

TLS-Server:

```bash
keytool -printcert -sslserver server.example.org:443
```

Signierte JAR:

```bash
keytool -printcert -jarfile anwendung.jar
```

CA in Truststore:

```bash
keytool -importcert \
  -alias firma-root-ca \
  -file root-ca.cer \
  -keystore truststore.p12 \
  -storetype PKCS12
```

CA-Antwort für vorhandenen Schlüssel:

```bash
keytool -importcert \
  -alias server \
  -file server-response.p7b \
  -keystore server.p12
```

> [!danger] Alias muss stimmen
> Die CA-Antwort gehört unter denselben Alias, aus dem der CSR erzeugt wurde. Ein Zertifikat ersetzt keinen verlorenen privaten Schlüssel.

Nichtinteraktiv nur mit vorher validiertem Fingerprint:

```bash
keytool -importcert -noprompt -trustcacerts \
  -alias firma-root-ca -file root-ca.cer \
  -keystore truststore.p12
```

> [!warning]
> `-noprompt` überspringt die Vertrauensfrage. Herkunft/Fingerprint vorher auf unabhängigem Kanal prüfen.

## Zertifikate exportieren

PEM:

```bash
keytool -exportcert \
  -alias server \
  -keystore server.p12 \
  -rfc \
  -file server.crt.pem
```

DER:

```bash
keytool -exportcert \
  -alias server \
  -keystore server.p12 \
  -file server.crt.der
```

Private Schlüssel exportiert `keytool` nicht direkt als PEM. Dafür gesamten Eintrag über PKCS#12 übertragen und mit OpenSSL extrahieren.

## Keystores mergen und konvertieren

Kompletten Store importieren:

```bash
keytool -importkeystore \
  -srckeystore quelle.p12 \
  -srcstoretype PKCS12 \
  -destkeystore ziel.p12 \
  -deststoretype PKCS12
```

Bestimmten Alias:

```bash
keytool -importkeystore \
  -srckeystore quelle.p12 \
  -srcalias server \
  -destkeystore ziel.p12 \
  -destalias produktiv-server
```

JKS nach PKCS#12:

```bash
keytool -importkeystore \
  -srckeystore alt.jks \
  -srcstoretype JKS \
  -destkeystore neu.p12 \
  -deststoretype PKCS12
```

Vorher und nachher:

```bash
keytool -list -v -keystore alt.jks
keytool -list -v -keystore neu.p12 -storetype PKCS12
```

> [!warning]
> Alias-Konflikte, unterschiedliche Passwörter und Provider-Kompatibilität vor Massenmigration testen.

## Aliase und Passwörter

Alias ändern:

```bash
keytool -changealias \
  -alias alter-name \
  -destalias neuer-name \
  -keystore server.p12
```

Store-Passwort:

```bash
keytool -storepasswd -keystore server.p12
```

Schlüsselpasswort:

```bash
keytool -keypasswd -alias server -keystore server.jks
```

Bei PKCS#12 verlangen viele Implementierungen ein einheitliches Passwort für Store und Schlüssel.

## Einträge löschen

```bash
keytool -delete -alias server -keystore server.p12
keytool -delete -alias firma-root-ca -keystore truststore.p12
```

> [!danger]
> Beim Löschen eines `PrivateKeyEntry` verschwinden privater Schlüssel und Kette. Vorher Backup und Aliasprüfung.

Store-Datei löschen ist eine normale Dateisystemoperation:

```bash
rm -- server.p12
```

## Java-System-Truststore

```bash
keytool -list -cacerts
keytool -list -v -cacerts
```

CA hinzufügen:

```bash
keytool -importcert -cacerts \
  -alias firma-root-ca \
  -file root-ca.cer
```

Entfernen:

```bash
keytool -delete -cacerts -alias firma-root-ca
```

> [!important]
> System-`cacerts` wird bei JDK-Updates ersetzt oder unterscheidet sich zwischen Runtimes. Für Anwendungen oft expliziten, versionierten Truststore verwenden.

Runtime-Truststore prüfen:

```bash
readlink -f "$(command -v java)"
java -XshowSettings:properties -version 2>&1 | grep -E 'java.home|java.version'
```

## Standardabläufe

### Neues Serverzertifikat über CA

```bash
# 1. Schlüssel/Keystore
keytool -genkeypair -alias server -keyalg RSA -keysize 3072 \
  -keystore server.p12 -storetype PKCS12 \
  -dname 'CN=server.example.org,O=Firma,C=DE' \
  -ext 'SAN=dns:server.example.org'

# 2. CSR
keytool -certreq -alias server -keystore server.p12 \
  -file server.csr -rfc -ext 'SAN=dns:server.example.org'

# 3. CSR prüfen
keytool -printcertreq -v -file server.csr

# 4. CA-Antwort importieren
keytool -importcert -alias server \
  -file server-response.p7b -keystore server.p12

# 5. Ergebnis prüfen
keytool -list -v -alias server -keystore server.p12
```

### Eigener Truststore

```bash
keytool -importcert -alias firma-root-ca \
  -file root-ca.pem \
  -keystore truststore.p12 \
  -storetype PKCS12

keytool -list -v -keystore truststore.p12
```

Anwendung:

```bash
java \
  -Djavax.net.ssl.trustStore=/opt/app/truststore.p12 \
  -Djavax.net.ssl.trustStoreType=PKCS12 \
  -jar app.jar
```

Passwort nicht als sichtbares Prozessargument behandeln; anwendungsspezifische Secret-Konfiguration verwenden.

## OpenSSL-Interoperabilität

PKCS#12 anzeigen:

```bash
openssl pkcs12 -in server.p12 -info -noout
```

Zertifikat und Schlüssel extrahieren:

```bash
openssl pkcs12 -in server.p12 -clcerts -nokeys -out server.crt.pem
openssl pkcs12 -in server.p12 -nocerts -out server.key.pem
```

Zertifikatskette prüfen:

```bash
openssl verify -CAfile root.pem -untrusted intermediate.pem server.crt.pem
```

## Fehlerdiagnose

### Public-Key-Mismatch

```text
Public keys in reply and keystore don't match
```

Ursachen:

- CSR aus anderem Store/Alias;
- Schlüssel nach CSR ersetzt;
- falsche CA-Antwort;
- falscher Alias;
- Endzertifikat/CA-Kette verwechselt.

Prüfen:

```bash
keytool -list -v -alias server -keystore server.p12
keytool -printcert -v -file server-response.cer
```

Mismatch nicht „erzwingen“; richtige CA-Antwort oder neuen CSR verwenden.

### Alias fehlt

```bash
keytool -list -keystore server.p12
```

### Passwort/Format

```text
Keystore was tampered with, or password was incorrect
```

```bash
file server.p12
keytool -list -v -storetype PKCS12 -keystore server.p12
openssl pkcs12 -in server.p12 -info -noout
```

### Kette unvollständig

```bash
keytool -list -v -alias server -keystore server.p12
```

Kettenlänge, Issuer/Subject und Intermediate prüfen.

### TLS der Java-Anwendung

Nur kurzfristig und ohne Geheimnisse in gemeinsamem Log:

```bash
java -Djavax.net.debug=ssl,handshake,trustmanager -jar app.jar
```

> [!warning]
> TLS-Debuglogs können Zertifikate, Hostnamen und sensible Metadaten enthalten und sehr groß werden.

## Schnellreferenz

| Aufgabe | Befehl |
|---|---|
| Schlüsselpaar | `keytool -genkeypair` |
| CSR | `keytool -certreq` |
| CSR prüfen | `keytool -printcertreq` |
| Zertifikat prüfen | `keytool -printcert` |
| Zertifikat importieren | `keytool -importcert` |
| Zertifikat exportieren | `keytool -exportcert` |
| Store anzeigen | `keytool -list` |
| Store migrieren | `keytool -importkeystore` |
| Alias ändern | `keytool -changealias` |
| Eintrag löschen | `keytool -delete` |
| System-Truststore | `keytool -list -cacerts` |

## Quellen

- [Oracle Java SE 25: keytool](https://docs.oracle.com/en/java/javase/25/docs/specs/man/keytool.html)
- [JSSE Reference Guide](https://docs.oracle.com/en/java/javase/25/security/java-secure-socket-extension-jsse-reference-guide.html)
- [OpenSSL PKCS#12](https://docs.openssl.org/master/man1/openssl-pkcs12/)

## Verwandte Notizen

- [[OpenSSL-Premium-Spickzettel]]
- [[HashiCorp-Vault-Premium-Spickzettel]]
- [[OpenBao-Premium-Spickzettel]]
- [[nginx-Premium-Spickzettel]]
- [[Apache-HTTP-Server-Premium-Spickzettel]]
