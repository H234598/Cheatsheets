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
9. byteweiser, blockierender Vergleich der kanonischen Metadaten;
10. vollständigen Strict-MkDocs-Build unter einem Project-Page-Unterpfad;
11. Prüfung, dass der Build keine versionierten Quelldateien verändert hat.

Diagnoseberichte werden auch bei einem fehlgeschlagenen Schritt als normales Actions-Artefakt hochgeladen und nach 14 Tagen gelöscht. Der PR-Workflow enthält keine Pages-Actions, kein Environment und keine Secrets.

## Kanonische Metadaten

Die folgenden Dateien werden bei jedem Lauf reproduzierbar neu erzeugt und byteweise mit dem eingecheckten Stand verglichen:

- `MANIFEST.csv`;
- `MANIFEST.md`;
- `BUILD-REPORT.yaml`;
- `SHA256SUMS.txt`.

Jede Abweichung ist ein blockierender Fehler und wird zusätzlich als `metadata-diff.patch` im Diagnoseartefakt gespeichert. Änderungen an Fachseiten, Kategorieindizes, Dateinamen oder Frontmatter müssen deshalb immer gemeinsam mit den generatorisch aktualisierten Metadaten reviewt werden.

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

## Pages-Deployment

`.github/workflows/pages.yml` läuft ausschließlich bei:

- Push nach `main`;
- manueller Auslösung über `workflow_dispatch`.

Globale Berechtigungen sind leer. Der Workflow besteht aus zwei getrennten Jobs:

1. `build`: liest den Repositoryinhalt, konfiguriert Pages, validiert Quellen und erzeugt genau einmal `site/`;
2. `deploy`: benötigt den erfolgreichen Build und veröffentlicht ausschließlich dessen Pages-Artefakt.

### Buildjob

```yaml
permissions:
  contents: read
  pages: write
```

Der Build verwendet `actions/configure-pages` als einzige Autorität für die tatsächliche Basis-URL. Die daraus gelieferte URL wird an `build_site.py --site-url` übergeben. Dadurch bleiben Project Page und spätere Custom Domain dieselbe Buildarchitektur.

Vor dem Upload prüft `validate_pages_artifact.py`:

- `index.html` und `404.html`;
- reguläre Dateien und Verzeichnisse;
- keine Symlinks oder Hardlinks;
- keine Case-insensitiven Pfadkollisionen;
- Größenlimit;
- deterministischen Baum-SHA-256.

### Deploymentjob

```yaml
permissions:
  pages: write
  id-token: write
```

Der Deploymentjob besitzt:

```yaml
needs: build
environment:
  name: github-pages
  url: ${{ steps.deployment.outputs.page_url }}
```

Er checkt das Repository nicht erneut aus, baut nichts und verwendet keine Secrets. Ein fehlgeschlagener Build kann deshalb kein Deployment auslösen.

Das vollständige Betriebs-, Custom-Domain- und Rollback-Runbook steht in `docs/WEB-WARTUNG.md`.
