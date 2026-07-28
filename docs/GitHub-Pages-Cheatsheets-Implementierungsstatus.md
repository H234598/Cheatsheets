# GitHub-Pages-Cheatsheets – Implementierungsstatus

Dieser Fortschrittsnachweis wird mit jeder Planphase aktualisiert. Verbindliche Sollbeschreibung ist der vollständige Implementierungsplan aus dem Arbeitsauftrag; Abweichungen werden hier begründet dokumentiert.

| Phase | Status | Nachweis |
|---|---|---|
| 0A – Sicherheitsbaseline | ✅ umgesetzt | PR #1, Merge `fdf24c369dded98a63af046c174d29d5636c080b` |
| 0B – Inventur und Baseline | ✅ umgesetzt | PR #2, Merge `48f2a518f52e4d595a0887bd2de3ee45fcc3f19a`, 8 Tests |
| 1 – Linkmodell und Callouts | ✅ umgesetzt | PR #3, Merge `7fcccdca800b60dc2fee55de1b5e3b99614e1c3c`, 21 Tests |
| 2 – MkDocs-Basis | ✅ umgesetzt | PR #4, Merge `81ef6b66abb64116d153d8558ea6a230eee676e9`, 26 Tests |
| 3 – Navigation, Indizes und Suche | ✅ umgesetzt | PR #6, Merge `7db8f713aca07e67b481f9fbcb00553f6a555495`; CodeRabbit und qlty grün |
| 4 – ADHS-freundliche Oberfläche | ✅ umgesetzt | PR #7, Merge `0682c7f8e508d56b60d8d8e72024121e1bcd815d`; CodeRabbit und qlty grün |
| 5A – PR-CI | ✅ umgesetzt | PR #9, Merge `69c72997eed4fc0ac831eba696bac12b3a2f69b9`; 78 Tests und alle Gates grün |
| 5B – Pages-Deployment | 🚧 im Review | Branch `agent/pages-deployment`; getrennte Build-/Deploy-Jobs, Artefaktvalidator und Betriebsrunbook |
| 6 – Downloads und Provenienz | ⬜ offen | – |
| 7 – Browser, Accessibility und Performance | ⬜ offen | – |
| 8 – optionale Erweiterungen | ⬜ offen | – |

## Abgeschlossene Phase 3

PR #6 erzeugt die Navigation, Kategorie-, Gesamt-, Alphabet- und Tagindizes sowie die maschinenlesbaren Dateien `pages.json`, `categories.json`, `tags.json` und `build-info.json`. Die Generatoren laufen im selben atomaren Stagingverzeichnis wie die transformierten Markdown-Seiten; die resultierende Navigation wird strukturiert in `mkdocs.generated.yml` übernommen.

Vor dem Merge wurden zusätzlich behoben:

- doppelte Page-IDs im Manifest trotz gleicher ID-Menge;
- potenzielles Folgen von Symlinks beim Vergleich kanonischer Metadaten;
- abweichende Unicode-Normalisierung zwischen Sortierung und Alphabetüberschrift;
- zunächst fehlende Verkabelung der Generatoren mit dem tatsächlichen Gesamtbuild.

## Abgeschlossene Phase 4

PR #7 ergänzt die Oberfläche progressiv; die kanonischen Markdown-Dateien bleiben unverändert. Umgesetzt wurden:

- drei primäre Startaktionen;
- lokale Favoriten, zuletzt gelesen und monotoner Lesefortschritt;
- Fokusmodus mit sichtbarem Ausstieg auf allen Seitentypen;
- lokale Kategorie-, Tag-, Text- und Zeitfilter;
- Tastaturhilfe mit lokal abschaltbaren Kürzeln;
- robuste Fallbacks bei deaktiviertem JavaScript, beschädigtem Zustand oder nicht verfügbarem `localStorage`;
- responsive, reizreduzierte Karten-, Fokus- und Dialogdarstellung.

Vor dem Merge wurden fünf konkrete Reviewbefunde behoben und mit Regressionstests abgesichert:

- Favoritenkappung behält konsistent die neuesten Einträge;
- native Semantik generischer Tabellen bleibt erhalten;
- lokale Vorschau verwendet eine same-origin Sitewurzel;
- Enter im Filterformular lädt die Seite nicht neu;
- optionale Lesezeit erzeugt keine leere Beschriftung.

## Parallele Inhaltsvereinheitlichung

PR #8 wurde unabhängig vom Phasenstrang als repositoryweite Inhalts- und Dateinamenvereinheitlichung gemergt:

```text
05b8d7469ba8c1129ddfde016e43852f88bfc499
```

Der PR ersetzt die bisherige Zusatzbezeichnung durch **Cheatsheet**, benennt die betroffenen Dateien und Links um und regeneriert die kanonischen Metadaten. Er behebt zugleich die im ersten Phase-5A-Lauf sichtbar gewordenen Baseline-Linkprobleme:

- Kategorieindizes verweisen eindeutig auf den Root-Gesamtindex;
- die Thales-Inhaltsmarke verwendet `Java JCA/JCE`;
- der mobile AMD-Unterabschnitt besitzt einen eindeutigen Titel.

Der anschließend eröffnete PR #10 wurde deshalb ohne Merge und mit leerem Diff geschlossen.

## Abgeschlossene Phase 5A

PR #9 wurde nach den Merges von PR #7 und PR #8 ohne alte Branchhistorie exakt auf den damaligen `main`-Stand aufgebaut. Der Diff enthielt ausschließlich CI-, Security-, Test-, Konfigurations- und Dokumentationsdateien.

Umgesetzt wurden:

- `.github/workflows/validate.yml` für Pull Requests, `main` und manuelle Läufe;
- ausschließlich `contents: read`, keine Secrets, kein Environment und kein Deployment;
- vollständige Commit-SHA-Pins mit Versionskommentaren;
- fester Runner `ubuntu-24.04`, Python 3.12, Timeouts und Concurrency;
- Workflow-Selbstvalidierung;
- Unit-, Integrations-, Content-, Link-, Sicherheits- und Strict-MkDocs-Gates;
- byteweiser, blockierender Vergleich der kanonischen Metadaten;
- Diagnoseartefakte auch nach Fehlern;
- Dependabot für GitHub Actions und Python;
- hochpräziser Secret-/Raw-HTML-/Laufzeitasset-Scanner mit exakten, hashgebundenen Ausnahmen.

Die Pipeline hat während ihrer Einführung reale Fehler sichtbar gemacht. Behoben wurden:

- falscher Modulimport im Securityscanner;
- strukturierte Prüfung von Checkout-Credentials, Pythonversion und `if: always()`;
- spröde beziehungsweise unvollständige Test-Fixtures;
- vollständige Linkdiagnostik als JSON und Text;
- zunächst nur diagnostischer Metadatenvergleich wurde nach PR #8 in ein hartes Gate überführt.

Der vollständige GitHub-Actions-Lauf `30324962948` auf dem finalen PR-Head `52db970bd5d8c13e9d96d371ae8bf33aac92cb42` bestätigte:

- **78 von 78 Tests bestanden**;
- zwölf Kategorien und 86 Fachseiten;
- null Contentfehler und null Contentwarnungen;
- null Linkfehler und null Linkwarnungen;
- null Securityfehler, -warnungen oder Informationsbefunde;
- bytegleiche kanonische Metadaten, `metadata-diff.patch` leer;
- vollständiger Strict-MkDocs-Build erfolgreich;
- versionierte Arbeitskopie nach dem Build unverändert;
- Diagnoseartefakt erfolgreich erzeugt;
- CodeRabbit und qlty grün;
- keine offenen Review-Threads.

PR #9 wurde anschließend per Squash unter folgendem Commit gemergt:

```text
69c72997eed4fc0ac831eba696bac12b3a2f69b9
```

## Laufende Phase 5B

Phase 5B ergänzt `.github/workflows/pages.yml` mit zwei strikt getrennten Jobs:

1. `build` liest Inhalte, validiert das Repository, ermittelt die tatsächliche Pages-Basis-URL und erzeugt `site/` genau einmal;
2. `deploy` benötigt den erfolgreichen Build und veröffentlicht ausschließlich dessen Pages-Artefakt im Environment `github-pages`.

Sicherheits- und Betriebsmerkmale:

- Trigger nur bei Push nach `main` und manuell;
- keine Pull-Request-Veröffentlichung;
- leere globale Berechtigungen;
- Buildjob: `contents: read`, `pages: write`;
- Deploymentjob: `pages: write`, `id-token: write`;
- vollständige Action-SHA-Pins mit Versionskommentaren;
- dynamische `site_url` aus `configure-pages.outputs.base_url`;
- genau ein zentraler Strict-Build;
- kein Checkout und kein Build im Deploymentjob;
- `needs: build` und Environment `github-pages`;
- kein direktes Pushen oder manuelles Austauschen von Artefakten.

Neu ist `scripts/validate_pages_artifact.py`. Das Modul blockiert fehlende `index.html`/`404.html`, Symlinks, Hardlinks, Sonderdateien, Case-Kollisionen und ein überschrittenes Größenlimit. Es erzeugt zusätzlich einen deterministischen Baum-SHA-256 und einen JSON-Bericht.

Die Workflow- und Artefaktverträge werden durch `tests/test_pages_workflow.py` und `tests/test_pages_artifact.py` geprüft. Betrieb, Erstaktivierung, Custom Domain, Fehlerdiagnose und Rollback sind in `docs/WEB-WARTUNG.md` dokumentiert.

Der Pull Request muss zunächst die vorhandene Validate-Pipeline, CodeRabbit und qlty bestehen. Nach dem Merge wird der erstmals auf `main` laufende Pages-Workflow bis zum tatsächlichen Deployment und zur ausgegebenen `page_url` verifiziert.

Eine Phase wird erst nach grünen Gates, ohne offene Review-Threads und nach verifiziertem Merge als vollständig umgesetzt markiert.

## Verbindliche Ausgangsstände

- `H234598/Cheatsheets`: `42541f87105cb6dd178c8609cb031dc361bb59a9`
- `H234598/ADHS-Lernpfad`: `93c8c02d263ec123c1c271caf0d2deaa76760ccb`
- `H234598/desinfect`: `fbcc6e850fec1f4592ca519fa3e5141b11a95e60`

Die drei Stände wurden vor Beginn erneut gegen die jeweiligen Default-Branches verifiziert.

## Pflegekonvention

- Eine Phase wird erst als umgesetzt markiert, wenn ihre Dateien veröffentlicht, ihre lokalen Tests grün und die PR-Gates abgeschlossen sind.
- Der Nachweis nennt PR, Merge-Commit und die wichtigsten ausführbaren Prüfungen.
- Noch nicht implementierte optionale Bestandteile bleiben sichtbar offen; sie werden nicht stillschweigend aus dem Plan entfernt.
- Neue Erkenntnisse ändern nicht rückwirkend die kanonischen Markdown-Fachinhalte, sondern werden als eigene Content- oder Infrastrukturänderung umgesetzt.
- Behauptete Integrationen werden im Diff und durch Integrationsprüfungen nachgewiesen; reine Standalone-Generatoren gelten nicht als abgeschlossene Phase.
- Nach parallelen `main`-Änderungen werden offene Infrastruktur-PRs neu auf dem aktuellen Merge-Commit aufgebaut, statt veraltete Inhalte zurückzuspielen.

**Letzte Pflege:** 2026-07-28
