# ADHS-freundliche Weboberfläche

## Ziel

Die Webseite soll Orientierung geben, ohne Inhalte zu verkürzen oder Nutzer durch Gamification, Animationen oder Kontozwang abzulenken. Alle fachlichen Markdown-Dateien bleiben kanonisch; UI-Metadaten und lokale Zustände entstehen ausschließlich in der generierten Webkopie beziehungsweise im Browser.

## Progressive Verbesserung

Die Grundseite funktioniert ohne projektspezifisches JavaScript:

- alle Fachinhalte bleiben sichtbar;
- Kategorien, Gesamtindex, alphabetischer Index, Tags und Downloads bleiben normale Links;
- die Material-Navigation und die statischen Seiten bleiben lesbar;
- lokale Werkzeuge tragen zunächst das HTML-Attribut `hidden` und werden erst nach erfolgreicher Initialisierung eingeblendet;
- ein `<noscript>`-Hinweis erklärt ausschließlich die fehlenden lokalen Komfortfunktionen.

JavaScript ergänzt:

- Favoriten;
- zuletzt gelesene Seite;
- Lesefortschritt;
- Fokusmodus;
- lokale Kategorie-, Tag-, Zeit- und Textfilter;
- Tastaturkürzel;
- Migration gespeicherter Page-IDs nach bewusst reviewten Umbenennungen.

## Startseite

Die Startseite zeigt drei primäre Entscheidungen:

1. **Hier anfangen** – zur vorhandenen Einführung;
2. **Kategorie wählen** – zur generierten Kategorienübersicht;
3. **Alle durchsuchen** – zum vollständigen Index und den lokalen Filtern.

Darunter erscheinen bei verfügbarer lokaler Speicherung:

- zuletzt gelesen;
- weiterlesen;
- Favoriten.

Es gibt keine Streaks, Punkte, Benachrichtigungen, automatisch startenden Medien oder animierten Belohnungen.

## Stabile Page-IDs

Jede generierte Fachseite erhält zusätzliches Web-Frontmatter:

```yaml
web_page_id: "p_0123456789abcdef"
web_page_type: "reference"
web_minutes: 8
web_source_path: "03-Linux-Administration/SSH-Premium-Spickzettel.md"
web_category_id: "03-Linux-Administration"
web_category_title: "Linux-, Unix- & Paketverwaltung"
```

Diese Felder werden nur in `build/docs` ergänzt. Reservierte `web_*`-Felder in einer kanonischen Quelle blockieren den Build, damit keine stillen Überschreibungen entstehen.

Die Page-ID wird weiterhin deterministisch aus dem NFC-normalisierten Quellpfad erzeugt. Umbenennungen werden in `config/page-id-aliases.json` abgebildet. Das Register:

- besitzt eine feste Schema-Version;
- darf kein Symlink sein;
- darf keine aktuelle ID als veraltet markieren;
- darf nur auf eine tatsächlich vorhandene aktuelle Fachseite zeigen;
- wird deterministisch als `data/page-id-aliases.json` veröffentlicht.

## Lokaler Zustand

Speicherschlüssel:

```text
cheatsheets.ui.v1
```

Gespeichert werden ausschließlich:

- Page-IDs;
- Abschnittsanker;
- Favoritenstatus;
- Lesefortschritt zwischen 0 und 1;
- Zeitpunkte;
- Fokusmodus und Shortcut-Präferenz.

Nicht gespeichert werden:

- Suchbegriffe;
- aufgerufene Inhalte;
- Freitext;
- Code;
- IP-Adressen;
- Gerätekennungen;
- Kontodaten.

Fehlerhaftes JSON, eine alte Schemanummer, deaktivierte Cookies/Speicher oder eine Speicherquota führen zu einem leeren In-Memory-Zustand. Die Seite bleibt nutzbar und zeigt bei Fachseiten einen unaufdringlichen Hinweis.

## Filter

Die Startseite lädt die bereits beim Build erzeugten Dateien:

- `pages.json`;
- `categories.json`;
- `tags.json`.

Alle Requests müssen dieselbe Origin wie die aktuelle Seite besitzen. Treffer werden ausschließlich mit DOM-Methoden und `textContent` aufgebaut; HTML-Strings werden nicht injiziert. Suchbegriffe verbleiben im Eingabefeld und werden nicht in `localStorage` geschrieben.

Die Ergebnisliste wird in Portionen von 24 Einträgen gezeigt. Weitere Treffer erscheinen erst nach einer bewussten Aktion.

## Tastatur

| Taste | Funktion |
|---|---|
| `/` | Material-Suche fokussieren |
| `?` | Tastaturhilfe öffnen |
| `Esc` | Hilfe oder Fokusmodus schließen |
| `f` | aktuelle Fachseite als Favorit umschalten |
| `g`, dann `i` | Gesamtindex |
| `g`, dann `k` | Kategorien |
| `g`, dann `d` | Downloads |

Kürzel werden nicht in Eingabefeldern, Auswahlfeldern oder editierbaren Bereichen verarbeitet. Jede Funktion besitzt eine sichtbare Alternative. Die Kürzel lassen sich im Hilfedialog lokal deaktivieren.

## Fokusmodus

Der Fokusmodus blendet Header, Tabs, Seitenleisten und Footer aus, nicht aber den fachlichen Inhalt oder die Seitenwerkzeuge. Er ist lokal, jederzeit über die sichtbare Schaltfläche oder `Esc` beendbar und verändert keine Quellseite.

## Reizreduktion und mobile Nutzung

- begrenzte Inhaltsbreite;
- ruhige Karten ohne automatisch bewegte Elemente;
- sichtbarer `:focus-visible`-Rahmen;
- `prefers-reduced-motion`;
- eigenständig horizontal scrollbare Codeblöcke und Tabellen;
- einspaltige Filter auf schmalen Bildschirmen;
- Systemschrift statt externer Fonts;
- Dark- und Light-Mode des Material-Themes.

## Prüfungen

```bash
python -m pytest -q \
  tests/test_build_docs.py \
  tests/test_ui_config.py \
  tests/test_ui_contract.py
```

Wenn Node.js vorhanden ist, prüft die Testsuite zusätzlich alle lokalen JavaScript-Dateien mit `node --check`. Echte No-JavaScript-, Tastatur-, Mobile- und Accessibility-Browsertests folgen als blockierender Bestandteil von Phase 7.
