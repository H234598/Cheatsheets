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
- Online- und Offline-Artefakte stammen aus demselben Checkout, Quellcommit und `SOURCE_DATE_EPOCH`.
- Optionale Erweiterungen dürfen den Deploymentjob weder um einen Checkout noch um einen zweiten Build erweitern.

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

Er verwendet:

- `ubuntu-24.04`;
- Python 3.12;
- Node.js 24;
- exakt gepinnte Python- und npm-Abhängigkeiten;
- `npm ci --ignore-scripts`;
- Chromium ausschließlich über das lokal installierte `npx --no-install`;
- einen Worker und begrenzte Laufzeit;
- abbrechbare Concurrency pro Pull Request;
- Checkout ohne persistente Credentials.

Die Pipeline führt in dieser Reihenfolge aus:

1. Installation und Prüfung der exakt gepinnten Python- und npm-Abhängigkeiten;
2. reproduzierbare Chromiuminstallation;
3. maschinelle Workflow-Policy;
4. Python-Compilecheck und JavaScript-Syntaxprüfung;
5. Unit- und Integrationstests;
6. Contentmodellprüfung;
7. Link- und Calloutvalidierung;
8. Secret-, Raw-HTML- und Laufzeitassetprüfung;
9. reproduzierbare Erzeugung der erwarteten kanonischen Metadaten;
10. byteweisen, blockierenden Vergleich der kanonischen Metadaten;
11. vollständigen Online- und Offline-Strict-MkDocs-Build unter einem Project-Page-Unterpfad;
12. unabhängige Prüfung und atomare Testextraktion von `Cheatsheets-Offline-HTML.zip`;
13. Prüfung des gesamten Pages-Artefakts;
14. statische JavaScript-, CSS-, HTML- und Laufzeitassetbudgets;
15. Online-, No-JavaScript-, Accessibility-, Mobil- und Offline-Browsertests;
16. Prüfung, dass der Build keine versionierten Quelldateien verändert hat.

Diagnoseberichte werden auch bei einem fehlgeschlagenen Schritt als normales Actions-Artefakt hochgeladen und nach 14 Tagen gelöscht. Der PR-Workflow enthält keine Pages-Actions, kein Environment und keine Secrets.

## Workflow-Selbstvalidierung

`scripts/validate_workflows.py` erzwingt unter anderem:

- vollständige Action-SHA-Pins samt Versionskommentar;
- Python 3.12 und Node.js 24;
- `npm ci --ignore-scripts`;
- `npx --no-install playwright install --with-deps chromium`;
- Webbudget- und Browsertestschritte;
- unabhängige Offline-Archivprüfung;
- Extraktion nach `build/offline-site`;
- `build/reports/offline.json`;
- JavaScript-Syntaxprüfung der Offline-Browsertests;
- einen Diagnoseupload mit `if: always()`;
- keine Deploymentactions, Secrets oder erweiterten Rechte im Validate-Workflow.

Ergänzende Vertragstests prüfen den Pages-Workflow und stellen sicher, dass Offline-HTML im Buildjob validiert, im Deploymentjob aber weder neu gebaut noch erneut geprüft wird.

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

`validate_offline_archive.py` prüft zusätzlich das fertige Offline-ZIP unabhängig vom Generator. Es verifiziert Archivpfade, Dateitypen, Rechte, Zeitstempel, Manifest, Prüfsummen, Baumhash und sämtliche lokalen HTML-/CSS-Referenzen. Eine Testextraktion darf ausschließlich atomar unter `build/` erfolgen.

## Browser- und Performancegates

Playwright startet parallel:

```text
Online:  http://127.0.0.1:4173/Cheatsheets/
Offline: http://127.0.0.1:4174/
```

Blockierend geprüft werden:

- Online-Navigation und repräsentative kurze und lange Fachseiten;
- axe ohne `serious`- oder `critical`-Befund;
- No-JavaScript-Fallback;
- Favoriten, Fortschritt, Fokusmodus, Tastatur und Filter;
- 320-Pixel-Ansicht, Reduced Motion und Scrollcontainer;
- Downloads und tiefe 404-Pfade;
- entpacktes Offlinepaket mit lokaler Suche und `.html`-Navigation;
- Offline-No-JavaScript-Fallback direkt über `file://`;
- null ungeplante fremde Laufzeitrequests.

Statische Budgets bleiben:

```text
Eigenes JavaScript, Gzip: 30 KiB
Eigenes CSS, Gzip:        35 KiB
Einzelne HTML-Datei:       2 MiB
Externe Laufzeitassets:    0
```

## Abhängigkeitsaktualisierung

Dependabot prüft wöchentlich:

- GitHub Actions;
- Pythonabhängigkeiten;
- npm-Abhängigkeiten der Browsertests.

Die Aktualisierungen erfolgen als normale Pull Requests gegen `main`, durchlaufen dieselben Gates und werden nicht allein wegen ihres automatischen Autors gemergt.

## Pages-Deployment

`.github/workflows/pages.yml` läuft ausschließlich bei:

- Push nach `main`;
- manueller Auslösung über `workflow_dispatch`.

Globale Berechtigungen sind leer. Der Workflow besteht aus zwei getrennten Jobs:

1. `build`: liest den Repositoryinhalt, konfiguriert Pages, validiert Quellen und erzeugt genau einmal den finalen `site/`-Baum einschließlich Offline-ZIP;
2. `deploy`: benötigt den erfolgreichen Build und veröffentlicht ausschließlich dessen Pages-Artefakt.

### Buildjob

```yaml
permissions:
  contents: read
  pages: write
```

Der Build verwendet `actions/configure-pages` als einzige Autorität für die tatsächliche Basis-URL. Die daraus gelieferte URL wird an `build_site.py --site-url` übergeben. Online-Site, Downloadmanifeste, Provenienz und Offlinepaket nennen dadurch dieselbe kanonische URL.

Vor dem Upload validiert der Build unabhängig:

- `Cheatsheets-Offline-HTML.zip`;
- `index.html` und `404.html`;
- reguläre Dateien und Verzeichnisse;
- keine Symlinks oder Hardlinks;
- keine Case-insensitiven Pfadkollisionen;
- Größenlimits;
- deterministische Baum-SHA-256-Werte.

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

## Produktiver Betrieb

Am 2026-07-28 wurde durch den Betreiber bestätigt:

- Pages-Quelle: **GitHub Actions**;
- Custom Domain: `https://cheatsheets.telacore.org/`;
- DNS und Zertifikat aktiv;
- HTTPS erzwungen;
- Alias-Subdomains werden vor GitHub auf die kanonische Domain umgeleitet.

Das vollständige Betriebs-, Custom-Domain-, Offline- und Rollback-Runbook steht in:

- `docs/WEB-WARTUNG.md`;
- `docs/WEB-OFFLINE.md`.
