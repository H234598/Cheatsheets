---
title: "OpenBao – Premium-Spickzettel"
aliases: ["OpenBao Cheatsheet", "Bao CLI", "OpenBao Operations"]
created: 2026-07-16
modified: 2026-07-17
type: reference
status: fertig
origin: "Premium Spickzettel I – vollständig überarbeitet"
reviewed: 2026-07-17
tags: [openbao, secrets-management, pki, transit, kv, security, linux-foundation]
source: "https://openbao.org/docs/"
---

# OpenBao – Premium-Spickzettel

> [!abstract] Zweck
> Betriebsreferenz für OpenBao: CLI, HCL-Konfiguration, Seal/Unseal, Tokens, Policies, KV v2, Auth Methods, Audit, Transit, PKI, Integrated Storage/Raft, Snapshots, Recovery und Migration von Vault.

> [!important] Eigenständiges Projekt
> OpenBao ging aus dem offen lizenzierten Vault-Code hervor und wird unter dem Dach der Linux Foundation weiterentwickelt. Viele Konzepte und APIs ähneln Vault, aber Versionen, Plugins, Features und Migrationsregeln dürfen nicht blind gleichgesetzt werden.

> [!note] Versionsstand
> Zum Recherchestand war die aktuelle Dokumentationslinie **2.6.x**; ältere Linien sind separat gekennzeichnet. Vor Betrieb und Migration immer die Dokumentation der exakten Version verwenden.

## Inhalt

- [[#CLI und Umgebungsvariablen]]
- [[#Serverkonfiguration]]
- [[#Initialisierung und Unseal]]
- [[#Login und Tokens]]
- [[#Policies und Capabilities]]
- [[#KV v2]]
- [[#Auth Methods und AppRole]]
- [[#Audit]]
- [[#Transit und PKI]]
- [[#Integrated Storage und Raft]]
- [[#Snapshots und Recovery]]
- [[#Migration von Vault]]
- [[#Upgrade und Betrieb]]
- [[#Diagnose und Härtung]]
- [[#Schnellreferenz]]

## CLI und Umgebungsvariablen

```bash
bao version
bao -help
bao status
```

```bash
export BAO_ADDR='https://bao.example.org:8200'
export BAO_CACERT='/etc/ssl/certs/firma-ca.pem'
```

Ausgabe:

```bash
bao status -format=json
bao kv get -format=json secret/app
bao kv get -field=password secret/app
bao path-help secret/data/app
```

> [!warning]
> TLS-Prüfung nicht dauerhaft deaktivieren. Interne CA über `BAO_CACERT` oder System-Truststore korrekt einrichten.

## Serverkonfiguration

`/etc/openbao/openbao.hcl`:

```hcl
ui = true
api_addr     = "https://bao-1.example.org:8200"
cluster_addr = "https://bao-1.example.org:8201"

storage "raft" {
  path    = "/opt/openbao/data"
  node_id = "bao-1"
}

listener "tcp" {
  address         = "0.0.0.0:8200"
  cluster_address = "0.0.0.0:8201"
  tls_cert_file   = "/etc/openbao/tls/server.crt"
  tls_key_file    = "/etc/openbao/tls/server.key"
}

telemetry {
  prometheus_retention_time = "30s"
}
```

Start:

```bash
bao server -config=/etc/openbao/openbao.hcl
```

Dev-Mode:

```bash
bao server -dev
```

> [!danger]
> Dev-Mode ist nicht für Produktion. Er ist initialisiert/entsiegelt und verwendet absichtlich vereinfachte Annahmen.

Konfiguration nach Möglichkeit verifizieren:

```bash
bao server -config=/etc/openbao/openbao.hcl -verify-only
```

Ob die Option in der konkreten Version vorhanden ist, mit `bao server -help` prüfen.

## Initialisierung und Unseal

```bash
umask 077
bao operator init -format=json > openbao-init.json
bao status
```

Manuell:

```bash
bao operator unseal
```

> [!danger]
> Init-Datei, Key-Shares und Initial-Root-Token getrennt und verschlüsselt verwahren. Recovery regelmäßig üben.

Rekey/Root-Recovery sinngemäß:

```bash
bao operator rekey -init
bao operator generate-root -init
```

Auto-Unseal nur mit dokumentierter IAM-/KMS-/HSM-Vertrauenskette.

## Login und Tokens

```bash
bao login
bao login -method=oidc
bao login -method=userpass username='alice'
bao token lookup
```

```bash
bao token create \
  -policy='app-read' \
  -ttl='1h' \
  -renewable=true

bao token renew
bao token revoke TOKEN
bao token revoke -accessor ACCESSOR
```

Root-Token nicht im Tagesbetrieb. Workloads mit kurzlebiger Authentisierung.

## Policies und Capabilities

```hcl
path "secret/data/app/prod" {
  capabilities = ["read"]
}

path "secret/metadata/app/prod" {
  capabilities = ["read", "list"]
}
```

```bash
bao policy fmt app-read.hcl
bao policy write app-read app-read.hcl
bao policy read app-read
bao token capabilities secret/data/app/prod
```

Gesamteffekt mit realen Rollen testen; KV-v2-`data`/`metadata` unterscheiden.

## KV v2

```bash
bao secrets list -detailed
bao secrets enable -path=secret kv-v2
```

```bash
bao kv put secret/app/prod username='svc-app' password='...'
bao kv get secret/app/prod
bao kv patch secret/app/prod username='svc-app-v2'
```

Versionen:

```bash
bao kv metadata get secret/app/prod
bao kv get -version=2 secret/app/prod
bao kv delete -versions=2 secret/app/prod
bao kv undelete -versions=2 secret/app/prod
bao kv destroy -versions=2 secret/app/prod
```

> [!danger]
> `destroy` ist irreversibel. Vor automatischen Retention-Jobs Restore- und Rechtsanforderungen prüfen.

## Auth Methods und AppRole

```bash
bao auth list -detailed
bao auth enable oidc
bao auth enable approle
bao auth enable kubernetes
```

```bash
bao write auth/approle/role/app \
  token_policies='app-read' \
  token_ttl='15m' \
  token_max_ttl='1h' \
  secret_id_ttl='10m' \
  secret_id_num_uses=1

bao read auth/approle/role/app/role-id
bao write -f auth/approle/role/app/secret-id
bao write auth/approle/login role_id='...' secret_id='...'
```

RoleID und SecretID getrennt verteilen; Wrapping/Einmalverwendung bevorzugen.

## Audit

```bash
bao audit enable file file_path=/var/log/openbao_audit.log
bao audit list -detailed
```

Audit Device muss dauerhaft schreibbar, rotiert und überwacht sein. Auditdaten sind sensibel und benötigen Zugriffsschutz/Retention.

## Transit und PKI

Transit:

```bash
bao secrets enable transit
bao write -f transit/keys/app-key
PLAINTEXT=$(printf '%s' 'geheim' | base64 -w0)
bao write transit/encrypt/app-key plaintext="$PLAINTEXT"
```

```bash
bao write -field=plaintext transit/decrypt/app-key \
  ciphertext='bao:v1:...' | base64 -d
```

Das tatsächliche Ciphertext-Präfix versionsabhängig beobachten, nicht fest verdrahten.

PKI:

```bash
bao secrets enable pki
bao secrets tune -max-lease-ttl=87600h pki
```

Für reale Infrastruktur Root-CA offline und OpenBao als Intermediate. Rollen, TTLs, CRL/OCSP, AIA/CDP und Issuer-Rotation planen.

```bash
bao write pki/roles/web \
  allowed_domains='example.org' \
  allow_subdomains=true \
  max_ttl='720h'

bao write pki/issue/web common_name='app.example.org' ttl='168h'
```

## Integrated Storage und Raft

```bash
bao operator raft list-peers
bao operator raft autopilot state
bao operator raft join https://bao-1.example.org:8200
```

HA-Grundlagen:

- ungerade Zahl stimmberechtigter Knoten;
- geringe, stabile Latenz;
- Failure Domains verteilen;
- Cluster-/API-Adressen korrekt;
- TLS zwischen Knoten;
- Quorum und Disk Space überwachen;
- keine manuelle Dateikopie des Raft-Verzeichnisses als Backup.

## Snapshots und Recovery

```bash
bao operator raft snapshot save openbao-$(date +%F).snap
sha256sum openbao-*.snap
chmod 600 openbao-*.snap
```

Restore:

```bash
bao operator raft snapshot restore openbao-2026-07-17.snap
```

> [!danger]
> Restore nur mit passender Version, Seal-Konfiguration, Wartungsfenster, Rückfallplan und getestetem Runbook.

Recovery Mode ist ein spezieller Notfallmodus für begrenzte Reparaturfälle. Nur nach exakter Versionsdokumentation und mit gesicherter Evidenz verwenden; er ist kein allgemeiner Administrationsersatz.

## Migration von Vault

Migration ist kein Umbenennen des Binaries.

### Inventar

```text
Vault- und Zielversion
Edition/Enterprise-Funktionen
Storage und HA
Seal/Auto-Unseal
Auth Methods
Secrets Engines
Plugins
Namespaces/Replication
Policies/Identity
Agents/Terraform/SDK/API-Clients
Audit/Monitoring/Backups
```

### Vorprüfung

```text
[ ] offizielle Migrationsmatrix für konkrete Versionen
[ ] inkompatible Enterprise-Daten/Plugins geklärt
[ ] vollständiger Snapshot und getesteter Restore
[ ] Staging-Kopie
[ ] Downtime und Rollback
[ ] Client-/Provider-Kompatibilität
[ ] API-/CLI-Namenswechsel
[ ] Akzeptanztests
```

### Akzeptanztests

```bash
bao status
bao secrets list -detailed
bao auth list -detailed
bao policy list
bao audit list
bao operator raft list-peers
```

Danach exemplarisch:

```text
Login jeder Auth-Methode
KV lesen/schreiben/versionieren
Dynamisches Secret und Lease-Renewal
Transit encrypt/decrypt
PKI-Ausstellung und Revocation
Token-Widerruf
Auditkorrelation
HA-Failover
Snapshot/Restore in Testumgebung
```

> [!danger]
> Proprietäre Vault-Enterprise-Daten oder externe Plugins können direkte Migration verhindern. Offizielle OpenBao-Migrationsdokumentation ist maßgeblich.

## Upgrade und Betrieb

Vor Upgrade:

- Release Notes und Sicherheitsmeldungen;
- alle Zwischenversionen;
- Storage-/Seal-/Plugin-Kompatibilität;
- Snapshot/Restore-Test;
- Staging und Rollbackgrenze;
- Client-Kompatibilität;
- Change-Fenster/Monitoring.

Keine alte Versionsanleitung auf neue Cluster anwenden, nur weil CLI-Befehle ähnlich aussehen.

## Diagnose und Härtung

| Symptom | Prüfen |
|---|---|
| Verbindung abgelehnt | Dienst, `BAO_ADDR`, Listener, Firewall |
| TLS-Vertrauensfehler | CA, SAN, Zeit, Zertifikatskette |
| `permission denied` | Token, Policy, Pfad, Auth-Rolle |
| Server sealed | KMS/Auto-Unseal oder Key-Shares |
| `no handler for route` | Mount, API-/KV-v2-Pfad |
| Raft-Node fehlt | Join, Clusteradresse, TLS, Peerstatus |
| Snapshot-Fehler | Leader, Rechte, Speicher, Version |

```bash
bao status
journalctl -u openbao -b
bao operator raft list-peers
bao operator raft autopilot state
```

Produktionscheck:

```text
[ ] TLS-Prüfung aktiv
[ ] kein Dev-Mode
[ ] Root-Token nicht im Alltag
[ ] Least-Privilege-Policies
[ ] kurzlebige Workload-Identitäten
[ ] überwachte Audit Devices
[ ] Raft/HA und Quorum getestet
[ ] Snapshot/Restore regelmäßig getestet
[ ] NTP und Zertifikatsalarm
[ ] Upgrades zuerst Staging
[ ] Incident-/Break-Glass-Runbook
```

## Schnellreferenz

```bash
bao version
bao status
bao login
bao secrets list -detailed
bao auth list -detailed
bao policy list
bao kv put secret/app key=value
bao kv get secret/app
bao token lookup
bao audit list
bao operator raft list-peers
bao operator raft snapshot save openbao.snap
```

## Quellen

- [OpenBao Documentation](https://openbao.org/docs/)
- [OpenBao CLI](https://openbao.org/docs/commands/)
- [Server configuration](https://openbao.org/docs/configuration/)
- [Integrated Storage](https://openbao.org/docs/configuration/storage/raft/)
- [Raft commands](https://openbao.org/docs/commands/operator/raft/)
- [Recovery mode](https://openbao.org/docs/concepts/recovery-mode/)
- [OpenBao GitHub](https://github.com/openbao/openbao)

## Verwandte Notizen

- [[HashiCorp-Vault-Premium-Spickzettel]]
- [[OpenSSL-Premium-Spickzettel]]
- [[Keytool-Premium-Spickzettel]]
- [[KI-Flottenmanagement-Premium-Spickzettel]]
