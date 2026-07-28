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

## Pull-Request-Validierung

`.github/workflows/validate.yml` läuft bei:

- jedem Pull Request;
- jedem Push nach `main`;
- manueller Auslösung über `workflow_dispatch`.

Der Workflow besitzt ausschließlich:

```yaml
permissions:
  contents: read
```

Er verwendet einen festen `ubuntu-24.04`-Runner, Python 3.12, begrenzte Laufzeit und bricht ältere Läufe desselben Pull Requests ab. Checkout-Credentials werden nicht persistent gespeichert.

Die Pipeline führt in dieser Reihenfolge aus:

1. Installation der exakt gepinnten Pythonabhängigkeiten;
2. maschinelle Workflow-Policy;
3. Python-Compilecheck;
4. Unit- und Integrationstests;
5. Contentmodellprüfung;
6. Link- und Calloutvalidierung;
7. Secret-, Raw-HTML- und Laufzeitassetprüfung;
8. reproduzierbare Erzeugung der erwarteten kanonischen Metadaten;
9. vollständigen Strict-MkDocs-Build unter einem Project-Page-Unterpfad;
10. Prüfung, dass der Build keine versionierten Quelldateien verändert hat.

Diagnoseberichte werden auch bei einem fehlgeschlagenen Schritt als normales Actions-Artefakt hochgeladen und nach 14 Tagen gelöscht. Der PR-Workflow enthält keine Pages-Actions, kein Environment und keine Secrets.

## Metadatendrift

Bis zum separaten Metadaten-/Content-PR wird Drift von:

- `MANIFEST.csv`;
- `MANIFEST.md`;
- `BUILD-REPORT.yaml`;
- `SHA256SUMS.txt`

als `metadata-diff.patch` dokumentiert, aber noch nicht als eigenes CI-Gate blockiert. Die eigentliche Web- und Contentvalidierung bleibt blockierend. Nach der bewussten kanonischen Aktualisierung wird der Diffvergleich auf einen Fehler bei jeder Abweichung umgestellt.

## Sicherheitsberichte

`validate_security.py` blockiert hochpräzise Secretmuster, vollständige private Schlüsselblöcke, aktive HTML-Tags, Eventhandler, gefährliche URL-Schemata und externe Laufzeitbilder. Raw HTML, das nicht aktiv gefährlich, aber auch nicht ausdrücklich freigegeben ist, erscheint zunächst als Warnung im Bericht.

Ausnahmen für secretähnliche Lehrbeispiele müssen in `config/secret-allowlist.yaml` enthalten:

- Regelname;
- exakten Repositorypfad;
- SHA-256 des exakten Treffers;
- nachvollziehbare Begründung.

Eine pauschale Datei- oder Regel-Ausnahme ist unzulässig.

## Abhängigkeitsaktualisierung

Dependabot prüft wöchentlich:

- GitHub Actions;
- Pythonabhängigkeiten.

Die Aktualisierungen erfolgen als normale Pull Requests gegen `main`, durchlaufen dieselben Gates und werden nicht allein wegen ihres automatischen Autors gemergt.

## Zielstruktur für Pages

Die spätere Pages-Pipeline besteht aus getrennten Jobs:

1. `build`: Checkout, reproduzierbare Validierung, Tests und Erzeugung von `site/`.
2. `deploy`: Veröffentlichung des zuvor geprüften Pages-Artefakts im Environment `github-pages`.

Ein fehlgeschlagener Build darf kein Deployment auslösen.
