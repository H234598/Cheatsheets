# GitHub-Pages-Cheatsheets – Implementierungsstatus

Dieser Fortschrittsnachweis wird mit jeder Planphase aktualisiert. Verbindliche Sollbeschreibung ist der vollständige Implementierungsplan aus dem Arbeitsauftrag; Abweichungen werden hier begründet dokumentiert.

| Phase | Status | Nachweis |
|---|---|---|
| 0A – Sicherheitsbaseline | ✅ umgesetzt | PR #1, Merge `fdf24c369dded98a63af046c174d29d5636c080b` |
| 0B – Inventur und Baseline | ✅ umgesetzt | PR #2, Merge `48f2a518f52e4d595a0887bd2de3ee45fcc3f19a`, 8 Tests |
| 1 – Linkmodell und Callouts | ✅ umgesetzt | PR #3, Merge `7fcccdca800b60dc2fee55de1b5e3b99614e1c3c`, 21 Tests |
| 2 – MkDocs-Basis | ✅ umgesetzt | PR #4, Merge `81ef6b66abb64116d153d8558ea6a230eee676e9`, 26 Tests |
| 3 – Navigation, Indizes und Suche | ✅ umgesetzt | PR #6, Merge `7db8f713aca07e67b481f9fbcb00553f6a555495`; CodeRabbit und qlty grün, drei Reviewregressionen ergänzt |
| 4 – ADHS-freundliche Oberfläche | 🚧 in Umsetzung | Branch `agent/adhs-ui`; progressive UI, lokale Zustände, Filter, Fokusmodus und Tastaturhilfe |
| 5A – PR-CI | ⬜ offen | – |
| 5B – Pages-Deployment | ⬜ offen | – |
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

## Laufende Phase 4

Die kanonischen Markdown-Dateien bleiben unverändert. Der generierte Webbaum erhält stabile UI-Metadaten und ein geprüftes Page-ID-Migrationsregister. Die Oberfläche ergänzt progressiv:

- drei primäre Startaktionen;
- lokale Favoriten, zuletzt gelesen und Lesefortschritt;
- Fokusmodus;
- lokale Kategorie-, Tag-, Text- und Zeitfilter;
- Tastaturhilfe mit lokal abschaltbaren Kürzeln;
- robuste Fallbacks bei deaktiviertem JavaScript oder nicht verfügbarem `localStorage`;
- responsive, reizreduzierte Karten-, Fokus- und Dialogdarstellung.

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

**Letzte Pflege:** 2026-07-28
