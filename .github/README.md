# GitHub-Automation und Schutzregeln

Dieses Verzeichnis enthält ausschließlich nachvollziehbare, reproduzierbare und minimal berechtigte Automatisierung für das Cheatsheets-Repository.

## Verbindliche Regeln

- Keine externen Bootstrap-Archive oder temporären Payload-Hosts.
- Keine selbstlöschenden oder selbstmodifizierenden Workflows.
- Keine direkten Workflow-Pushes nach `main`.
- Kein `pull_request_target` für Build-, Test- oder Inhaltsvalidierung.
- Pull-Request-Workflows erhalten standardmäßig nur `contents: read`.
- GitHub Pages wird ausschließlich aus dem generierten Verzeichnis `site/` als Actions-Artefakt veröffentlicht.
- Pull Requests validieren, veröffentlichen aber niemals die produktive Website.
- Externe Actions werden vollständig auf unveränderliche Commit-SHAs gepinnt; ein Versionskommentar dokumentiert den zugehörigen Release-Tag.
- Änderungen unter `.github/`, `scripts/`, `tests/`, `web/`, `config/` sowie an Build- und Abhängigkeitsdateien benötigen CODEOWNER-Review.
- Generierte Verzeichnisse wie `build/` und `site/` werden nie nach `main` committed.
- Inhaltsquellen werden vom Webbuild nur gelesen; Transformationen erfolgen ausschließlich in generierten Verzeichnissen.

## Zielstruktur

Die spätere Pages-Pipeline besteht aus getrennten Jobs:

1. `build`: Checkout, reproduzierbare Validierung, Tests und Erzeugung von `site/`.
2. `deploy`: Veröffentlichung des zuvor geprüften Pages-Artefakts im Environment `github-pages`.

Ein fehlgeschlagener Build darf kein Deployment auslösen.
