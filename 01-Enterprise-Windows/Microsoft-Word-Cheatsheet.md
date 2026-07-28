---
title: "Microsoft Word – Cheatsheet"
aliases: ["MS Word Cheatsheet", "Word Shortcuts", "Word Dokumente"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [microsoft, word, office, documents, shortcuts]
source: "https://support.microsoft.com/de-de/office/tastenkombinationen-in-word-95ef89dd-7142-4b50-afb2-f762f663ceb2"
---

# Microsoft Word – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für belastbare Word-Dokumente: Formatvorlagen, Gliederung, Abschnitte, Felder, Verzeichnisse, Überarbeiten, Serienbriefe, Barrierefreiheit und Tastenkürzel.

## Inhalt

- [[#Dokumentmodell]]
- [[#Formatvorlagen statt Handarbeit]]
- [[#Seiten und Abschnitte]]
- [[#Felder, Verweise und Verzeichnisse]]
- [[#Überarbeiten und Zusammenarbeit]]
- [[#Tabellen, Bilder und Beschriftungen]]
- [[#Serienbriefe]]
- [[#Wichtige Tastenkürzel]]
- [[#Fehlerdiagnose und Reparatur]]

## Dokumentmodell

```text
Dokument
├── Abschnitte
│   ├── Seitenformat/Kopf- und Fußzeilen
│   └── Spalten/Nummerierung
├── Absätze
│   └── Absatzformatvorlage
├── Zeichen
│   └── Zeichenformatvorlage
├── Felder/Querverweise
└── eingebettete/verknüpfte Objekte
```

> [!important]
> Professionelle Dokumente werden über Formatvorlagen, Abschnitte, Felder und strukturierte Verweise aufgebaut. Manuelles „Leerzeichen, Enter, Fett, Schriftgröße“ führt zu instabilen Layouts.

## Formatvorlagen statt Handarbeit

### Empfohlenes Set

| Zweck | Vorlage |
|---|---|
| Fließtext | Standard/Normal oder eigene Textkörper-Vorlage |
| Kapitel | Überschrift 1 |
| Unterkapitel | Überschrift 2/3 |
| Bild-/Tabellentitel | Beschriftung |
| Zitat/Hinweis | eigene Absatzvorlage |
| Code | eigene Monospace-Vorlage ohne automatische Sprachprüfung |

Formatvorlagenbereich:

```text
Ctrl + Alt + Shift + S
```

Formatierung anzeigen:

```text
Shift + F1
```

Direkte Zeichenformatierung entfernen:

```text
Ctrl + Leertaste
```

Absatzformatierung auf Vorlage zurücksetzen:

```text
Ctrl + Q
```

### Überschriften sauber nummerieren

1. Überschrift-1/2/3-Formatvorlagen verwenden.
2. **Liste mit mehreren Ebenen** wählen.
3. Ebenen mit den Überschriftformatvorlagen verknüpfen.
4. Keine Kapitelnummern per Hand eintippen.

## Seiten und Abschnitte

| Element | Wirkung |
|---|---|
| Seitenumbruch | neue Seite, gleiche Abschnittseinstellungen |
| Abschnittsumbruch „Nächste Seite“ | neue Seite und neue Layout-/Kopfzeilenlogik |
| Abschnittsumbruch „Fortlaufend“ | neuer Abschnitt auf derselben Seite |
| „Mit vorheriger verknüpfen“ | Kopf-/Fußzeile übernimmt Vorgänger |

Steuerzeichen ein-/ausblenden:

```text
Ctrl + Shift + 8
```

Seitenumbruch:

```text
Ctrl + Enter
```

> [!warning]
> Leere Absätze sind kein Seitenlayout. Bei „mysteriösen“ Kopfzeilen, Seitennummern oder Querformatseiten zuerst Abschnittsumbrüche und Verknüpfungen sichtbar machen.

## Felder, Verweise und Verzeichnisse

### Felder aktualisieren

Gesamtes Dokument:

```text
Ctrl + A
F9
```

Einzelnes Feld umschalten:

```text
Shift + F9
```

Alle Feldfunktionen anzeigen:

```text
Alt + F9
```

### Inhaltsverzeichnis

- Überschriftformatvorlagen verwenden.
- **Referenzen → Inhaltsverzeichnis** einfügen.
- Vor Export Rechtsklick → **Feld aktualisieren → Gesamtes Verzeichnis**.

### Querverweise

Auf Überschrift, Abbildung, Tabelle oder nummeriertes Element verweisen. Querverweise sind Felder und bleiben beim Verschieben konsistent.

### Beschriftungen

```text
Referenzen → Beschriftung einfügen
```

Anschließend Abbildungs- oder Tabellenverzeichnis automatisch erzeugen.

## Überarbeiten und Zusammenarbeit

### Änderungen nachverfolgen

```text
Ctrl + Shift + E
```

Workflow:

1. Änderungsverfolgung aktivieren.
2. Anzeigemodus bewusst wählen: einfaches Markup, gesamtes Markup, kein Markup.
3. Kommentare statt Format-Farbcodes verwenden.
4. Änderungen einzeln oder nach Autor prüfen.
5. Vor Veröffentlichung Metadaten und Kommentare mit Dokumentprüfung kontrollieren.

> [!danger]
> „Kein Markup“ blendet Änderungen nur aus; es nimmt sie nicht an. Vor externer Weitergabe Änderungen annehmen/ablehnen und den Dokumentinspektor ausführen.

### Vergleichen statt Vertrauen

```text
Überprüfen → Vergleichen → Zwei Versionen eines Dokuments vergleichen
```

Geeignet, wenn eine bearbeitete Datei ohne aktivierte Änderungsverfolgung zurückkommt.

## Tabellen, Bilder und Beschriftungen

- Tabellen nicht mit Tabulatoren nachbauen.
- Tabellenkopf wiederholen lassen.
- Alt-Text für bedeutungstragende Grafiken vergeben.
- Bilder möglichst „Mit Text in Zeile“ nutzen, wenn robustes Layout wichtiger als freie Positionierung ist.
- Verankerung und Textumbruch bei schwebenden Objekten kontrollieren.
- Bilder vor Einfügen passend skalieren; unnötige Auflösung komprimieren.
- Beschriftungen und Querverweise verwenden.

## Serienbriefe

Grundablauf:

1. Datenquelle bereinigen: eine Zeile pro Empfänger, eindeutige Spaltennamen.
2. **Sendungen → Seriendruck starten**.
3. Empfänger auswählen.
4. Merge-Felder einfügen.
5. Regeln wie `Wenn…Dann…Sonst` sparsam verwenden.
6. Vorschau für erste, letzte und Sonderfall-Datensätze prüfen.
7. In neues Dokument zusammenführen und Stichprobe durchführen.
8. Datenschutz und sichere Ablage beachten.

> [!warning]
> Dezimal-, Datums- und Postleitzahlenformat können aus Excel unerwartet erscheinen. Datenquelle und Feldschalter vor Massenversand testen.

## Wichtige Tastenkürzel

| Aktion | Kürzel |
|---|---|
| Speichern | `Ctrl+S` |
| Speichern unter | `F12` beziehungsweise `Ctrl+Shift+S` je Version |
| Suchen/Ersetzen | `Ctrl+F` / `Ctrl+H` |
| Gehe zu | `Ctrl+G` oder `F5` |
| Fett/Kursiv/Unterstrichen | `Ctrl+B` / `Ctrl+I` / `Ctrl+U` |
| Linksbündig/Zentriert/Rechts/Blocksatz | `Ctrl+L/E/R/J` |
| Überschrift 1/2/3 | `Ctrl+Alt+1/2/3` |
| Standardformat | `Ctrl+Shift+N` |
| Hyperlink | `Ctrl+K` |
| Seitenumbruch | `Ctrl+Enter` |
| geschützter Bindestrich | `Ctrl+Shift+-` |
| geschütztes Leerzeichen | `Ctrl+Shift+Leertaste` |
| Format übertragen | `Ctrl+Shift+C`, dann `Ctrl+Shift+V` |
| Kommentar | `Ctrl+Alt+M` |
| Änderungen verfolgen | `Ctrl+Shift+E` |
| Feld aktualisieren | `F9` |
| Druckvorschau/Drucken | `Ctrl+P` |
| Menüband-Tipps | `Alt` |

## Barrierefreiheit und Veröffentlichung

Vor PDF/Weitergabe:

- Dokumenttitel und Sprache setzen.
- Überschriftenhierarchie ohne Sprünge prüfen.
- aussagekräftige Linktexte verwenden.
- Tabellen mit Kopfzeile und einfacher Struktur bauen.
- Alt-Texte für relevante Bilder ergänzen.
- Farbkontrast prüfen; Information nicht nur durch Farbe vermitteln.
- **Überprüfen → Barrierefreiheit überprüfen** ausführen.
- Felder, Inhalts- und Abbildungsverzeichnis aktualisieren.
- Kommentare, ausgeblendeten Text und Metadaten prüfen.

## Fehlerdiagnose und Reparatur

### Layout springt

1. Steuerzeichen anzeigen.
2. Abschnitts- und Seitenumbrüche prüfen.
3. Absatzoptionen **Nicht vom nächsten Absatz trennen**, **Zeilen zusammenhalten**, **Seitenumbruch oberhalb** kontrollieren.
4. schwebende Objekte und Anker prüfen.
5. Formatvorlage statt direkter Formatierung anwenden.

### Nummerierung kaputt

- nicht manuell korrigieren
- mehrstufige Liste und Vorlagenverknüpfung prüfen
- betroffenen Absatz erneut korrekter Überschriftvorlage zuweisen
- bei großen Schäden Inhalt in saubere Vorlage überführen

### Datei beschädigt

- Kopie anlegen.
- **Öffnen und reparieren** verwenden.
- Text über **Einfügen → Text aus Datei** in neues Dokument übernehmen.
- eingebettete Objekte/Änderungen als mögliche Ursache isolieren.
- AutoWiederherstellen-/Versionsverlauf prüfen.

### Sichere Abschlussroutine

```text
Ctrl+A → F9
Rechtschreibung/Editor
Barrierefreiheit
Änderungen/Kommentare
Dokumentinspektor
PDF-Export
PDF visuell stichprobenartig prüfen
```

## Quellen
- [Microsoft: Tastenkombinationen in Word](https://support.microsoft.com/de-de/office/tastenkombinationen-in-word-95ef89dd-7142-4b50-afb2-f762f663ceb2)
- [Microsoft: Erstellen eines Inhaltsverzeichnisses](https://support.microsoft.com/de-de/office/einf%C3%BCgen-eines-inhaltsverzeichnisses-882e8564-0edb-435e-84b5-1d8552ccf0c0)
- [Microsoft: Barrierefreiheit in Word](https://support.microsoft.com/de-de/office/erstellen-von-barrierefreien-word-dokumenten-f%C3%BCr-menschen-mit-behinderungen-d9bf3683-87ac-47ea-b91a-78dcacb3c66d)

## Verwandte Notizen
- [[Microsoft-Excel-Cheatsheet]]
- [[Microsoft-Visio-Cheatsheet]]
- [[KI-Prompts-Cheatsheet]]
