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
| 5B – Pages-Deployment | ⚠️ technisch umgesetzt | PR #11, Merge `59724c5256a5bed001164fe908dacff2d01fb11a`; Artefaktprüfung grün, produktive `page_url` noch extern zu bestätigen |
| 6 – Downloads und Provenienz | ✅ umgesetzt | PR #12, Merge `128b44b349e54dd38c9ef097a18d480c5a526c2c`; 108 Tests und alle Gates grün |
| 7 – Browser, Accessibility und Performance | 🚧 abnahmebereit | PR #14; 116 Python- und 7 Chromiumtests, axe und Budgets grün |
| 8 – optionale Erweiterungen | ⬜ offen | – |

## Abgeschlossene Phase 3

PR #6 erzeugt Navigation, Kategorie-, Gesamt-, Alphabet- und Tagindizes sowie `pages.json`, `categories.json`, `tags.json` und `build-info.json`. Die Generatoren laufen im selben atomaren Stagingverzeichnis wie die transformierten Markdown-Seiten; die resultierende Navigation wird strukturiert in `mkdocs.generated.yml` übernommen.

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

PR #8 wurde unabhängig vom Phasenstrang als repositoryweite Inhalts- und Dateinamenvereinheitlichung unter `05b8d7469ba8c1129ddfde016e43852f88bfc499` gemergt. Der PR ersetzt die frühere Zusatzbezeichnung durch **Cheatsheet**, benennt betroffene Dateien und Links um und regeneriert die kanonischen Metadaten. Der anschließend eröffnete PR #10 wurde deshalb ohne Merge und mit leerem Diff geschlossen.

## Abgeschlossene Phase 5A

PR #9 führt die schreibgeschützte Pull-Request-CI ein:

- `contents: read`, keine Secrets, kein Environment und kein Deployment;
- vollständig gepinnte Actions;
- fester Runner `ubuntu-24.04`, Python 3.12, Timeouts und Concurrency;
- Workflow-Selbstvalidierung;
- Unit-, Integrations-, Content-, Link-, Sicherheits- und Strict-MkDocs-Gates;
- byteweiser, blockierender Vergleich der kanonischen Metadaten;
- Diagnoseartefakte auch nach Fehlern;
- Dependabot für GitHub Actions und Python;
- hochpräziser Secret-/Raw-HTML-/Laufzeitasset-Scanner.

Der finale PR-Lauf bestätigte 78 bestandene Tests, null Content-, Link- oder Sicherheitsbefunde, bytegleiche kanonische Metadaten, einen grünen Strict-Build, CodeRabbit, qlty und keine offenen Review-Threads. PR #9 wurde unter `69c72997eed4fc0ac831eba696bac12b3a2f69b9` gemergt.

## Phase 5B – technischer Abschluss und verbleibende Laufzeitbestätigung

PR #11 ergänzt `.github/workflows/pages.yml` mit strikt getrennten Jobs:

1. `build` liest Inhalte, validiert das Repository, ermittelt die Pages-Basis-URL und erzeugt `site/` genau einmal;
2. `deploy` benötigt den erfolgreichen Build und veröffentlicht ausschließlich das Pages-Artefakt im Environment `github-pages`.

Sicherheits- und Betriebsmerkmale:

- Trigger nur bei Push nach `main` und manuell;
- keine Pull-Request-Veröffentlichung;
- leere globale Berechtigungen;
- Buildjob: `contents: read`, `pages: write`;
- Deploymentjob: `pages: write`, `id-token: write`;
- vollständige Action-SHA-Pins;
- dynamische `site_url` aus `configure-pages.outputs.base_url`;
- kein Checkout und kein Build im Deploymentjob;
- `needs: build` und Environment `github-pages`.

Der PR-Lauf bestätigte 90 Tests und ein sicheres Pages-Artefakt. CodeRabbit, qlty und alle Review-Threads waren grün. PR #11 wurde unter `59724c5256a5bed001164fe908dacff2d01fb11a` gemergt.

Die technische Pipeline ist damit umgesetzt. Die unabhängige Bestätigung eines produktiven Push-Deployments einschließlich ausgegebener `page_url` bleibt sichtbar offen und wird nicht als bereits erfolgt behauptet.

## Abgeschlossene Phase 6

PR #12 erzeugt einen vollständigen Downloadsatz aus demselben Checkout und `SOURCE_DATE_EPOCH` wie die Website:

- `Cheatsheets-Quellen.zip` mit kanonischen Inhalten, Git-getrackten Inhaltsassets, Lizenz und Quellprüfsummen;
- ein aus allen 86 Fachseiten neu erzeugtes `Cheatsheet-Gesamtband.md`;
- kanonische Manifestansichten und Buildreport;
- `SOURCE-SHA256SUMS.txt` und `DOWNLOAD-SHA256SUMS.txt`;
- `PROVENANCE.json` mit Commit, Zeitpunkt, Umfang und Quellbaumhash;
- JSON- und CSV-Downloadmanifest;
- eine aus den geprüften Datensätzen erzeugte Download-Landingpage.

Der Quell-ZIP verwendet stabile Reihenfolge, feste Rechte, `ZIP_STORED` und den Commitzeitpunkt. `.git`, `.github`, `.obsidian`, Buildausgaben, Tests und Entwicklungszustände sind ausgeschlossen. Unerwartete oder verlinkte Inhaltsassets blockieren fail-closed. Archivnamen werden vor der Prüfung plattformübergreifend normalisiert; Traversal-, Laufwerks-, UNC-, Steuerzeichen- und leere Punktpfade sind verboten.

Das Gesamt-Markdown verwendet die kanonische Kategorienreihenfolge, stabile Page-ID-Anker und präfixierte Abschnittsanker. Codefences werden vor und nach der Linkkonvertierung gehasht.

Der zentrale Site-Build erzeugt den Contentindex einmalig und reicht ihn an Download- und Webbuild weiter. Downloads entstehen vor MkDocs; die Landingpage verwendet reale Größen und Hashes. Die Artefakte werden erst nach erfolgreichem HTML-Build nach `site/downloads/files/` kopiert.

Der endgültige PR-Head `e95687389dfbd32ada4cf42a40adeef40ff736e6` bestand 108 Tests sowie alle Content-, Link-, Security-, Metadaten-, Pages-, CodeRabbit- und qlty-Gates ohne offene Review-Threads. PR #12 wurde per Squash unter `128b44b349e54dd38c9ef097a18d480c5a526c2c` gemergt.

Der danach versehentlich aus einem divergierten historischen Phase-6-Branch eröffnete PR #13 enthielt eine konkurrierende zweite Downloadimplementierung. Er wurde entsprechend der Pflegekonvention ohne Merge geschlossen; keine seiner Änderungen gelangte nach `main`.

## Phase 7 – Abnahmestand

PR #14 baut exakt auf dem Phase-6-Mergecommit `128b44b349e54dd38c9ef097a18d480c5a526c2c` auf und ergänzt die bisherige statische Prüfung um echte Browser-, Accessibility- und Performancegates.

### Reproduzierbare Browsertoolchain

- Node.js 24 über vollständig gepinnte `actions/setup-node`-Action;
- exakt gepinnte `@playwright/test`- und `axe-core`-Versionen in `package-lock.json`;
- `npm ci --ignore-scripts`;
- Chromiuminstallation nur über `npx --no-install`;
- wöchentliche Dependabot-Updates für npm in `Europe/Berlin`;
- ein Worker und keine verdeckten globalen npm-Abhängigkeiten;
- sicherer lokaler Testserver unter dem realen Prefix `/Cheatsheets/`.

Die Workflowpolicy erzwingt diese Verträge selbst und blockiert insbesondere Node-Abweichungen, fehlende Browsergates sowie jedes `npx`, das ein nicht lokal vorhandenes Paket nachladen könnte.

### Blockierende Chromium-Szenarien

Sieben End-to-End-Tests prüfen:

1. Start-, Kategorie-, Download-, kurze und lange Fachseite ohne Browserfehler oder fremde Origin;
2. axe auf Start- und repräsentativer Fachseite ohne `serious`- oder `critical`-Befund;
3. sichtbare Inhalte und Navigation bei deaktiviertem JavaScript;
4. Favoriten, LocalStorage, Fokusmodus, Tastaturhilfe, Escape und Suchkürzel;
5. lokale Filter und vollständige Rücksetzung;
6. 320-Pixel-Ansicht, sichtbaren Fokus, Reduced Motion sowie tastaturfokussierbare Code- und Tabellencontainer;
7. erreichbare Downloadartefakte sowie eine echte tiefe HTTP-404-Seite mit sicherem Rücklink zur Project-Page-Startseite.

### Statische Budgets

| Messwert | Blockierende Grenze | Funktionslauf `30343694759` |
|---|---:|---:|
| eigenes JavaScript, Gzip-Summe | 30 KiB | 8.410 Bytes |
| eigenes CSS, Gzip-Summe | 35 KiB | 2.187 Bytes |
| einzelne HTML-Datei | 2 MiB | max. 288.067 Bytes |
| externe Laufzeitassets | 0 | 0 |

Lighthouse-Scores werden nicht vorgetäuscht. Der Plan sieht eine blockierende Lighthouse-Schwelle erst nach einer stabilen dreifachen Messbaseline vor. Bereits blockierend sind deterministische Größen-, Origin-, axe-, Mobil- und Funktionsgates.

### Durch die echten Browserläufe gefundene und behobene Probleme

- Material versuchte bei gesetztem `repo_url` GitHub-API-Zähler abzurufen; der Repositorylink ist nun statisch und erzeugt keinen Laufzeitrequest;
- mehrere Sekundärtexte und Syntaxfarben lagen knapp unter WCAG-AA-Kontrast; ihre Farben wurden gezielt angehoben;
- Tabellencontainer waren weder horizontal scrollend noch tastaturfokussierbar;
- die Standard-404-Seite war nicht deutsch und besaß nicht den gewünschten Project-Page-sicheren Rücklink;
- das mehrere Megabyte große Gesamtband wurde unnötig zusätzlich als HTML gerendert; es bleibt nun ausschließlich verifiziertes Rohdownloadartefakt;
- drei kanonische Links auf den Gesamtband werden beim Webbuild explizit als `download`-Links auf `downloads/files/` ausgegeben;
- das Fragezeichen-Kürzel wird in der Capture-Phase verarbeitet, bevor Theme-Shortcuts es übernehmen können.

### Funktionsabnahme vor der abschließenden Statuspflege

GitHub-Actions-Lauf `30343694759` auf Head `fe4ed478fc432fcb400cf258ac63e2fdb3fb6a53` bestätigte:

- **116 von 116 Python-Tests bestanden**;
- **7 von 7 Chromiumtests bestanden**, keine Wiederholung und kein Flake;
- zwölf Kategorien, 86 Fachseiten und null Contentfehler oder -warnungen;
- null Linkfehler und null Linkwarnungen;
- null Securityfehler, -warnungen oder Informationsbefunde;
- bytegleiche kanonische Metadaten;
- vollständiger Strict-MkDocs-Build einschließlich Downloads;
- Pages-Artefakt mit 181 regulären Dateien und 19.869.192 Bytes;
- keine Symlinks, Hardlinks, Sonderdateien oder Case-Kollisionen;
- Artefakt-Baum-SHA-256 `8657ccc80fa87db95ddddb73100515f3dcd888ac7e603d44b095afe7b5808846`;
- 113 HTML-Dateien und null externe Laufzeitassets;
- versionierte Arbeitskopie nach dem Build unverändert;
- CodeRabbit und qlty grün;
- keine offenen Review-Threads.

Diese Dokumentations- und Statuspflege erzeugt bewusst einen neuen PR-Head. Phase 7 bleibt deshalb bis zum erneut grünen Validate-Lauf, abgeschlossenen Reviews und verifiziertem Merge als **abnahmebereit** markiert.

Eine Phase wird erst nach veröffentlichten Dateien, grünen Tests und PR-Gates, ohne offene Review-Threads und nach verifiziertem Merge als vollständig umgesetzt markiert.

## Verbindliche Ausgangsstände

- `H234598/Cheatsheets`: `42541f87105cb6dd178c8609cb031dc361bb59a9`
- `H234598/ADHS-Lernpfad`: `93c8c02d263ec123c1c271caf0d2deaa76760ccb`
- `H234598/desinfect`: `fbcc6e850fec1f4592ca519fa3e5141b11a95e60`

Die drei Stände wurden vor Beginn erneut gegen die jeweiligen Default-Branches verifiziert.

## Pflegekonvention

- Eine Phase wird erst als umgesetzt markiert, wenn ihre Dateien veröffentlicht, ihre Tests und PR-Gates grün, keine Review-Threads offen und der Merge verifiziert ist.
- Der Nachweis nennt PR, Merge-Commit und die wichtigsten ausführbaren Prüfungen.
- Noch nicht implementierte optionale Bestandteile bleiben sichtbar offen; sie werden nicht stillschweigend aus dem Plan entfernt.
- Neue Erkenntnisse ändern nicht rückwirkend die kanonischen Markdown-Fachinhalte, sondern werden als eigene Content- oder Infrastrukturänderung umgesetzt.
- Behauptete Integrationen werden im Diff und durch Integrationsprüfungen nachgewiesen; reine Standalone-Generatoren gelten nicht als abgeschlossene Phase.
- Nach parallelen `main`-Änderungen werden offene Infrastruktur-PRs neu auf dem aktuellen Merge-Commit aufgebaut, statt veraltete Inhalte zurückzuspielen.

**Letzte Pflege:** 2026-07-28
