---
title: "Vim und .vimrc – Umsetzungsplan und Veröffentlichungsnachweis"
aliases:
  - "Vim und Vimrc Veröffentlichungsplan"
  - "Cheatsheets Vim Erweiterung 2026-10-12"
tags:
  - projekt/cheatsheets
  - plan/umsetzung
  - vim
  - vimrc
  - dokumentation
  - github-pages
type: plan
status: review
date: '2026-10-12'
created: '2026-10-12'
modified: '2026-10-12'
updates:
  - date: '2026-10-12'
    change: "Bestandsaufnahme abgeschlossen; Umsetzungsplan vor den Inhaltsänderungen angelegt."
repository: "H234598/Cheatsheets"
base_commit: "28c5218486479ef669d5c36e0392441ebcbe0604"
---

# Vim und .vimrc – Umsetzungsplan und Veröffentlichungsnachweis

## Ziel und Auftrag

Zwei eigenständige, ausführliche deutschsprachige Fachseiten für **Vim** und **die `.vimrc`** erstellen und auf der bestehenden Cheatsheets-Website veröffentlichen. Beide Markdown-Quellen werden vollständig zum Download bereitgestellt.

Der Auftrag umfasst Erstellung und Veröffentlichung. Die Umsetzung folgt den bestehenden Konventionen des aktuellen Default-Branches, dem Superpowers-Planungs- und Prüfablauf sowie dem ausdrücklichen Wunsch nach vollständigen Obsidian-Dokumenten. Fachrecherche und Ausarbeitung der beiden Seiten können parallel erfolgen; Integration, Veröffentlichung und Ergebnisprüfung erfolgen geordnet.

## Bestandsaufnahme und verbindliche Grundlage

| Aspekt | Festgestellter Ausgangspunkt |
|---|---|
| Repository | [H234598/Cheatsheets](https://github.com/H234598/Cheatsheets) |
| Verbindlicher Quellstand | [main, Commit 28c5218](https://github.com/H234598/Cheatsheets/commit/28c5218486479ef669d5c36e0392441ebcbe0604) |
| Zielkategorie | `02-Versionierung-Entwicklung` – Versionierung, Entwicklung & Editoren |
| Bestehende verwandte Inhalte | Vier Neovim-Seiten, Git, Linux-Administration und Obsidian-Markdown |
| Inhaltsmodell | `type: reference`, `status: fertig`, strukturierte Frontmatter und eindeutige Titel/Aliases |
| Navigation | Jede neue Fachseite muss genau einmal im Abschnitt `## Seiten` des Kategorieindex stehen |
| Veröffentlichung | MkDocs Material; generierte Webkopie unter `build/`, fertige Website unter `site/`; GitHub Pages aus Actions-Artefakt |
| Kanonische Metadaten | `MANIFEST.csv`, `MANIFEST.md`, `BUILD-REPORT.yaml`, `SHA256SUMS.txt` werden mit `scripts/build_manifest.py` erzeugt |
| Downloadmodell | Markdown-Einzelseiten, Kategorienpakete, Gesamtpaket, Gesamtband und Offline-HTML werden vom bestehenden Build bedient |
| Produktive Adresse | [cheatsheets.telacore.org](https://cheatsheets.telacore.org/) |

Projektgrundlagen: [Contentmodell](../../WEB-CONTENTMODELL.md), [Webbuild](../../WEB-BUILD.md), [Downloadmodell](../../WEB-DOWNLOADS.md), [Tests](../../WEB-TESTS.md), [Wartung und Veröffentlichung](../../WEB-WARTUNG.md) und [GitHub-Regeln](../../../.github/README.md).

## Inhaltlicher Entwurf

### Seite 1: Vim – Cheatsheet

**Datei:** `02-Versionierung-Entwicklung/Vim-Cheatsheet.md`.

Die Seite beginnt mit dem schnellen Einstieg einschließlich Speichern und Verlassen. Danach erklärt sie das Modusmodell und die kombinierbare Befehlssprache. Tabellen und vollständig erläuterte Beispiele behandeln Navigation, Textobjekte, Änderungen, Register, Zwischenablage, Suche und Ersetzung, Sprungmarken, Makros, Buffer, Fenster, Tabs, Quickfix, Diffmodus, externe Befehle, Hilfe und Wiederherstellung.

Wichtige Präzisierungen: Vim und Neovim haben unterschiedliche Konfigurationen; Tabs enthalten Fensterlayouts; Register und Zwischenablage sind zu unterscheiden; `:write` und `:saveas` ändern die Dateibindung unterschiedlich; Suche und Ersetzung hängen von Optionen und expliziten Flags ab. Verwerfende Befehle erhalten ihre konkrete Wirkung direkt daneben.

### Seite 2: .vimrc – Konfiguration und Praxis

**Datei:** `02-Versionierung-Entwicklung/Vimrc-Konfiguration-Cheatsheet.md`.

Die Seite erklärt den tatsächlich verwendeten Konfigurationspfad, Startreihenfolge, `$MYVIMRC`, `defaults.vim`, klassische Vimscript-Syntax und das gezielte Neuladen. Ein klar abgegrenzter, kommentierter `.vimrc`-Block bietet eine brauchbare Ausgangskonfiguration. Darauf folgen Optionen, lokale Dateitypeinstellungen, Mappings und Leader, wiederholt ladbare Autocommands, Farbe und Terminal, Zwischenablage, Swap/Backup/Undo, optionale Pakete und systematische Diagnose.

Die Basis richtet sich an reguläre Vim-9.x-Installationen. Plattform- oder Buildmerkmale werden kenntlich gemacht und erforderlichenfalls mit Featureprüfungen geschützt. Es wird keine bestimmte aktuelle Patchversion vorausgesetzt. Optionale Erweiterungen stehen außerhalb der Basiskonfiguration. Sicherheitsrelevante Nebenwirkungen von Konfigurationscode, Plugins und gespeicherten Dateikopien werden unmittelbar am jeweiligen Beispiel erläutert.

## Qualitätsanforderungen

- Alle neuen redaktionellen Markdown-Dateien enthalten mindestens `tags`, `type`, `status`, `updates`, `date`, `aliases`, `created` und `title`; `modified` ergänzt die vorhandene Projektkonvention.
- Inhalte sind eigenständig formuliert, vollständig und auf Deutsch. Befehle, Optionsnamen und Dateipfade behalten ihre originale Schreibweise.
- Interne Links verwenden die bestehenden Obsidian-kompatiblen Konventionen. Beide Seiten verlinken einander und geeignete vorhandene Fachseiten.
- Quellen stammen aus der offiziellen Vim-Dokumentation beziehungsweise dem offiziellen Vim-Repository. Abrufdatum und lokale `:help`-Einstiege werden dokumentiert.
- Code-Fences bleiben beim Webbuild bytegleich. Vimscript in Tabellen darf nicht an Markdown-Pipes zerbrechen.
- Eine minimale `.vimrc` wird nach Möglichkeit mit einer echten Vim-Binary in einer temporären Umgebung geladen und geprüft. Falls keine ausführbare Vim-Umgebung beschaffbar ist, wird diese Prüfung ausdrücklich als nicht ausgeführt dokumentiert.
- Bestehende Fachinhalte bleiben vollständig erhalten. Der Gesamtband erhält die beiden neuen Inhalte zusätzlich.
- Veröffentlichungsbelege unterscheiden lokale Prüfungen, GitHub-CI, Pages-Deployment und tatsächlich abgerufene Live-Seiten.

## Umsetzungsschritte

### Meilenstein 1 – Quellen und Plan

- [x] Lokale Arbeitsumgebung prüfen und das ausdrücklich festgelegte Repository beschaffen.
- [x] Aktuellen `main`-Commit, Kategorieaufbau, Publikationsmodell und Workflow-Regeln lesen.
- [x] Offizielle Vim-Dokumentation aufrufen; beide fachlichen Recherchen unabhängig beginnen.
- [x] Dateinamen, Inhalte, Integrationsstellen und Prüfungen vor der Implementierung festlegen.
- [x] Arbeitsbranch `docs/vim-vimrc-2026-10-12` aus dem geprüften Stand anlegen.

### Meilenstein 2 – Zwei vollständige Fachseiten

- [x] `Vim-Cheatsheet.md` mit Zweck, Inhaltsnavigation, Tabellen, Praxisbeispielen, Fehlersuche, Quellen und verwandten Notizen erstellen.
- [x] `Vimrc-Konfiguration-Cheatsheet.md` mit vollständiger Basisdatei, Erläuterungen, optionalen Einstellungen, Diagnose, Quellen und Querverweisen erstellen.
- [x] Eindeutige Titel und Aliases sowie die vollständigen Dokumenteneigenschaften prüfen.
- [x] Beide Seiten unabhängig fachlich gegenlesen; konkrete Funde korrigieren.
- [x] `.vimrc` aus dem veröffentlichten Codeblock extrahieren und Syntax, mehrfaches Laden sowie wesentliche globale und dateitypbezogene Optionen prüfen.

### Meilenstein 3 – Integration und reproduzierbare Prüfung

**Redaktionelle Integrationsdateien:**

- `02-Versionierung-Entwicklung/INDEX.md`: beide Seiten ergänzen; Seitenzahl, Umfang und Beschreibung aktualisieren.
- `INDEX.md`: Kategorie- und alphabetischen Index ergänzen; neue Gesamtzahl und Stand aufnehmen.
- `00-START-HIER.md`: neue Seiten als aktuelle Ergänzungen verlinken; Umfang und Kategorienzahl korrigieren.
- `README.md`: nachprüfbare aktuelle Gesamtzahlen und Dokumentstand übernehmen.
- `CHANGELOG.md`: beide Ergänzungen und ihre Integration als neue Inhaltsversion dokumentieren.
- `Cheatsheet-Gesamtband.md`: beide vollständigen Artikelkörper ergänzen; bestehende Artikel erhalten; Dokumentkopf aktualisieren.

**Notwendige Integrationskorrektur nach erster Prüfung:** `scripts/validate_content.py` erwartet bisher standardmäßig exakt 86 Fachseiten. Der CLI-Lauf hat die Erweiterung mit `BL001` blockiert. Der bestehende Sollwert wird gezielt auf 88 erhöht; Kategorienzahl und sämtliche Prüfregeln bleiben erhalten. Die erfolgreiche vollständige Inhaltsprüfung mit 88 echten Fachseiten belegt die Korrektur.

**Abgeleitete Dateien:** `MANIFEST.csv`, `MANIFEST.md`, `BUILD-REPORT.yaml`, `SHA256SUMS.txt` über den vorhandenen Generator aktualisieren. Generierte Ausgaben unter `build/` und `site/` bleiben Buildartefakte.

- [x] Redaktionsdateien aktualisieren und vorhandene Angaben aus den tatsächlichen Fachquellen neu berechnen.
- [x] Den veralteten Standard-Sollwert des Inhaltsprüfers von 86 auf 88 Fachseiten aktualisieren.
- [x] Kanonische Metadaten mit `python scripts/build_manifest.py --update-committed` erzeugen.
- [x] Bytegleiche Reproduzierbarkeit mit `python scripts/build_manifest.py --check` nachweisen.
- [x] `python scripts/validate_content.py --report build/reports/content.json` ausführen.
- [x] `python scripts/validate_links.py --report build/reports/links.json` ausführen.
- [x] `python scripts/validate_security.py --report build/reports/security.json` ausführen.
- [x] Relevante vorhandene Tests für Inhaltsmodell, Manifest, Links, Navigation und Downloads ausführen; die vollständige CI bleibt Veröffentlichungskriterium.
- [x] Vollständigen Strict-Build mit den exakt gepinnten Abhängigkeiten ausführen.
- [x] Beide generierten Seiten, ihre Querverweise und Markdown-Downloadziele prüfen.
- [x] Den endgültigen Änderungsumfang gegenlesen; sachfremde oder versehentliche Änderungen ausschließen.

**Prüfschwerpunkte:**

| Risiko | Prüfung |
|---|---|
| Verwechslung Vim/Neovim | Klassisches Vimscript, Vim-Hilfe und Startoptionen im Gegenlesen prüfen |
| Nicht lauffähige `.vimrc` | Original-Codeblock mit echtem Vim laden; aussagekräftige Options-/Autocommandprüfungen |
| `FileType`-Regeln beim Neuladen | Benannte Augroup, `autocmd!` innerhalb der Gruppe, mehrmaliges Laden ohne Duplikate |
| Seite nicht auffindbar | Kategorieindex, Gesamtindex, Suche und erzeugte Route prüfen |
| Veraltete Downloadpakete | Manifestvergleich, tatsächliche Paketmitglieder und vollständiger Gesamtband |
| Fehler beim Veröffentlichen | PR-/Commitprüfungen, erfolgreicher Pages-Lauf und HTTP-/Inhaltsabruf der produktiven Seiten |

### Meilenstein 4 – Veröffentlichung und Übergabe

- [ ] Geprüfte Änderungen committen und den Arbeitsbranch auf GitHub bereitstellen.
- [ ] Pull Request gegen den aktuellen `main` mit Inhalt, Zweck und Prüfnachweisen eröffnen.
- [ ] CI und vorhandene Reviewanforderungen prüfen; neue relevante Funde bearbeiten.
- [ ] Bei erfüllten Voraussetzungen den PR im Rahmen des Veröffentlichungsauftrags mergen.
- [ ] Den resultierenden GitHub-Pages-Lauf bis zum abgeschlossenen Deployment verfolgen.
- [ ] Beide produktiven Seiten abrufen und Titel, wesentliche Inhalte sowie Downloads verifizieren.
- [ ] Diesen Plan um tatsächliche Ergebnisse, Commit/PR, Workflow-Links und gegebenenfalls verbleibende Grenzen ergänzen.
- [ ] Beide vollständigen Markdown-Dateien und den vollständigen Umsetzungsnachweis als Downloads verlinken.

## Fortschritt und Prüfnachweise

### Ausgangsprüfung

- Frischer Checkout von `main` auf Commit `28c5218486479ef669d5c36e0392441ebcbe0604`; keine vorhandenen lokalen Änderungen.
- Kanonische Metadaten am Ausgangsstand: reproduzierbar und aktuell.
- Inhaltsmodell am Ausgangsstand: **86 Fachseiten, 12 Kategorien, 0 Fehler, 0 Warnungen**.
- Linkprüfung am Ausgangsstand: **0 Fehler, 0 Warnungen**.
- Exakt gepinnte Pythonabhängigkeiten in eigener virtueller Umgebung installiert; `pip check`: keine Abhängigkeitskonflikte.
- Arbeitsbranch angelegt; beide Fachartikel werden parallel ausgearbeitet.

### Prüfwerkzeuge und Ausgangs-CI

- 45 vorhandene Tests für Inhaltsmodell, Manifest, Links, Navigation und Downloads bestanden am Ausgangsstand.
- Die letzten produktiven Läufe für den Ausgangscommit waren erfolgreich: [Validate](https://github.com/H234598/Cheatsheets/actions/runs/31550918754) und [Pages](https://github.com/H234598/Cheatsheets/actions/runs/31550918762).
- Vim 9.2.0000 wurde aus dem [offiziellen Quellcommit e7e2101](https://github.com/vim/vim/commit/e7e21018fc0b60c153c8e668f696d95e574cc5a4) als temporäres Prüfwerkzeug gebaut. Erforderliche Editorfunktionen sind vorhanden; GUI und eine echte Desktop-Zwischenablage werden damit nicht getestet.
- Die exakt gepinnten npm-Pakete ließen sich installieren. Der lokale Chromium-Download für Playwright lieferte jedoch kein gültiges ZIP; lokale Playwright-Browsertests sind deshalb vorerst nicht ausführbar. Die vorhandene GitHub-CI bleibt für diesen Prüfumfang maßgeblich.

Weitere Ergebnisse werden ausschließlich nach Durchführung ergänzt.

## Quellen für den fachlichen Einstieg

- [Vim: offizielle Dokumentationsübersicht](https://www.vim.org/docs.php).
- [Vim: Quick Reference](https://vimhelp.org/quickref.txt.html).
- [Vim: Einstellungen und vimrc](https://vimhelp.org/usr_05.txt.html).
- [Vim: Start und Konfigurationsdateien](https://vimhelp.org/starting.txt.html).
- [Vim: vollständiges offizielles Repository](https://github.com/vim/vim).

Die einzelnen Fachseiten führen zusätzliche, thematisch zugeordnete Primärquellen auf. Recherchetag: **12. Oktober 2026**.

### Erste fachliche und integrative Befunde

- Der unabhängige Review fand einen mehrdeutigen `[[INDEX]]`-Verweis in der Vim-Seite. Er wurde durch den vollständigen Kategorienpfad ersetzt.
- Der echte Basistest zeigte, dass das mitgelieferte Python-Filetype-Plugin die globale Tabdarstellung auf 4 setzte. Die Python-Regel und das passende `after/ftplugin`-Beispiel setzen nun ausdrücklich `tabstop=8`; die erwartete Darstellung bleibt damit nachvollziehbar.
- Danach bestanden **30 Assertions mit Vim 9.2.0000**, unter anderem dreifaches Laden derselben Basisdatei, unveränderte drei Autocommands, Mappings, Schutzoptionen, Python/YAML/Make-Werte, Suche/Ersetzung, Register und Dateibindung. Exitcode 0, leere Fehlerliste.
- Zusätzlich haben die Fachautoren 13 Kernbefehlsprüfungen sowie den optionalen Zustands-/Undo-Block mit Leerzeichen und Komma im Zielpfad erfolgreich geprüft. Neue Zustandsverzeichnisse hatten Unix-Rechte `0700`; eine echte Undo-Datei wurde erzeugt.
- Direkter Shell-Push ist mangels Git-Zugangsdaten nicht verfügbar. Für Branch, Commit und PR wird die bereits verbundene GitHub-Integration verwendet.

### Abgeschlossene lokale Prüfung

| Prüfung | Ergebnis |
|---|---|
| Vollständige vorhandene Python-Test-Suite | **132 bestanden** |
| Echte Vim-Basis- und Befehlsprüfung | **30 Assertions bestanden**, dreifaches Laden, Exitcode 0 |
| Zusätzlicher unabhängiger Filetype-Test | **16 Assertions bestanden**, Wechsel Python → Text → Python → Make |
| Inhaltsmodell | **88 Fachseiten, 12 Kategorien, 0 Fehler, 0 Warnungen** |
| Interne Links und Callouts | **0 Fehler, 0 Warnungen** |
| Kanonische Metadaten | Generatorvergleich bytegleich |
| Sicherheitsprüfung | Keine blockierenden Befunde |
| Vollständiger Strict-Build mit Online- und Offline-Ausgabe | Erfolgreich; **107 HTML-Quellseiten** einschließlich generierter Übersichten |

Vier externe Quellenanker wurden nach dem unabhängigen Review korrigiert. Ein zusätzlicher Reviewhinweis zu den relativen Planverweisen erwies sich bei direkter Pfadauflösung als unbegründet: Die fünf `../../WEB-*.md`-Ziele liegen tatsächlich unter `docs/` und sind vorhanden.
