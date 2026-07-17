---
title: "OpenAI Codex – Premium-Spickzettel"
aliases: ["Codex Cheatsheet", "Codex CLI", "OpenAI Coding Agent", "Codex Cloud"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [ki, openai, codex, coding-agent, cli, softwareentwicklung, git, security]
source: "https://developers.openai.com/codex/"
---

# OpenAI Codex – Premium-Spickzettel

> [!abstract] Zweck
> Praxisreferenz für Codex als Coding-Agent in Terminal, IDE, ChatGPT Desktop und Cloud: Installation, Projektvorbereitung, Modelle, Prompts, `AGENTS.md`, Konfiguration, Berechtigungen, Sandboxing, Git-Workflows, MCP, Diagnose, Tokenkontrolle und sicherer Betrieb.

> [!important] Stand
> Produktoberflächen, Modellnamen, Limits und Tarifzuordnung ändern sich schnell. Diese Seite ist auf den **17. Juli 2026** datiert. Vor automatisierten oder produktiven Abläufen Release Notes, lokale Version und Organisationsrichtlinien prüfen.

## Inhalt

- [[#Produktlandkarte]]
- [[#Installation und Anmeldung]]
- [[#Modelle und Arbeitsmodi]]
- [[#Projekt sicher vorbereiten]]
- [[#Sitzungen und Kernbefehle]]
- [[#Gute Arbeitsaufträge]]
- [[#Planen, Implementieren und Prüfen]]
- [[#AGENTS.md und Projektregeln]]
- [[#Konfiguration]]
- [[#Berechtigungen, Sandbox und Netzwerk]]
- [[#Git- und Review-Workflow]]
- [[#MCP und externe Werkzeuge]]
- [[#Cloud-Aufgaben und Parallelisierung]]
- [[#Kontext und Token sparen]]
- [[#Sicherheitscheckliste]]
- [[#Fehlerdiagnose]]
- [[#Schnellreferenz]]

## Produktlandkarte

```text
Codex
├── CLI                         interaktiv im Terminal
├── IDE-Erweiterung             Editor-Kontext und Änderungen im Projekt
├── ChatGPT Desktop – Codex     mehrere Aufgaben, Diffs und Arbeitsbereiche
├── Web/Cloud-Aufgaben          isolierte Remote-Ausführung und Reviews
└── SDK/Integrationen           programmatische Einbindung je Produktstand
```

Wichtige Trennung:

| Ebene | Typischer Zugang | Abrechnung/Identität |
|---|---|---|
| ChatGPT/Codex-Produkt | ChatGPT-Konto | Plan- und Organisationslimits |
| OpenAI API | API-Schlüssel/Projekt | separate API-Abrechnung und Limits |
| Git-Hosting | GitHub/GitLab-Zugang | eigene Berechtigungen und Tokens |
| MCP/Tools | jeweiliger Dienst | eigener Trust- und Rechtebereich |

> [!warning]
> Ein ChatGPT-Abonnement ist nicht automatisch dasselbe wie API-Guthaben. Ebenso überträgt eine Codex-Anmeldung keine GitHub-, Cloud- oder Datenbankrechte, solange diese nicht separat konfiguriert wurden.

> [!note] Desktop-Änderung vom 9. Juli 2026
> Die frühere eigenständige Codex-App wurde in die **ChatGPT-Desktop-App für macOS und Windows** integriert. Dort bleibt Codex als eigener Arbeitsbereich erhalten. Ältere Anleitungen und Changelogs können weiterhin von der „Codex-App“ sprechen.

## Installation und Anmeldung

Offizieller Installer für macOS/Linux/WSL, sofern auf der aktuellen Codex-Seite weiterhin angeboten:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Danach:

```bash
codex --version
codex --help
codex
```

Bei der ersten Ausführung im Browser mit dem vorgesehenen Konto anmelden. In verwalteten Umgebungen können SSO, Richtlinien oder API-basierte Anmeldung vorgegeben sein.

Aktualisierung und installierten Pfad prüfen:

```bash
command -v codex
type -a codex
codex --version
```

Shell-Vervollständigung gemäß Hilfe der installierten Version aktivieren:

```bash
codex completion --help
```

> [!tip]
> Vor Supportanfragen immer `codex --version`, Betriebssystem, Shell, Repository-Commit und den genauen Startbefehl dokumentieren.

## Modelle und Arbeitsmodi

Die aktuelle Codex-Modellfamilie ist nach Einsatzprofilen gegliedert:

| Modell | Schwerpunkt | Typische Aufgaben |
|---|---|---|
| **GPT-5.6 Sol** | maximale Tiefe und Qualität | komplexe Änderungen, Architektur, schwierige Fehlersuche, Research, hochwertige Dokumentation |
| **GPT-5.6 Terra** | ausgewogener Allrounder | tägliche Entwicklung, Reviews, Refactoring und Tool-Workflows |
| **GPT-5.6 Luna** | Geschwindigkeit und geringere Kosten | klar definierte, wiederholbare oder volumenstarke Aufgaben |

Explizite Auswahl in der CLI, sofern für Konto und installierte Version verfügbar:

```bash
codex -m gpt-5.6-sol
codex -m gpt-5.6-terra
codex -m gpt-5.6-luna
```

Praxisregel:

```text
unklar/hochwertig   -> Sol
alltägliche Arbeit  -> Terra
klar/oft/wiederholbar -> Luna
```

Reasoning beziehungsweise Arbeitsintensität so niedrig wie möglich und so hoch wie nötig wählen. **Max** eignet sich nur für besonders schwierige Einzelaufgaben; **Ultra** zerlegt geeignete Aufgaben auf mehrere Subagenten und verbraucht entsprechend mehr Kontingent.

> [!important]
> Modellverfügbarkeit hängt von ChatGPT-Plan, Workspace-Richtlinien, Oberfläche, Region, Rollout und API-Projekt ab. Nicht darauf vertrauen, dass ein heute sichtbarer Modellalias dauerhaft unverändert bleibt; Modell und Agentversion bei reproduzierbaren Abläufen protokollieren.

## Projekt sicher vorbereiten

### Vor dem ersten Agentenlauf

```bash
git status --short
git branch --show-current
git remote -v
git log -1 --oneline
```

Empfohlener Ablauf:

```bash
git switch -c codex/ticket-123
# oder in einem separaten Worktree
git worktree add ../projekt-ticket-123 -b codex/ticket-123
```

Prüfen:

- ist das Repository vertrauenswürdig?
- enthält das Arbeitsverzeichnis private Schlüssel, Dumps oder `.env`-Dateien?
- sind Build- und Testbefehle bekannt?
- darf ein Agent Netzwerk, Paketmanager oder Cloud-CLI verwenden?
- ist ein Rollback über Git oder Snapshot möglich?
- gibt es `AGENTS.md`, `README`, `CONTRIBUTING` und lokale Regeln?

### Minimale Projektinventur

```bash
find . -maxdepth 2 -type f | sort | sed -n '1,200p'
git ls-files | sed -n '1,200p'
```

Nicht ungeprüft das gesamte Home-Verzeichnis als Arbeitsbereich öffnen. Ein klar begrenztes Repository reduziert Datenabfluss und Fehlbedienung.

## Sitzungen und Kernbefehle

Interaktiv starten:

```bash
cd /pfad/zum/repository
codex
```

Eine frühere Sitzung wieder aufnehmen:

```bash
codex resume
```

Bild als Kontext übergeben, sofern von der installierten Version unterstützt:

```bash
codex --image fehlerdialog.png
```

Websuche explizit aktivieren, sofern benötigt und erlaubt:

```bash
codex --search
```

Cloud-Kommandos erkunden:

```bash
codex cloud --help
```

In der interaktiven Oberfläche:

```text
/permissions   aktuellen Berechtigungsmodus prüfen/ändern
/help          verfügbare Kommandos anzeigen
```

Die konkrete Liste kann je Version variieren; die eingebaute Hilfe ist maßgeblich.

## Gute Arbeitsaufträge

### Robuste Promptstruktur

```text
Ziel:
Kontext:
Relevante Dateien:
Nicht ändern:
Akzeptanzkriterien:
Tests/Prüfung:
Ausgabeformat:
```

Beispiel:

```text
Ziel: Behebe den NullPointer-Fehler beim Import leerer CSV-Dateien.
Kontext: Java-21-Projekt, Maven, Spring Boot.
Relevante Dateien: src/main/java/.../CsvImporter.java und vorhandene Tests.
Nicht ändern: öffentliche REST-API und Datenbankschema.
Akzeptanzkriterien:
1. Leere Datei ergibt eine fachliche ValidationException.
2. Bestehende gültige Imports bleiben unverändert.
3. Regressionstest ergänzen.
Prüfung: mvn -q test.
Arbeite zuerst nur mit einem Plan und nenne Unsicherheiten.
```

### Bewährte Auftragsarten

**Repository erklären:**

```text
Analysiere die Architektur. Nenne Einstiegspunkte, Datenfluss,
Konfigurationspfade, externe Abhängigkeiten und die fünf wichtigsten Risiken.
Ändere noch nichts.
```

**Fehler reproduzieren:**

```text
Reproduziere den Fehler zuerst mit einem minimalen Test.
Zeige Ursache und betroffene Invariante. Implementiere erst danach den kleinsten Fix.
```

**Review:**

```text
Prüfe den Diff gegen main auf Korrektheit, Sicherheit, Nebenläufigkeit,
Abwärtskompatibilität und fehlende Tests. Priorisiere Findings nach Schweregrad.
```

**Refactoring:**

```text
Refaktoriere ohne beobachtbare Verhaltensänderung.
Lege vorab Sicherungstests an und halte jeden Commit klein und rücksetzbar.
```

> [!warning]
> „Mach alles besser“ ist kein belastbarer Auftrag. Unklare Ziele erzeugen große Diffs, unnötige Abhängigkeiten und schwer prüfbare Entscheidungen.

## Planen, Implementieren und Prüfen

Empfohlenes Drei-Phasen-Muster:

```text
1. PLAN: Dateien, Hypothese, Risiken, Tests, keine Änderungen
2. PATCH: kleinste zielgerichtete Änderung
3. VERIFY: Tests, Linter, Diff, Sicherheits- und Randfallprüfung
```

Beispielanweisung:

```text
Beginne mit einer Bestandsaufnahme und einem maximal zehn Punkte langen Plan.
Warte nicht auf Bestätigung, wenn der Plan eindeutig ist. Implementiere danach
in kleinen Schritten, führe die relevanten Tests aus und fasse den finalen Diff zusammen.
```

Kontrollpunkte:

```bash
git diff --stat
git diff --check
git diff --word-diff
```

Tests abhängig vom Projekt:

```bash
npm test
pytest -q
cargo test
mvn test
go test ./...
```

> [!tip]
> Einen grünen Testlauf nicht blind akzeptieren. Prüfen, ob der neue Test vor dem Fix tatsächlich fehlschlägt und ob die richtige Testmenge ausgeführt wurde.

## AGENTS.md und Projektregeln

`AGENTS.md` dient als dauerhafter Projektkontext. Typische Inhalte:

```markdown
# AGENTS.md

## Projekt
- Python 3.13, FastAPI, PostgreSQL
- Paketmanager: uv

## Befehle
- Setup: `uv sync --frozen`
- Tests: `uv run pytest -q`
- Lint: `uv run ruff check .`
- Typen: `uv run mypy src`

## Regeln
- Keine neuen Laufzeitabhängigkeiten ohne Begründung.
- Keine Schemaänderung ohne Migration.
- Öffentliche APIs rückwärtskompatibel halten.
- Geheimnisse nie in Logs oder Fixtures schreiben.

## Definition of Done
- Tests und Linter grün
- relevante Dokumentation aktualisiert
- Diff frei von Debug-Ausgaben
```

Hierarchie beachten: globale, Repository- und unterverzeichnisspezifische Anweisungen können zusammenwirken. Regeln so nah wie sinnvoll an den betroffenen Code legen, aber Widersprüche vermeiden.

Gute Regeln sind:

- konkret und testbar,
- kurz genug, um tatsächlich gelesen zu werden,
- ohne Geheimnisse,
- im Repository reviewbar,
- mit korrekten Befehlen und Pfaden.

## Konfiguration

Benutzerkonfiguration:

```text
~/.codex/config.toml
```

Projektkonfiguration kann unterhalb von `.codex/` liegen. Organisationsrichtlinien können lokale Werte übersteuern.

Beispiel:

```toml
# ~/.codex/config.toml
model = "gpt-5.6"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "disabled"

[history]
persistence = "save-all"
```

> [!note]
> `gpt-5.6` ist hier ein zeitgebundenes Beispiel vom 17. Juli 2026. Verfügbare Modell-IDs mit aktueller Dokumentation und Organisationsfreigabe abgleichen.

Typische Priorität:

```text
CLI-Optionen
> Projektkonfiguration
> Profil
> Benutzerkonfiguration
> System-/Organisationskonfiguration
> Standardwerte
```

Konfiguration prüfen:

```bash
sed -n '1,240p' ~/.codex/config.toml
find . -path '*/.codex/*' -type f -maxdepth 4 -print
```

Keine Tokens oder Passwörter in versionierte TOML-Dateien schreiben.

## Berechtigungen, Sandbox und Netzwerk

### Grundmodell

```text
Modellvorschlag
    ↓
Tool-/Shell-Anforderung
    ↓
Policy + Sandbox + Benutzerfreigabe
    ↓
Ausführung
```

Typischer sicherer Standard:

```text
sandbox_mode = workspace-write
approval_policy = on-request
Netzwerk = aus oder explizit begrenzt
```

Bedeutung:

- Lesen und Schreiben bleiben auf erlaubte Pfade begrenzt.
- Riskante oder außerhalb des Bereichs liegende Aktionen benötigen Freigabe.
- Netzwerkzugriff ist eine eigene Fähigkeit und nicht mit Dateischreibrecht gleichzusetzen.
- Cloud-Setup- und Agentenphase können unterschiedliche Netzwerk-/Secret-Regeln haben.

### Besonders kritisch

- `sudo`, `su`, Systemdienste und Paketmanager
- `rm -rf`, Massenersetzungen, `git clean -fdx`
- Produktionsdatenbanken und Cloud-CLIs
- Deployment, DNS, Firewall und IAM
- Zugriff auf `$HOME`, SSH-Schlüssel, Browserprofile und Secret Stores
- Download und Ausführung fremder Installationsskripte

> [!danger] Vollständige Umgehung
> Optionen wie `--dangerously-bypass-approvals-and-sandbox` beziehungsweise Aliasformen wie `--yolo` entfernen wesentliche Schutzschichten. Nicht auf dem normalen Arbeitsplatz, nicht mit Produktionszugängen und nicht in unbekannten Repositorys einsetzen. Für autonome Tests eher eine wegwerfbare VM oder einen gehärteten Container mit minimalen Credentials verwenden.

### Freigaben sinnvoll beurteilen

Vor „Allow“:

1. vollständigen Befehl lesen,
2. Arbeitsverzeichnis prüfen,
3. Globbing, Pipes und Umleitungen verstehen,
4. Datenziel und Netzwerkkontakt erkennen,
5. erwartete Nebenwirkungen benennen können,
6. bei Unsicherheit ablehnen und eine ungefährliche Alternative verlangen.

## Git- und Review-Workflow

### Vorher

```bash
git status --short
git fetch --all --prune
git switch -c codex/kurze-beschreibung
```

### Währenddessen

```bash
git diff
git diff --check
git status --short
```

### Nachher

```bash
# Tests ausführen
git diff --stat
git diff --name-status
git diff --check
```

Commit erst nach eigener Prüfung:

```bash
git add -p
git commit -m 'fix: leere CSV-Dateien fachlich ablehnen'
```

> [!important]
> Nicht ungeprüft `git add .`, automatisch generierte Lockfiles, Migrationen oder Binärdateien committen. `git add -p` macht unerwartete Änderungen sichtbar.

### Reviewauftrag für einen Agenten

```text
Bewerte ausschließlich den Diff von origin/main...HEAD.
Nenne zuerst konkrete Fehler mit Datei und Zeile, danach Risiken und fehlende Tests.
Keine Stilpräferenzen als Fehler ausgeben. Ändere nichts.
```

## MCP und externe Werkzeuge

Model Context Protocol kann externe Systeme als Tools bereitstellen, etwa:

- Dokumentationssuche,
- Ticket- oder Git-Systeme,
- Datenbanken,
- Browser/Automation,
- interne APIs.

Risiken:

```text
Prompt Injection + überbreite Toolrechte + sensibles Ziel = hoher Schaden
```

Prüfen:

- Herkunft und Wartung des Servers,
- exakte Tools und Schemas,
- Leserechte versus Schreibrechte,
- Netzwerkziele,
- Secret-Bereitstellung,
- Logging/Retention,
- Mandantentrennung,
- Abbruch- und Widerrufsmöglichkeit.

Gute Praxis:

- read-only zuerst,
- getrennte Servicekonten,
- kurze Tokenlaufzeit,
- Allowlist für Tools und Hosts,
- keine generischen „execute arbitrary SQL/shell“-Tools,
- menschliche Freigabe für externe Änderungen.

## Cloud-Aufgaben und Parallelisierung

Cloud-Aufgaben eignen sich für isolierbare Arbeiten wie:

- Tests auf einem fixierten Commit,
- unabhängige Buganalysen,
- Dokumentations- oder Migrationsentwürfe,
- parallele Lösungsvorschläge,
- reproduzierbare Evals.

Vorher festlegen:

```text
Commit/SHA
Setup-Skript
Netzwerkzugriff
Secrets
Testbefehl
Zeit-/Kostenbudget
Ausgabeformat
Artefakte
```

> [!warning]
> Parallelität vervielfacht nicht nur Geschwindigkeit, sondern auch Kosten, Logvolumen und Konflikte. Aufgaben nach Dateien oder unabhängigen Hypothesen schneiden und nie mehrere Agenten unkoordiniert denselben Branch ändern lassen.

## Kontext und Token sparen

- nur relevante Pfade öffnen,
- große Logs mit `tail`, `grep` oder Zeitfenster eingrenzen,
- Binärdateien und Build-Verzeichnisse ausschließen,
- problembezogene Zusammenfassung statt vollständigem Chatverlauf,
- Akzeptanzkriterien einmal klar definieren,
- nach Kontextwechsel neue Sitzung beginnen,
- Ergebnisse in `AGENTS.md`, Issue oder kurze Notiz überführen,
- zuerst lokalisieren, dann gezielt Dateien lesen.

Beispiel:

```bash
rg -n 'NullPointerException|CsvImporter' src test
sed -n '120,230p' src/main/java/.../CsvImporter.java
tail -n 200 logs/app.log
```

Agentenanweisung:

```text
Lies zunächst nur README, AGENTS.md, Builddatei und die direkt betroffenen Dateien.
Fordere weitere Dateien nur bei einer konkreten Hypothese an.
```

## Sicherheitscheckliste

```text
[ ] Repository und Abhängigkeiten vertrauenswürdig
[ ] separater Branch oder Worktree
[ ] keine Produktions-Secrets im Arbeitsbereich
[ ] Sandbox workspace-begrenzt
[ ] Netzwerk standardmäßig aus/begrenzt
[ ] MCP-Server und Tools geprüft
[ ] keine pauschale Dauerfreigabe riskanter Shellbefehle
[ ] Tests, Diff und erzeugte Artefakte selbst geprüft
[ ] externe Aktionen mit Human Approval
[ ] Logs vor Weitergabe bereinigt
[ ] Rollback vorhanden
```

## Fehlerdiagnose

### Codex startet nicht

```bash
command -v codex
codex --version
echo "$PATH"
type -a codex
```

Shell neu starten, Installationspfad und Architektur prüfen.

### Anmeldung hängt

- Systemzeit und TLS prüfen,
- Browser/Popup/Proxy kontrollieren,
- Organisationskonto und SSO-Richtlinie prüfen,
- VPN oder SSL-Inspection berücksichtigen,
- keine Tokens in Tickets posten.

### Agent sieht Dateien nicht

```bash
pwd
git rev-parse --show-toplevel
find . -maxdepth 2 -type f | head -100
```

Arbeitsbereich, Ignore-Regeln, Sandbox und Dateirechte prüfen.

### Schreibzugriff verweigert

```bash
ls -ld .
namei -l pfad/zur/datei
```

Dann Sandboxmodus, Mounts, Eigentümer und Read-only-Worktree prüfen. Nicht reflexartig mit `sudo` starten.

### Tests funktionieren im Terminal, nicht im Agentenlauf

```bash
env | sort > /tmp/env-shell.txt
# entsprechende Agentenumgebung ausgeben lassen und vergleichen
```

PATH, virtuelle Umgebung, Working Directory, Secrets, Submodule, Container und Netzwerkzugriff vergleichen.

### Zu große oder falsche Änderung

```bash
git diff --stat
git diff --name-only
git restore -p
```

Auftrag enger formulieren, Patch aufteilen oder Branch zurücksetzen.

## Schnellreferenz

```text
Vorher: git status → Branch/Worktree → Secrets entfernen → AGENTS.md prüfen
Auftrag: Ziel + Kontext + Nicht ändern + Akzeptanzkriterien + Tests
Ablauf: Plan → kleinster Patch → Tests → Diff → Review
Sicherheit: workspace-write + on-request + Netzwerk minimal
Danach: git diff --check → Tests → git add -p → menschlicher Review
```

```bash
codex --version
codex --help
codex
codex resume
codex --search
codex cloud --help
```

## Quellen

- [OpenAI Codex](https://developers.openai.com/codex/)
- [Codex – Modelle](https://developers.openai.com/codex/models)
- [Codex – Was ist neu?](https://developers.openai.com/codex/whats-new)
- [Codex CLI](https://developers.openai.com/codex/cli/)
- [Codex Configuration](https://developers.openai.com/codex/config/)
- [Codex Security](https://developers.openai.com/codex/security/)
- [AGENTS.md](https://developers.openai.com/codex/guides/agents-md/)
- [Codex MCP](https://developers.openai.com/codex/mcp/)
- [OpenAI Help – Codex und ChatGPT-Pläne](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)

## Verwandte Notizen

- [[Git-Premium-Spickzettel]]
- [[GitHub-Premium-Spickzettel]]
- [[GitLab-Premium-Spickzettel]]
- [[KI-Prompts-Premium-Spickzettel]]
- [[KI-Token-sparen-Premium-Spickzettel]]
- [[KI-Flottenmanagement-Premium-Spickzettel]]
- [[Claude-Premium-Spickzettel]]
- [[Gemini-Premium-Spickzettel]]
