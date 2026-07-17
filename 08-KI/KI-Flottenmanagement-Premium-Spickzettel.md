---
title: "KI-Flottenmanagement – Premium-Spickzettel"
aliases: ["AI Fleet Management", "LLM Governance", "Multi Model Operations", "LLMOps"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [ki, llmops, governance, agents, routing, observability, security]
source: "https://www.nist.gov/itl/ai-risk-management-framework"
---

# KI-Flottenmanagement – Premium-Spickzettel

> [!abstract] Zweck
> Betriebsreferenz für mehrere KI-Modelle, Anbieter und Agenten: Inventar, Routing, Datenklassen, Identitäten, Budgets, Evals, Prompt-/Modellversionierung, Observability, Rate Limits, Ausfallsicherheit, Prompt-Injection-Schutz, Deprecations und Incident Response.

> [!abstract] Was „Flotte“ bedeutet
> Eine KI-Flotte besteht nicht nur aus Modellen. Dazu gehören Provider, Endpunkte, Gateways, Prompts, Agenten, Tools, Datenquellen, Vektorspeicher, Schlüssel, Budgets, Evals, Logs, Nutzer und Verantwortliche.

> [!danger] Agenten sind privilegierte Software
> Sobald ein Modell Dateien ändern, E-Mails versenden, Tickets schließen, Code deployen oder Datenbanken beschreiben darf, ist es wie ein automatisierter Administrator zu behandeln: Least Privilege, Sandbox, Approval, Audit und Rückfallplan.

## Inhalt

- [[#Zielbild]]
- [[#Flotteninventar]]
- [[#Rollen und Verantwortungen]]
- [[#Datenklassifizierung]]
- [[#Architektur]]
- [[#Modell- und Provider-Routing]]
- [[#Prompt- und Konfigurationsmanagement]]
- [[#Identitäten, Secrets und Berechtigungen]]
- [[#Agenten- und Tool-Governance]]
- [[#Budgets und Quotas]]
- [[#Rate Limits und Queues]]
- [[#Evaluationen und Freigaben]]
- [[#Observability]]
- [[#Verfügbarkeit und Fallbacks]]
- [[#Modelllebenszyklus und Deprecations]]
- [[#Datenschutz und Aufbewahrung]]
- [[#Incident Response]]
- [[#Betriebschecklisten]]
- [[#Schnellreferenz]]

## Zielbild

Ein kontrolliertes System trennt:

```text
Anwendung
   |
   v
AI Gateway / Policy Layer
   +-- Authentisierung und Tenant
   +-- Datenklasse und Redaction
   +-- Modellrouting
   +-- Budget/Rate Limit
   +-- Prompt-/Tool-Policy
   +-- Logging/Metriken
   |
   +--> Provider A / Modell klein
   +--> Provider A / Modell stark
   +--> Provider B / Fallback
   +--> lokales Modell
```

Kein Anwendungsteam sollte beliebige Modelle mit privaten API-Keys und unversionierten Prompts direkt produktiv anbinden.

## Flotteninventar

Mindestens diese Objekte erfassen:

| Objekt | Pflichtfelder |
|---|---|
| Provider | Vertrag, Region, DPA, Statusseite, Owner |
| Modell | ID/Alias, Fähigkeiten, Kontext, Kostenklasse, Lifecycle |
| Endpoint | Region, Netzwerk, Auth, Quotas |
| Anwendung | Zweck, Owner, Kritikalität, Nutzer |
| Prompt | Version, Repository, Freigabe, Datenklasse |
| Agent | Tools, Rechte, Sandbox, Max Turns |
| Tool/MCP | Zielsystem, Aktionen, Auth, Approval |
| Dataset/RAG | Quelle, Rechtsgrundlage, Aktualität, Tenant |
| Evalset | Aufgaben, erwartete Ergebnisse, Risiken |
| Secret | Vault-Pfad, Rotation, Scope, Owner |

Beispiel als YAML:

```yaml
application: ticket-triage
owner: service-desk
criticality: medium
data_class: internal
models:
  primary: fast-classifier-v3
  escalation: reasoning-v2
allowed_regions: [eu]
max_cost_per_request_eur: 0.08
retention_days: 14
tools:
  - jira-read
  - jira-draft-comment
forbidden_actions:
  - close-ticket
  - change-priority-p1
```

## Rollen und Verantwortungen

RACI-Beispiel:

| Aufgabe | Product Owner | AI Platform | Security/DSB | Fachteam |
|---|---|---|---|---|
| Use Case | A | C | C | R |
| Modellfreigabe | C | R/A | C | C |
| Datenklasse | C | C | A | R |
| Prompt | A | C | C | R |
| Produktionsbetrieb | C | A/R | C | R |
| Incident | A | R | R | R |
| Evalset | A | C | C | R |

Kein „KI-Team ist für alles verantwortlich“. Fachliche Richtigkeit bleibt beim Prozess-/Fachverantwortlichen.

## Datenklassifizierung

Beispielklassen:

| Klasse | Beispiele | Erlaubte Ziele |
|---|---|---|
| öffentlich | veröffentlichte Webseiten | freigegebene Standardmodelle |
| intern | Handbücher, interne Tickets | vertraglich freigegebene Endpunkte |
| vertraulich | Quellcode, Kunden-/Personaldaten | EU/private Endpoints, strengere Logs |
| hochsensibel | Secrets, Gesundheits-/Schlüsseldaten | meist nicht an generative Modelle; Spezialfreigabe |

Gateway-Entscheidung:

```text
Datenklasse + Region + Zweck + Vertrag + Modellfähigkeit
-> allow / redact / route private / deny
```

> [!danger] Secrets sind keine Kontextdaten
> API-Keys, private Schlüssel, Passwörter und produktive Tokens niemals „zur Analyse“ an ein Modell senden. Secret-Scanner vor dem Request und Redaction danach einsetzen.

## Architektur

### Zentrale Komponenten

- API Gateway/AI Gateway,
- Identity Provider,
- Policy Engine,
- Secret Manager,
- Model Registry,
- Prompt Registry,
- Eval-/Benchmark-Pipeline,
- Observability,
- Queue/Worker,
- RAG-/Search-Layer,
- Audit Store,
- Cost/FinOps Dashboard.

### Mandantentrennung

- Tenant-ID nicht nur im Prompt, sondern in Auth/Policy.
- Vector Stores und Caches mandantensicher.
- Toolzugriffe mit Tenant-gebundenen Credentials.
- keine Cross-Tenant-Konversationen.
- Logs und Evals ebenfalls trennen.

### Umgebungen

```text
dev -> test/eval -> staging -> production
```

Modelle, Prompts und Toolrechte je Umgebung getrennt. Produktions-Secrets nicht in lokalen Tests.

## Modell- und Provider-Routing

Routingdimensionen:

```text
Aufgabentyp
Komplexität
Datenklasse/Region
Latenz-SLO
Kostenbudget
Modalität
Toolfähigkeit
Verfügbarkeit
Modellfreigabe
```

Beispielpolicy:

```yaml
routes:
  - match: {task: classify, data_class: public}
    target: small-fast
  - match: {task: code_review, data_class: confidential}
    target: private-strong-code
  - match: {task: legal_summary}
    target: strong-long-context
    require_human_review: true
  - match: {contains_secret: true}
    action: deny
```

### Routing nie nur nach Promptlänge

Kurzer Prompt kann eine schwierige Mathematikaufgabe sein; langer Prompt kann einfache Extraktion sein. Klassifikator, Metadaten und Eskalationssignal kombinieren.

### Fallback

Fallback nur auf kompatible Ziele:

- gleiche Datenregion,
- vergleichbare Tool-/Schemafähigkeit,
- freigegebene Datenverarbeitung,
- bekannte Qualitätsgrenze.

Nicht bei Sicherheitsverweigerung automatisch zu einem „weniger strengen“ Modell wechseln.

## Prompt- und Konfigurationsmanagement

Prompts wie Code behandeln:

```text
prompts/
├── ticket-triage/
│   ├── prompt.md
│   ├── schema.json
│   ├── tests.yaml
│   ├── CHANGELOG.md
│   └── metadata.yaml
```

Metadaten:

```yaml
id: ticket-triage
version: 3.2.0
owner: service-desk
approved_models: [small-fast-v4, medium-v2]
data_class: internal
reviewed: 2026-07-10
expires: 2026-10-10
```

SemVer-ähnlich:

- Major: Ausgabe/Verhalten inkompatibel,
- Minor: neue Fähigkeit,
- Patch: Klarstellung ohne erwartete Schemaänderung.

Jede Änderung durch Evalset, Peer Review und Canary.

## Identitäten, Secrets und Berechtigungen

### Keine gemeinsamen API-Keys

Pro Anwendung/Umgebung:

```text
ticket-triage-prod
code-review-staging
research-dev
```

Rechte:

- nur benötigte Modelle/Endpoints,
- hartes Budget,
- IP/VPC-Einschränkung,
- kurze Rotation,
- Audit,
- Notfallwiderruf.

Secrets aus Vault/Cloud Secret Manager zur Laufzeit injizieren. Nicht in Git, Images, Promptdateien oder Notebookausgaben.

### Service-to-Service

Bevorzugt:

- Workload Identity/OIDC,
- kurzlebige Tokens,
- mTLS, wo sinnvoll,
- signierte Requests,
- zentrale Policy.

## Agenten- und Tool-Governance

Tools nach Risiko klassifizieren:

| Klasse | Beispiele | Regel |
|---|---|---|
| Read-only | Suche, Logs lesen | automatisch, eingeschränkter Scope |
| Reversibel write | Draft, Branch, Ticketkommentar | Sandbox/Review |
| Extern wirksam | E-Mail senden, PR mergen | Human Approval |
| Destruktiv | Löschen, DB-Migration, Firewall | gesonderte Freigabe, oft verboten |
| Hochprivilegiert | IAM, Secrets, Produktion | engste Allowlist/MFA/Break-glass |

### Toolvertrag

Jedes Tool braucht:

- eindeutigen Namen,
- präzise Beschreibung,
- striktes Eingabeschema,
- Grenzen,
- idempotente Operationen,
- Fehlercodes,
- maximale Ausgabe,
- Redaction,
- Audit-ID.

Schlecht:

```text
run_command(command: string)
```

Besser:

```text
restart_service(host_id, service_name, change_ticket_id, dry_run)
```

### Human-in-the-Loop

Freigabedialog zeigt:

```text
Was wird geändert?
Wo?
Mit welcher Identität?
Welche Daten verlassen das System?
Wie wird rückgängig gemacht?
Welche Evidenz stützt die Aktion?
```

### Prompt Injection

- untrusted Inhalte markieren,
- Toolauswahl nicht durch Dokumenttext steuern lassen,
- Allowlist statt freie URLs/Commands,
- Secrets nie im Modellkontext,
- Egress einschränken,
- Toolresultate validieren,
- Canary-Secrets/DLP zur Erkennung.

## Budgets und Quotas

Mehrstufig:

```text
Organisation
 -> Business Unit
   -> Anwendung
     -> Nutzer/Tenant
       -> Request/Workflow
```

Grenzen:

- monatliches Kostenbudget,
- Tageslimit,
- Requests/min,
- Tokens/min,
- maximale Outputtokens,
- maximale Agent-Turns,
- maximale Toolcalls,
- maximale Parallelität.

Beispiel:

```yaml
budget:
  monthly_eur: 2500
  alert_at_percent: [50, 75, 90, 100]
  hard_stop_percent: 110
workflow:
  max_cost_eur: 2.50
  max_turns: 15
  max_tool_calls: 30
  max_duration_seconds: 600
```

> [!warning] Alarm ist kein Limit
> Ein Dashboard verhindert keine Kostenexplosion. Providerquota, Gatewaylimit und Workflowbudget technisch durchsetzen.

## Rate Limits und Queues

Fehlerklassen unterscheiden:

| Typ | Reaktion |
|---|---|
| 429/Quota | `Retry-After`, Backoff, Queue |
| 5xx temporär | begrenzter Retry, Circuit Breaker |
| 4xx Prompt/Schema | nicht blind wiederholen |
| Safety/Policy | nicht auf schwächere Policy ausweichen |
| Timeout | Idempotenz prüfen, Status abfragen |

Backoff:

```text
wait = min(cap, base * 2^attempt) + random_jitter
```

Queueattribute:

- Request-ID,
- Tenant,
- Priorität,
- Deadline,
- Versuchszahl,
- Modellklasse,
- Kostenbudget,
- Deduplizierungsschlüssel.

Dead-Letter Queue analysieren statt endlos erneut senden.

## Evaluationen und Freigaben

### Evalset

Enthält:

- normale Fälle,
- Grenzfälle,
- mehrdeutige Fälle,
- adversariale Prompt-Injection,
- Datenleak-Tests,
- Toolfehler,
- veraltete Fakten,
- Nichtbeantwortbarkeit.

Bewertung:

```text
fachliche Korrektheit
Schemaerfüllung
Quellenqualität
Sicherheitsverletzungen
Toolauswahl
Kosten
Latenz
Stabilität
```

### Gates

```text
Unit/Schema Tests
 -> Offline Evals
 -> Security Tests
 -> Shadow Traffic
 -> Canary 1–5 %
 -> gestufter Rollout
 -> vollständige Freigabe
```

Rollback auf vorherige Kombination aus:

```text
Modell + Prompt + Tools + Retrievalindex + Policy
```

Nur Modell-ID zurückzusetzen genügt nicht immer.

## Observability

### Metriken

- Requests und Tokens,
- Cachetreffer,
- Kosten,
- Latenz p50/p95/p99,
- Fehler nach Klasse,
- Toolcalls,
- Agent-Turns,
- Queue-Länge,
- Fallbackrate,
- Safety-Blockrate,
- Schemafehler,
- menschliche Korrekturen,
- Evalscore.

### Tracing

Ein Trace verbindet:

```text
User Request
-> Router
-> Retrieval
-> Model Call 1
-> Tool Call
-> Model Call 2
-> Approval
-> External Action
```

Trace-ID in Logs und Toolaktionen propagieren.

### Logging

Stufen:

```text
Metadaten standardmäßig
redigierte Inhalte nur bei Bedarf
Rohinhalt nur mit Rechtsgrundlage, Zugriffskontrolle und kurzer TTL
```

Keine Tokens/Secrets im Klartext.

## Verfügbarkeit und Fallbacks

SLO-Beispiele:

```text
99,9 % Gateway-Verfügbarkeit
p95 < 5 s für Klassifikation
95 % Tasks ohne menschliche Nacharbeit
```

Resilienz:

- Providerstatus überwachen,
- Circuit Breaker,
- Multi-Region nur datenschutzkonform,
- kompatibler Zweitprovider,
- Queue statt Drop,
- degradiertes read-only Verhalten,
- statische Fallbackantwort für kritische Services,
- Kill Switch für Agentaktionen.

Nicht alle Workflows brauchen Multi-Provider. Komplexität und Qualitätsabweichung abwägen.

## Modelllebenszyklus und Deprecations

Modelle werden geändert, umbenannt oder abgeschaltet.

Registryfelder:

```yaml
model_id: provider/model-version
status: approved
released: 2026-05-01
deprecation_announced: null
shutdown: null
replacement: null
last_eval: 2026-07-01
```

Prozess:

1. Release Notes automatisiert beobachten.
2. Alias nicht als unveränderliche Version behandeln.
3. Deprecation in Ticket/Alarm umsetzen.
4. Ersatzmodell gegen Evalset testen.
5. Prompt-/Schemaanpassungen versionieren.
6. Canary.
7. Altmodell vor Shutdown entfernen.

> [!danger] „latest“ in Produktion
> Ein beweglicher Alias kann Verhalten ohne eigenen Deployment-Commit ändern. Für kritische Workflows versionierte Modell-IDs oder kontrollierte Freigabe verwenden, soweit Anbieter dies unterstützt.

## Datenschutz und Aufbewahrung

Für jeden Datenfluss dokumentieren:

- Verantwortlicher/Auftragsverarbeiter,
- Region,
- Zweck,
- Datenkategorien,
- Training/Abuse Monitoring,
- Retention,
- Subprozessoren,
- Löschprozess,
- Betroffenenrechte,
- grenzüberschreitende Übermittlung.

RAG-Daten:

- Quelle und Löschstatus synchronisieren,
- Berechtigungen beim Retrieval anwenden,
- veraltete Chunks entfernen,
- personenbezogene Daten minimieren,
- Embeddings als potenziell schutzbedürftig behandeln.

## Incident Response

### Mögliche Incidents

- Secret im Prompt/Log,
- Cross-Tenant-Leak,
- Agent führt falsche Aktion aus,
- Kostenexplosion,
- Modell liefert systematisch falsche Klassifikation,
- Prompt-Injection mit Toolmissbrauch,
- Providerregion/Vertrag falsch,
- unerwarteter Modellwechsel.

### Sofortmaßnahmen

```text
1. Kill Switch / Route deaktivieren
2. Credentials widerrufen
3. Toolrechte entziehen
4. betroffene Prompts/Logs sichern und Zugriff begrenzen
5. Scope über Trace-/Request-IDs bestimmen
6. Datenschutz/Security nach Prozess einbinden
7. sicheren Fallback aktivieren
8. Nutzer/Betroffene nach Vorgabe informieren
```

### Forensik

Sichern:

- Modell-ID und Konfiguration,
- Promptversion,
- Tooldefinitionen,
- Request-/Trace-ID,
- redigierte Eingaben/Ausgaben,
- Approval-Entscheidung,
- externe Aktion und Rückgabecode,
- Registry-/Policy-Version,
- Zeitstempel in UTC.

## Betriebschecklisten

### Neuer Use Case

- [ ] Owner und Zweck
- [ ] Datenklasse/Region/Rechtsgrundlage
- [ ] Modell- und Tool-Allowlist
- [ ] Budget/SLO
- [ ] Evalset und Sicherheitsfälle
- [ ] Logging/Retention
- [ ] Human Approval
- [ ] Rollback/Kill Switch
- [ ] Dokumentation und Schulung

### Modellwechsel

- [ ] Release Notes/Deprecation
- [ ] Kosten und Context Window
- [ ] Tool-/Schema-Kompatibilität
- [ ] Offline-Evals
- [ ] Safety/Injection-Evals
- [ ] Shadow/Canary
- [ ] Dashboards/Alerts
- [ ] Rollback getestet

### Wöchentlicher Betrieb

- [ ] Kostenabweichungen
- [ ] Cache-/Fallback-/Retryrate
- [ ] neue Fehlercluster
- [ ] Prompt-/Modelländerungen
- [ ] offene Deprecations
- [ ] ungewöhnliche Toolaktionen
- [ ] DLP/Secret-Funde
- [ ] Eval-Drift

## Schnellreferenz

```text
Inventar -> Datenklasse -> Gateway/Policy -> Least Privilege
-> Routing -> Budgets -> Evals -> Canary -> Observability
-> Deprecation-Prozess -> Kill Switch -> Incident Response
```

Goldene Regeln:

```text
Kein Modell ohne Owner.
Kein Prompt ohne Version.
Kein Tool ohne Schema und Rechtebegrenzung.
Kein Agent ohne Budget und Abbruchbedingung.
Kein Rollout ohne Eval und Rollback.
Keine sensiblen Daten ohne dokumentierten Datenfluss.
```

## Quellen
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
- [OpenAI – Production Best Practices](https://platform.openai.com/docs/guides/production-best-practices)
- [Anthropic – Reduce Latency and Cost](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Google Gemini – Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)

## Verwandte Notizen
- [[KI-Prompts-Premium-Spickzettel]]
- [[KI-Token-sparen-Premium-Spickzettel]]
- [[Codex-Premium-Spickzettel]]
- [[Claude-Premium-Spickzettel]]
- [[Gemini-Premium-Spickzettel]]
- [[HashiCorp Vault – Premium-Spickzettel]]
