# GitHub Pages – Betrieb, Deployment und Rollback

## Zielarchitektur

Die Webseite wird ausschließlich aus einem GitHub-Actions-Artefakt veröffentlicht. Weder `build/` noch `site/` werden nach `main` committed.

```text
main-Push oder manuelle Auslösung
          │
          ▼
Pages / build
          │
          ├── Checkout ohne persistente Credentials
          ├── Python 3.12 und gepinnte Abhängigkeiten
          ├── vollständige Validierung
          ├── genau ein Strict-Build nach site/
          ├── Artefaktprüfung
          └── Upload als github-pages-Artefakt
          │
          ▼
Pages / deploy
          │
          ├── needs: build
          ├── Environment github-pages
          ├── OIDC über id-token: write
          └── actions/deploy-pages
          │
          ▼
veröffentlichte page_url
```

Ein fehlgeschlagener Build erzeugt kein Deployment.

## Workflow

Datei:

```text
.github/workflows/pages.yml
```

Trigger:

- Push nach `main`;
- manuelle Auslösung über `workflow_dispatch`;
- ausdrücklich **kein** Pull-Request-Trigger.

Concurrency:

```yaml
concurrency:
  group: github-pages
  cancel-in-progress: false
```

Ein bereits laufendes Deployment wird nicht abgebrochen. Neuere Läufe warten, statt eine möglicherweise halbfertige Veröffentlichung zu erzwingen.

## Berechtigungen

Globale Workflowberechtigungen sind leer:

```yaml
permissions: {}
```

### Buildjob

```yaml
permissions:
  contents: read
  pages: write
```

Der Buildjob darf Inhalte lesen und GitHub Pages konfigurieren. Er besitzt weder `contents: write` noch `id-token: write`.

### Deploymentjob

```yaml
permissions:
  pages: write
  id-token: write
```

Der Deploymentjob checkt das Repository nicht erneut aus und führt keinen Build aus. Er veröffentlicht ausschließlich das vom erfolgreichen Buildjob erzeugte Pages-Artefakt.

## Dynamische Site-URL

`actions/configure-pages` liefert die für das Repository tatsächlich konfigurierte Basis-URL. Der Build verwendet ausschließlich diesen Wert:

```yaml
env:
  SITE_URL: ${{ steps.pages.outputs.base_url }}
```

```bash
python scripts/build_site.py \
  --strict \
  --site-url "${SITE_URL%/}/"
```

Dadurch funktionieren:

- die anfängliche Project Page unter `/Cheatsheets/`;
- eine spätere Root-Custom-Domain;
- eine Domain mit Unterpfad;
- lokale Test-URLs.

Die Markdownquellen enthalten keine fest codierte Domain und keinen fest codierten Repository-Unterpfad.

## Validierung vor dem Upload

Der Buildjob führt dieselben Kernprüfungen wie die Pull-Request-CI aus:

1. Workflowpolicy;
2. Python-Compilecheck;
3. vollständige Pytest-Suite;
4. Contentmodell;
5. interne Links und Callouts;
6. Secrets, Raw HTML und externe Laufzeitassets;
7. bytegleiche kanonische Metadaten;
8. genau einen Strict-MkDocs-Build;
9. Pages-Artefaktprüfung;
10. unveränderte versionierte Arbeitskopie.

Das fertige Verzeichnis `site/` wird durch `scripts/validate_pages_artifact.py` geprüft auf:

- vorhandene `index.html`;
- vorhandene `404.html`;
- reguläres Wurzelverzeichnis;
- keine symbolischen Links;
- keine Hardlinks;
- keine Sonderdateien;
- keine Case-insensitiven Pfadkollisionen;
- maximale Gesamtgröße von 1.000.000.000 Bytes;
- deterministischen Baum-SHA-256.

Der Bericht liegt während des Builds unter:

```text
build/reports/pages-artifact.json
```

## Einmalige Repositoryeinstellung

Die Pages-Veröffentlichungsquelle muss im Repository auf **GitHub Actions** stehen. Der Workflow verwendet keine Veröffentlichung aus einem Branch oder einem `/docs`-Verzeichnis.

Nach dem ersten erfolgreichen Merge ist zu prüfen:

- Repository → Settings → Pages;
- Source: GitHub Actions;
- Environment `github-pages` vorhanden;
- Deployment ausschließlich von `main`;
- optional erforderlicher Reviewer für das Environment;
- erfolgreiche `page_url` im Deploymentjob.

Die verfügbare Connector-Schnittstelle verändert diese Repositoryeinstellung nicht automatisch. Der Workflow ist so gebaut, dass `actions/configure-pages` die vorhandene Pages-Konfiguration ausliest und die tatsächliche Basis-URL an den Build übergibt.

## Lokale Project-Page-Prüfung

```bash
python -m pip install \
  -r requirements-docs.txt \
  -r requirements-test.txt

export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"

python scripts/build_site.py \
  --strict \
  --site-url https://example.invalid/Cheatsheets/

python scripts/validate_pages_artifact.py \
  --site-dir site \
  --report build/reports/pages-artifact.json
```

## Abnahme nach dem ersten Deployment

Nach dem ersten erfolgreichen `main`-Lauf werden mindestens geprüft:

- Buildjob grün;
- Deploymentjob grün;
- ausgegebene `page_url` verwendet HTTPS;
- Startseite liefert die erwartete Site;
- mindestens eine tiefe Fachseite ist erreichbar;
- Kategorie-, Gesamt- und Tagindex funktionieren;
- `404.html` ist im Artefakt vorhanden;
- keine Quelldatei oder Buildausgabe wurde nach `main` committed.

Reale HTTP- und Browserprüfungen werden in Phase 7 automatisiert. Phase 5B bestätigt zunächst die GitHub-Pages-Veröffentlichung und ihre URL.

## Custom Domain

Eine Custom Domain wird später ausschließlich in den GitHub-Pages-Einstellungen und beim DNS-Anbieter konfiguriert. Die Buildpipeline benötigt dafür keine Markdownänderung.

In dieser Actions-basierten Architektur wird keine `CNAME`-Datei als Buildquelle gepflegt. `configure-pages.outputs.base_url` bleibt die einzige URL-Autorität.

Vor der Umschaltung:

1. Domaininhaberschaft und DNS-Ziel verifizieren;
2. Custom Domain in GitHub Pages eintragen;
3. HTTPS-Aktivierung abwarten und erzwingen;
4. Pages-Workflow manuell auslösen;
5. Startseite, tiefe Seite, Suche, Assets und 404 erneut prüfen.

## Rollback

Ein fehlerhaftes Deployment wird nicht durch manuelles Austauschen eines Artefakts repariert.

Empfohlenes Verfahren:

1. fehlerverursachenden `main`-Commit per Review-PR revertieren;
2. vollständige Validate-Gates abwarten;
3. Revert mergen;
4. Pages-Workflow veröffentlicht aus dem wiederhergestellten Commit;
5. `page_url` und repräsentative Seiten prüfen.

Ist ausschließlich die Workflowdefinition defekt, wird `.github/workflows/pages.yml` in einem kleinen Infrastruktur-PR auf den letzten grünen Stand zurückgesetzt.

## Fehlerdiagnose

### `configure-pages` schlägt fehl

Prüfen:

- Pages-Quelle ist GitHub Actions;
- Buildjob besitzt `pages: write`;
- Repository erlaubt GitHub Actions;
- Workflow läuft auf `main` oder manuell, nicht aus einem Pull Request.

### Artefaktprüfung schlägt fehl

Der JSON-Bericht nennt einen stabilen Fehlercode:

| Code | Bedeutung |
|---|---|
| `PA001`–`PA004` | Siteverzeichnis oder Pflichtdatei fehlt |
| `PA005`–`PA008` | Symlink oder unerwarteter Dateityp |
| `PA009` | Hardlink erkannt |
| `PA010` | Case-insensitive Pfadkollision |
| `PA011` | Größenlimit überschritten |

### Deploymentjob schlägt fehl

Prüfen:

- Buildjob und Pages-Artefakt waren grün;
- `deploy` besitzt `pages: write` und `id-token: write`;
- Environment heißt exakt `github-pages`;
- Environment-Regeln erlauben den `main`-Branch;
- kein zweiter Deploymentmechanismus konkurriert mit dem Workflow.
