# Weblinks und Obsidian-Callouts

## Schutzprinzip

Die kanonischen Markdown-Dateien werden nicht verändert. Der Scanner erkennt Wikilinks ausschließlich außerhalb von:

- YAML-Frontmatter;
- beliebig langen Backtick- und Tilde-Codefences;
- Inline-Code, auch über Zeilengrenzen;
- eingerücktem Markdown-Code;
- HTML-Kommentaren.

Ersetzungen werden rückwärts nach Quelloffset ausgeführt. Dadurch bleiben alle zuvor ermittelten Positionen stabil und Lehrbeispiele in der Obsidian-Cheatsheet-Datei unverändert.

## Auflösungsreihenfolge

1. exakter relativer oder repositoryweiter Pfad;
2. exakter Pfad ohne `.md`;
3. Titel, Dateiname oder Alias aus dem Contentindex;
4. eindeutige Überschrift beziehungsweise expliziter Anker.

Groß-/Kleinschreibungsabweichungen sind ein eigener blockierender Fehler. Mehrdeutige Aliase werden nicht geraten. Pfade außerhalb des Repositoryroots, externe URL-Schemata in Wikilinks und Markdown-Transklusionen schlagen geschlossen fehl.

## Unterstützte Formen

```text
[[Seite]]
[[Seite|sichtbarer Text]]
[[Seite#Überschrift]]
[[Seite#Überschrift|sichtbarer Text]]
[[#lokale Überschrift]]
![[bild.png]]
```

`![[Seite.md]]` wird im Web-MVP bewusst nicht transkludiert. Der Validator meldet `EM001`, damit Inhalt nicht stillschweigend fehlt oder doppelt erscheint.

## Callouts

Obsidian-Callouts werden nur in der generierten Webkopie in Material-Admonitions umgewandelt. Unterstützt sind unter anderem `abstract`, `note`, `info`, `tip`, `important`, `warning`, `danger`, `success`, `question`, `failure`, `bug`, `example`, `quote` und `evidence` sowie gängige Obsidian-Synonyme.

```markdown
> [!danger]- Destruktiver Schritt
> Erst nach geprüftem Backup ausführen.
```

wird zu einer standardmäßig geschlossenen Material-Admonition. `+` erzeugt eine geöffnete einklappbare Admonition, ohne Fold-Marker entsteht eine normale Admonition. Unbekannte Typen bleiben unverändert und werden nicht semantisch geraten.

## Fehlercodes

| Code | Bedeutung |
|---|---|
| `LK001` | Linkziel fehlt |
| `LK002` | Linkziel ist mehrdeutig |
| `LK003` | Überschrift fehlt |
| `LK004` | Groß-/Kleinschreibung weicht ab |
| `LK005` | Link ist syntaktisch oder sicherheitlich unzulässig |
| `LK006` | Überschrift ist mehrdeutig |
| `EM001` | Einbettung wird nicht unterstützt |

## Prüfung

```bash
python -m pytest -q tests/test_links.py tests/test_callouts.py
python scripts/validate_links.py --strict --report build/reports/links.json
```
