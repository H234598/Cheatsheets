---
title: "GitHub – Cheatsheet"
aliases: ["GitHub Cheatsheet", "GitHub Pull Requests", "gh CLI"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [github, git, pull-request, actions, devops, security]
source: "https://docs.github.com/en"
---

# GitHub – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für GitHub: Authentisierung, Repositorys, Pull Requests, Reviews, Issues, Actions, Releases, Schutzregeln, Sicherheit und gh-CLI.

> [!note]
> GitHub ist die Kollaborations- und Hostingplattform; lokale Versionsverwaltung bleibt Git. Git-Befehle stehen im [[Git-Cheatsheet]].

## Inhalt

- [[#Authentisierung]]
- [[#Repositorys und Remotes]]
- [[#Pull-Request-Workflow]]
- [[#Reviews und Mergeverfahren]]
- [[#Issues, Labels und Projects]]
- [[#GitHub Actions]]
- [[#Releases und Pakete]]
- [[#Branchschutz und Rulesets]]
- [[#Sicherheit]]
- [[#gh-CLI-Schnellreferenz]]
- [[#Diagnose]]

## Authentisierung

### SSH

```bash
ssh-keygen -t ed25519 -a 64 -C 'name@example.org'
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com
```

Öffentlichen Schlüssel anzeigen:

```bash
cat ~/.ssh/id_ed25519.pub
```

Danach in den Kontoeinstellungen hinterlegen. Für verschiedene Konten:

```sshconfig
Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_work
    IdentitiesOnly yes
```

Remote:

```bash
git remote set-url origin git@github-work:organisation/repo.git
```

### HTTPS und Tokens

Passwortauthentisierung für Git über HTTPS durch Personal Access Token beziehungsweise Credential Manager ersetzen. Token:

- minimalen Scope wählen
- Ablaufdatum setzen
- nicht in URL, Skript oder Shell-History schreiben
- in Secret Store/Credential Manager verwalten
- bei Verdacht sofort widerrufen

### GitHub CLI

```bash
gh auth login
gh auth status
gh auth switch
gh auth refresh
```

> [!important]
> Organisationen können SSO, IP-Regeln, verpflichtende 2FA und genehmigungspflichtige OAuth-/GitHub-Apps erzwingen. Ein gültiger Token allein garantiert deshalb keinen Zugriff.

## Repositorys und Remotes

```bash
gh repo create organisation/projekt --private --clone
gh repo clone organisation/projekt
gh repo view --web
gh repo fork owner/projekt --clone
```

Upstream beim Fork:

```bash
git remote -v
git remote add upstream git@github.com:upstream/projekt.git
git fetch upstream
git switch main
git merge --ff-only upstream/main
git push origin main
```

### Wichtige Repositorydateien

```text
README.md
LICENSE
CONTRIBUTING.md
CODE_OF_CONDUCT.md
SECURITY.md
CODEOWNERS
.github/
├── ISSUE_TEMPLATE/
├── PULL_REQUEST_TEMPLATE.md
├── workflows/
└── dependabot.yml
```

## Pull-Request-Workflow

```bash
git switch -c feature/issue-123
git add -p
git commit -m 'feat: Importvalidierung ergänzen'
git push -u origin feature/issue-123
gh pr create --fill
```

### Gute PR-Beschreibung

```markdown
## Zweck
Welche Nutzer-/Betriebswirkung wird erreicht?

## Änderung
- ...
- ...

## Test
- [ ] Unit Tests
- [ ] manueller Pfad
- [ ] Rückwärtskompatibilität

## Risiko/Rollback
...

Closes #123
```

PR lokal auschecken:

```bash
gh pr list
gh pr view 123
gh pr checkout 123
gh pr diff 123
gh pr checks 123
```

### Draft und Bereitstellung

```bash
gh pr create --draft --fill
gh pr ready 123
gh pr review 123 --approve
gh pr review 123 --request-changes --body '...'
```

> [!tip]
> PR klein halten. Reine Umformatierung, Dependency-Update, Refactoring und Funktionsänderung wenn möglich trennen.

## Reviews und Mergeverfahren

| Verfahren | Wirkung |
|---|---|
| Merge commit | erhält Branchhistorie und erzeugt Mergecommit |
| Squash and merge | PR wird ein Commit auf Zielbranch |
| Rebase and merge | Commits linear neu auf Zielbranch geschrieben |

Auswahl nach Teamkonvention. Wichtiger als die Methode ist, dass Zielbranch reproduzierbar, prüfbar und releasefähig bleibt.

### Review-Checkliste

- entspricht Verhalten dem Issue/Design?
- Tests decken Erfolg, Fehler und Randfälle?
- Authentisierung/Autorisierung korrekt?
- Eingaben validiert und Ausgaben kodiert?
- Migrationen vorwärts/rückwärts geplant?
- Logs ohne Geheimnisse/PII?
- Performance und Ressourcenverbrauch?
- Dokumentation und Betriebshinweise aktualisiert?
- CI-Ergebnisse tatsächlich für den geprüften Commit?

CODEOWNERS-Beispiel:

```text
*                 @org/core-maintainers
/docs/            @org/docs
/infrastructure/  @org/platform
/security/        @org/security
```

## Issues, Labels und Projects

### Issue anlegen

```bash
gh issue create --title 'Import bricht bei leerem Datum ab' --body-file issue.md
gh issue list --label bug --assignee @me
gh issue view 123
gh issue close 123 --comment 'Behoben durch #456'
```

Gute Labels:

```text
type:bug        type:feature      type:maintenance
priority:p1     priority:p2       priority:p3
status:blocked  status:needs-info
area:api        area:frontend     area:infra
```

Labels nicht als vollständigen Workflow missbrauchen; klare Definitionen und wenige orthogonale Dimensionen verwenden.

## GitHub Actions

Minimales Workflowbeispiel:

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: pip
      - run: python -m pip install -r requirements.txt
      - run: python -m pytest
```

### Sicherheitsregeln

- `permissions` explizit minimieren.
- Actions auf vertrauenswürdige Herausgeber und möglichst Commit-SHA pinnen.
- Secrets nicht aus untrusted Fork-Code exponieren.
- `pull_request_target` nur mit genauer Kenntnis verwenden.
- OIDC statt langfristiger Cloud-Schlüssel bevorzugen.
- Umgebungen mit Freigaben für Produktion nutzen.
- Artefakte und Logs auf Geheimnisse prüfen.
- Self-hosted Runner von untrusted Code isolieren.

Status:

```bash
gh run list
gh run view <id>
gh run watch <id>
gh run rerun <id> --failed
gh workflow list
gh workflow run ci.yml -f target=staging
```

## Releases und Pakete

```bash
gh release create v2.1.0 --generate-notes
gh release view v2.1.0
gh release upload v2.1.0 dist/app.tar.gz#app-linux-amd64
gh release download v2.1.0
```

Release-Checkliste:

- signierter/geschützter Tag
- changelog und Migrationshinweise
- reproduzierbare Artefakte
- Prüfsummen/Signaturen
- SBOM, falls erforderlich
- bekannte Probleme
- Rollback und Supportzeitraum

## Branchschutz und Rulesets

Für `main` typischerweise:

- Pull Request erforderlich
- definierte Anzahl Reviews
- Code Owner Review für sensible Pfade
- veraltete Reviews bei neuen Commits zurücksetzen
- Statuschecks erforderlich
- Branch muss aktuell sein, wenn sinnvoll
- signierte Commits optional/regelabhängig
- Force-Push und Löschen sperren
- Administrator-Bypass minimieren und auditieren

> [!warning]
> Branchschutz ersetzt keine Rechtehygiene. Repository-Admin, Actions-Token, Deploy Keys, Apps und Umgebungsfreigaben ebenfalls betrachten.

## Sicherheit

### Secret Scanning und Dependabot

Konfiguration `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
```

Sicherheitsfunktionen je Plan/Repository prüfen:

- Dependabot Alerts/Updates
- Secret Scanning und Push Protection
- Code Scanning/CodeQL
- Dependency Review
- private vulnerability reporting
- Security Advisories

### Token/Schlüssel kompromittiert

1. sofort widerrufen oder rotieren
2. Audit Log und Nutzung prüfen
3. betroffene Systeme/Secrets rotieren
4. Geheimnis aus aktuellem Stand entfernen
5. Historie nur koordiniert bereinigen
6. Ursache und Prävention dokumentieren

## gh-CLI-Schnellreferenz

```bash
gh status
gh browse
gh repo view
gh pr status
gh pr list
gh pr create --fill
gh pr checks --watch
gh issue list
gh run list
gh api repos/{owner}/{repo}/branches/main/protection
gh secret list
gh variable list
```

JSON-Ausgabe:

```bash
gh pr list --json number,title,author,isDraft,statusCheckRollup \
  --jq '.[] | [.number,.title,.author.login] | @tsv'
```

## Diagnose

### `Permission denied (publickey)`

```bash
ssh -vT git@github.com
ssh-add -l
git remote -v
```

Prüfen: richtige Host-Alias-Konfiguration, Schlüssel im Konto/Organisation freigegeben, SSO autorisiert, Remote passt zum Konto.

### HTTPS 403/Authentisierung

```bash
gh auth status
git config --show-origin --get-all credential.helper
git remote -v
```

Token-Scopes, Organisationsrichtlinien und gespeicherte alte Credentials prüfen.

### PR zeigt unerwartete Commits

```bash
git log --oneline --graph --decorate --all
git merge-base HEAD origin/main
git diff origin/main...HEAD
```

Branch möglicherweise von falscher Basis erstellt. Sauber rebasen oder gewünschten Commitbereich auf neuen Branch cherry-picken.

### Action läuft lokal, CI scheitert

- Betriebssystem/Architektur/Zeitzone unterscheiden sich?
- uncommittete lokale Datei oder globale Dependency?
- Dateinamen-Groß-/Kleinschreibung?
- Secret/Permission fehlt?
- Cache veraltet?
- exakte Runner-Logs und verwendeten Commit prüfen.

## Quellen
- [GitHub Docs](https://docs.github.com/en)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
- [About pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)

## Verwandte Notizen
- [[Git-Cheatsheet]]
- [[GitLab-Cheatsheet]]
- [[SSH-Cheatsheet]]
- [[Codex-Cheatsheet]]
