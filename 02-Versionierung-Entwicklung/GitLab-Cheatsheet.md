---
title: "GitLab – Cheatsheet"
aliases: ["GitLab Cheatsheet", "GitLab CI CD", "GitLab Merge Requests"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [gitlab, git, ci-cd, merge-request, runner, devops]
source: "https://docs.gitlab.com/"
---

# GitLab – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für GitLab: Projekte, Merge Requests, Issues, CI/CD, Runner, Variablen, Releases, Berechtigungen, Self-Managed-Betrieb und Diagnose.

> [!note]
> GitLab-Version, Lizenzstufe und Betriebsmodell beeinflussen verfügbare Funktionen. Bei Self-Managed-Instanzen zusätzlich lokale Administratorrichtlinien und Versionsdokumentation beachten.

## Inhalt

- [[#Authentisierung und Projektzugriff]]
- [[#Merge-Request-Workflow]]
- [[#Issues, Epics und Boards]]
- [[#GitLab CI/CD]]
- [[#Runner]]
- [[#Variablen und Secrets]]
- [[#Environments, Deployments und Releases]]
- [[#Berechtigungen und geschützte Ressourcen]]
- [[#Self-Managed-Betrieb]]
- [[#glab-CLI]]
- [[#Diagnose]]

## Authentisierung und Projektzugriff

### SSH

```bash
ssh-keygen -t ed25519 -a 64 -C 'name@example.org'
ssh -T git@gitlab.example.org
git clone git@gitlab.example.org:gruppe/projekt.git
```

### Token

Tokenarten unterscheiden:

| Typ | Zweck |
|---|---|
| Personal Access Token | Benutzerautomation; minimaler Scope/Ablauf |
| Project Access Token | projektgebundene Automation |
| Group Access Token | gruppenweite Automation |
| Deploy Token | Registry/Repositoryzugriff für Deployments |
| CI Job Token | kurzlebiger Jobkontext |
| Trigger Token | Pipelineauslösung; wie Secret behandeln |

Langfristige persönliche Tokens in CI möglichst vermeiden. Projekt-/Gruppentoken, Job Token oder OIDC/Federation bevorzugen.

### Rollen

Typische Abstufung:

```text
Minimal Access → Guest → Planner/Reporter → Developer → Maintainer → Owner
```

Die genaue Rollenmengung kann versionsabhängig sein. Minimal notwendige Rolle vergeben und regelmäßige Rezertifizierung durchführen.

## Merge-Request-Workflow

```bash
git switch -c feature/issue-123
git add -p
git commit -m 'feat: Validierung ergänzen'
git push -u origin feature/issue-123
```

Beim Push kann GitLab eine URL zum Erstellen des Merge Requests ausgeben. Alternativ Weboberfläche oder `glab`:

```bash
glab mr create --fill --draft
glab mr view --web
glab mr checkout 123
glab mr diff 123
glab mr approve 123
```

### MR-Checkliste

```markdown
## Ziel
...

## Änderungen
- ...

## Tests
- [ ] Unit
- [ ] Integration
- [ ] manuell

## Deployment/Migration
...

## Risiko/Rollback
...

Closes #123
```

### Mergeoptionen

- Mergecommit
- Mergecommit mit semi-linearer Historie
- Fast-forward
- Squash
- Rebase, je Projekteinstellung

Branchstrategie, Commitqualität und Releaseprozess gemeinsam definieren.

## Issues, Epics und Boards

### Sinnvolle Struktur

- **Issue:** umsetzbare Arbeitseinheit oder Fehler
- **Epic:** größere Initiative, je Lizenz/Version
- **Milestone:** zeitliche oder Release-Zuordnung
- **Board:** Sicht auf Workflow/Labels
- **Iteration:** Sprint-/Zeitbox, sofern eingesetzt

Labels orthogonal halten:

```text
type::bug       type::feature
priority::1     priority::2
workflow::ready workflow::doing workflow::review
area::api       area::platform
```

Scoped Labels (`dimension::wert`) verhindern konkurrierende Werte derselben Dimension.

## GitLab CI/CD

Minimale `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - build

workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

unit-test:
  stage: test
  image: python:3.13-slim
  script:
    - python -m pip install -r requirements.txt
    - python -m pytest
  cache:
    key:
      files:
        - requirements.txt
    paths:
      - .cache/pip

build:
  stage: build
  script:
    - ./scripts/build.sh
  artifacts:
    paths:
      - dist/
    expire_in: 7 days
```

### `rules` statt unübersichtlicher Mischlogik

```yaml
job:
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
      when: on_success
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      changes:
        - src/**/*
    - when: never
```

> [!warning]
> `only/except` und `rules` nicht leichtfertig im selben Job mischen. Doppelte Branch- und MR-Pipelines über `workflow: rules` kontrollieren.

### Needs/DAG

```yaml
build:
  stage: build
  needs: [unit-test]
```

`needs` kann Jobs früher starten, sobald Abhängigkeiten fertig sind, unabhängig von kompletter Stufe.

### Includes und Vorlagen

```yaml
include:
  - local: .gitlab/ci/test.yml
  - project: platform/ci-templates
    ref: v3.2.0
    file: /python/base.yml
```

Externe Vorlagen auf immutable Tag oder Commit pinnen und Änderungen reviewen.

## Runner

Runnerarten:

| Typ | Einsatz |
|---|---|
| Instance Runner | für viele Projekte der Instanz |
| Group Runner | begrenzt auf Gruppe |
| Project Runner | einzelnes Projekt |
| Hosted Runner | von GitLab bereitgestellt, je Angebot |

Executors können unter anderem Shell, Docker oder Kubernetes sein.

### Sicherheitsprinzipien

- untrusted Jobs nicht auf privilegierten Runnern ausführen
- Shell Executor als Zugriff auf Runnerhost behandeln
- Docker `privileged` nur zwingend und isoliert
- Runner-Tags und geschützte Runner einsetzen
- kurzlebige/ephemere Runner bevorzugen
- Cache und Workspace zwischen Vertrauensdomänen trennen
- Registrierungstoken/Authentifizierungstoken schützen
- Netzwerk-Egress minimieren

Runnerstatus bei Self-Managed:

```bash
sudo gitlab-runner status
sudo gitlab-runner verify
sudo gitlab-runner list
sudo journalctl -u gitlab-runner -n 200 --no-pager
```

## Variablen und Secrets

Ebenen:

- Instance
- Group
- Project
- Environment
- Pipeline/Trigger
- Job

Eigenschaften:

- **Masked:** Wert wird nach Regeln in Logs maskiert
- **Protected:** nur geschützte Branches/Tags
- **Environment scope:** nur bestimmte Umgebung
- **File variable:** Wert als temporäre Datei bereitgestellt

> [!danger]
> Maskierung verhindert nicht jede Exfiltration durch bösartigen Jobcode. CI mit Secretzugriff darf nur vertrauenswürdigen Code und geschützte Auslöser ausführen.

Bevorzugen:

- OIDC/Workload Identity für Cloudzugriff
- externen Secret Manager
- kurzlebige Credentials
- getrennte Produktionsumgebung mit Genehmigung

## Environments, Deployments und Releases

```yaml
deploy-staging:
  stage: deploy
  environment:
    name: staging
    url: https://staging.example.org
  script:
    - ./deploy.sh staging
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
```

Manuelle Produktion:

```yaml
deploy-production:
  stage: deploy
  environment:
    name: production
  script:
    - ./deploy.sh production
  when: manual
  allow_failure: false
  rules:
    - if: '$CI_COMMIT_TAG'
```

Zusätzlich geschützte Umgebung, Freigaberegeln und minimale Deploy-Rechte konfigurieren.

Release über CLI/API je Umgebung; Artefakte, Changelog, SBOM, Signaturen und Rollback dokumentieren.

## Berechtigungen und geschützte Ressourcen

Schützen:

- Default Branch
- Releasebranches
- Tags nach Muster `v*`
- CI/CD-Variablen
- Runner
- Environments
- Package/Container Registry

Kontrollpunkte:

- wer darf pushen?
- wer darf mergen?
- wie viele Approvals?
- Code Owner erforderlich?
- Autor darf selbst genehmigen?
- neue Commits setzen Approval zurück?
- erfolgreiche Pipeline erforderlich?
- Security-/License-Checks blockierend?

## Self-Managed-Betrieb

### Kernkomponenten grob

```text
NGINX/Workhorse → Rails/Puma → PostgreSQL
                    │
                    ├→ Sidekiq/Redis
                    ├→ Gitaly/Repositories
                    └→ Object Storage/Registry/Pages
```

### Omnibus/Linux-Paket Schnellreferenz

```bash
sudo gitlab-ctl status
sudo gitlab-ctl reconfigure
sudo gitlab-ctl tail
sudo gitlab-ctl restart <dienst>
sudo gitlab-rake gitlab:check SANITIZE=true
sudo gitlab-rake gitlab:env:info
```

> [!danger]
> `reconfigure`, Upgrade und Restore sind betriebsweite Eingriffe. Versionspfad, Backup, Migrationsdauer, Geo/HA und Rückfallplan vorab prüfen.

Backup typischerweise:

```bash
sudo gitlab-backup create
```

Konfiguration und Secrets separat sichern, zum Beispiel `/etc/gitlab` nach offizieller Betriebsanleitung.

## glab-CLI

```bash
glab auth login
glab repo clone gruppe/projekt
glab issue list
glab issue create
glab mr list
glab mr create --fill
glab mr checks 123
glab pipeline list
glab ci view
glab release create v2.1.0
```

Verfügbarkeit einzelner Unterbefehle mit `glab help` und installierter Version prüfen.

## Diagnose

### Pipeline wird nicht erzeugt

1. YAML linten.
2. `workflow: rules` prüfen.
3. Job-`rules` und Variablen für tatsächlichen Pipeline Source prüfen.
4. Include-Referenzen erreichbar?
5. CI-Konfiguration in GitLab-Editor/CI Lint simulieren.

### Job hängt auf „pending“

- passender aktiver Runner vorhanden?
- Runner-Tags stimmen vollständig?
- Runner für Projekt/Gruppe aktiviert?
- geschützter Branch versus geschützter Runner?
- Kapazität/Concurrency/Quota?
- Runner-Log und Netzwerkzugriff?

### Clone/Push verweigert

```bash
ssh -vT git@gitlab.example.org
git remote -v
git branch -vv
```

Rolle, Branchschutz, SSO, Schlüssel/Token, Namespace und Speicherquota prüfen.

### Self-Managed langsam/Fehler 5xx

```bash
sudo gitlab-ctl status
sudo gitlab-ctl tail nginx/gitlab_error.log
sudo gitlab-ctl tail puma
sudo gitlab-ctl tail sidekiq
sudo gitlab-rake gitlab:check SANITIZE=true
```

Dann CPU/RAM/IO, PostgreSQL, Redis, Gitaly, Queue-Länge, Object Storage, Zertifikate und letzte Änderungen korrelieren.

## Quellen
- [GitLab Docs](https://docs.gitlab.com/)
- [GitLab CI/CD YAML reference](https://docs.gitlab.com/ci/yaml/)
- [GitLab Runner documentation](https://docs.gitlab.com/runner/)
- [GitLab permissions and roles](https://docs.gitlab.com/user/permissions/)

## Verwandte Notizen
- [[Git-Cheatsheet]]
- [[GitHub-Cheatsheet]]
- [[nginx-Cheatsheet]]
- [[Ruby-on-Rails-Cheatsheet]]
