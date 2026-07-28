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
| 5B – Pages-Deployment | ✅ umgesetzt und produktiv bestätigt | PR #11, Merge `59724c5256a5bed001164fe908dacff2d01fb11a`; GitHub Actions, `cheatsheets.telacore.org`, DNS, HTTPS und Aliase am 2026-07-28 durch den Betreiber bestätigt |
| 6 – Downloads und Provenienz | ✅ umgesetzt | PR #12, Merge `128b44b349e54dd38c9ef097a18d480c5a526c2c`; 108 Tests und alle Gates grün |
| 7 – Browser, Accessibility und Performance | ✅ umgesetzt | PR #14, Merge `2f01ca09084ecf94bb9faad9221c1a80ec09237b`; 116 Python- und 7 Chromiumtests, axe und Budgets grün |
| 8A – Offline-HTML | ✅ umgesetzt | PR #17, Merge `80a2eca257e7c6c668fb633f6de0062eb6e64f89`; 132 Python- und 9 Chromiumtests, unabhängige Archivprüfung grün |
| 8B – Wissensgraph | ⬜ offen | – |
| 8C – PDF/EPUB und weitere optionale Exporte | ⬜ offen | – |

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

## Abgeschlossene Phase 5B

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

Die zuvor noch offene produktive Laufzeitabnahme wurde am 2026-07-28 durch den Betreiber abgeschlossen und ausdrücklich bestätigt:

- Pages-Quelle ist **GitHub Actions**;
- kanonische Custom Domain ist `https://cheatsheets.telacore.org/`;
- DNS-CNAME ist aktiv;
- HTTPS wird erzwungen und ohne Zertifikatsfehler ausgeliefert;
- zusätzliche Alias-Subdomains werden vor GitHub per HTTPS-Redirect auf die kanonische Domain geführt;
- Website und Weiterleitungen funktionieren produktiv.

Diese Abnahme ist eine Betreiberbestätigung aus der realen Zielumgebung. Sie ersetzt nicht die technischen Buildgates, ergänzt sie aber um den im Plan geforderten produktiven Betriebsnachweis. Damit erfüllt Phase 5B sämtliche Abschlussbedingungen.

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

## Abgeschlossene Phase 7

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

| Messwert | Blockierende Grenze | Finaler Lauf `30344111731` |
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

### Endgültige Abnahme und Merge

GitHub-Actions-Lauf `30344111731` auf dem endgültigen Head `e9e546b10a3723c4a7bdb63028de8e5642fd3798` bestätigte:

- **116 von 116 Python-Tests bestanden**;
- **7 von 7 Chromiumtests bestanden**, keine Wiederholung und kein Flake;
- zwölf Kategorien, 86 Fachseiten und null Contentfehler oder -warnungen;
- null Linkfehler und null Linkwarnungen;
- null Securityfehler, -warnungen oder Informationsbefunde;
- bytegleiche kanonische Metadaten;
- vollständiger Strict-MkDocs-Build einschließlich Downloads;
- Pages-Artefakt mit 181 regulären Dateien und 19.869.192 Bytes;
- keine Symlinks, Hardlinks, Sonderdateien oder Case-Kollisionen;
- Artefakt-Baum-SHA-256 `2d2f6b37f31782c12d0fb5765d246ef2d1e9bd6549467d8cafab7920c0cd2313`;
- 113 HTML-Dateien und null externe Laufzeitassets;
- versionierte Arbeitskopie nach dem Build unverändert;
- CodeRabbit und qlty grün;
- keine offenen Review-Threads.

PR #14 wurde anschließend per Squash gemergt. Der Mergecommit `2f01ca09084ecf94bb9faad9221c1a80ec09237b` wurde auf `main` verifiziert. Damit erfüllt Phase 7 sämtliche Abschlussbedingungen.

## Abgeschlossene Phase 8A

PR #17 ergänzt die Downloadpipeline um:

```text
Cheatsheets-Offline-HTML.zip
```

Das Paket wird aus demselben Contentindex, Checkout, Quellcommit und `SOURCE_DATE_EPOCH` wie die Online-Site erzeugt. Es besitzt eine getrennte MkDocs-Konfiguration mit `use_directory_urls: false`, relative `.html`-Links und einen sichtbaren Offline-Hinweis.

Enthalten sind:

- der vollständige statische HTML-Baum;
- lokale Stylesheets, JavaScript- und Themeassets;
- die bereits geprüften Basisdownloads ohne rekursive Aufnahme des Offline-ZIPs;
- `OFFLINE-LESEN.txt`;
- ein ausschließlich an `127.0.0.1` gebundener `offline-server.py`;
- `OFFLINE-SHA256SUMS.txt`;
- `OFFLINE-MANIFEST.json` mit Quellcommit, Zeitpunkt, Dateihashes und Baumhash.

Der Generator und der unabhängige Validator prüfen fail-closed:

- ZIP-Pfade, Reihenfolge, Rechte und Zwei-Sekunden-Zeitauflösung;
- Größen- und Eintragslimits;
- Symlinks, Hardlinks, Sonderdateien und Case-Kollisionen;
- Manifest, Einzelhashes, Offline-Prüfsummen und Baumhash;
- sämtliche lokalen HTML-/CSS-Ziele und Fragmentanker;
- root-relative Links, Pfadflucht, Backslashes und unerlaubte URL-Schemata;
- externe Laufzeitassets, `<base>` und Meta-Refresh;
- atomare Extraktion ausschließlich unter `build/`.

Bewusst anklickbare externe Quell-, Canonical-, `mailto`- und `tel`-Links bleiben erlaubt; sie werden nicht beim Seitenladen angefordert. Externe Fonts, Skripte, Styles, Bilder oder andere Laufzeitassets bleiben verboten.

Die Pull-Request-CI baut Online- und Offline-Site, validiert das fertige ZIP unabhängig, entpackt es atomar und startet zwei lokale Testserver. Zusätzlich werden zwei Offline-Chromium-Szenarien ausgeführt:

1. vollständige lokale Funktion über HTTP einschließlich Filter, relativer Fachseiten- und Tastaturnavigation sowie null fremder Requests;
2. lesbarer und navigierbarer No-JavaScript-Fallback direkt über `file://`.

Der endgültige GitHub-Actions-Lauf `30365011519` auf Head `50de56d89c913f2429efc2e063f04e1b29d1a169` bestätigte:

- **132 von 132 Python-Tests bestanden**;
- **9 von 9 Chromiumtests bestanden**, davon zwei Offline-Szenarien;
- zwölf Kategorien, 86 Fachseiten und 117 bekannte Markdownseiten;
- null Content-, Link- oder Sicherheitsbefunde;
- bytegleiche kanonische Metadaten;
- vollständiger Online- und Offline-Strict-Build;
- Offline-ZIP mit 184 Dateien und 20.024.409 Bytes;
- Offline-ZIP-SHA-256 `45bf82c99849efb74d57cad481620e3431ebc0b88607c2e75aa9ae31defda28f`;
- Offline-Baum-SHA-256 `fe8c2296c7c72880d2ae490b397241b18e0a5c5d607a4ec775b059460d937489`;
- 36.788 geprüfte lokale Offline-Referenzen und 799 ausschließlich anklickbare externe Links;
- Pages-Artefakt mit 183 regulären Dateien und 39.899.127 Bytes;
- Pages-Baum-SHA-256 `3db413941cf8f889fb9c371d3c5a9e674064bd42c2a3b87cbc933052dbbf28a5`;
- eigenes JavaScript mit 9.067 Gzip-Bytes und eigenes CSS mit 2.325 Gzip-Bytes;
- 113 Online-HTML-Dateien und null externe Laufzeitassets;
- versionierte Arbeitskopie nach dem Build unverändert;
- CodeRabbit und qlty grün;
- keine offenen Review-Threads.

Frühere rote Läufe haben reale Integrationsfehler sichtbar gemacht und wurden nicht als Flakes ignoriert:

- ungerade Commitsekunden mussten auf die Zwei-Sekunden-Auflösung des ZIP-Formats normalisiert werden;
- Online-Verzeichnislinks aus Templates und Tastaturkürzeln benötigten explizite Offline-`.html`-Ziele;
- der lokale Testserver leitete einen Root-Mount `/` auf sich selbst um und verhinderte dadurch den Teststart;
- ein Workflowpolicy-Selbsttest verwendete zunächst fragile Python-Zeilenfortsetzungen und wurde durch eindeutige Befehlsmutationen ersetzt.

Alle Ursachen sind mit Unit-, Vertrags- oder Browsertests abgesichert. PR #17 wurde anschließend per Squash gemergt. Der Mergecommit `80a2eca257e7c6c668fb633f6de0062eb6e64f89` wurde auf `main` verifiziert. Damit erfüllt Phase 8A sämtliche Abschlussbedingungen.

Die übrigen optionalen Erweiterungen – Wissensgraph, PDF/EPUB, PWA oder signierte Attestations – bleiben getrennt offen. Sie werden weder als erledigt markiert noch mit dem Offline-PR vermischt.

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
