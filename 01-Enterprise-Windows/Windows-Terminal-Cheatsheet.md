---
title: "Windows Terminal – Cheatsheet"
aliases: ["Neues Windows Terminal", "wt.exe", "Windows Terminal Shortcuts"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [windows, terminal, powershell, wsl, shortcuts, cli]
source: "https://learn.microsoft.com/en-us/windows/terminal/"
---

# Windows Terminal – Cheatsheet

> [!abstract] Zweck
> Ausführliche Referenz für das moderne Windows Terminal: Profile, Tabs, Bereiche, Tastenkürzel, wt.exe, settings.json, WSL/SSH und Fehlerdiagnose.

## Inhalt

- [[#Grundkonzept]]
- [[#Installation und Aufruf]]
- [[#Wichtige Tastenkürzel]]
- [[#Tabs und Bereiche]]
- [[#wt.exe-Kommandozeile]]
- [[#Profile und settings.json]]
- [[#SSH, WSL und Arbeitsverzeichnisse]]
- [[#Darstellung, Schrift und Zwischenablage]]
- [[#Diagnose]]

## Grundkonzept

Windows Terminal ist ein Host für mehrere Kommandozeilenprofile, zum Beispiel PowerShell, Eingabeaufforderung, WSL-Distributionen, Azure Cloud Shell oder eigene SSH-/Toolprofile.

```text
Windows Terminal
├── Fenster
│   ├── Tab: PowerShell
│   ├── Tab: WSL Fedora
│   └── Tab: SSH Produktion
│       ├── Pane links
│       └── Pane rechts
└── settings.json / grafische Einstellungen
```

Es ersetzt nicht PowerShell, Bash oder `cmd.exe`; es stellt diese Shells dar und organisiert Sitzungen.

## Installation und Aufruf

```powershell
winget install --id Microsoft.WindowsTerminal --exact
wt
wt --help
```

Version und Paket:

```powershell
winget list --id Microsoft.WindowsTerminal
Get-AppxPackage Microsoft.WindowsTerminal |
  Select-Object Name,Version,InstallLocation
```

Standardterminal unter Windows über **Einstellungen → Datenschutz und Sicherheit/Entwickler** oder die Terminal-Einstellungen wählen; genaue Menüposition kann sich je Windows-Version ändern.

## Wichtige Tastenkürzel

| Aktion | Standardbelegung, typischerweise |
|---|---|
| Neues Tab | `Ctrl+Shift+T` |
| Tab schließen | `Ctrl+Shift+W` |
| Nächstes/vorheriges Tab | `Ctrl+Tab` / `Ctrl+Shift+Tab` |
| Tab direkt wählen | `Ctrl+Alt+1` … `Ctrl+Alt+9` je Konfiguration |
| Neues Fenster | `Ctrl+Shift+N` |
| Vertikal teilen | `Alt+Shift++` |
| Horizontal teilen | `Alt+Shift+-` |
| Pane fokussieren | `Alt` + Pfeiltaste |
| Pane vergrößern | `Alt+Shift` + Pfeiltaste |
| Pane schließen | `Ctrl+Shift+W` im fokussierten Pane |
| Kopieren | `Ctrl+Shift+C` oder markierter Text + `Ctrl+C` |
| Einfügen | `Ctrl+Shift+V` |
| Suchen | `Ctrl+Shift+F` |
| Befehlspalette | `Ctrl+Shift+P` |
| Einstellungen | `Ctrl+,` |
| Schrift größer/kleiner | `Ctrl++` / `Ctrl+-` |
| Vollbild | `Alt+Enter` |
| Fokusmodus | `Ctrl+Shift+F11`, abhängig von Version/Belegung |

> [!note]
> Tastenkürzel sind vollständig anpassbar. Bei Konflikten mit Neovim, tmux, WSL oder einer Anwendung die Terminal-Aktion neu belegen oder entfernen.

## Tabs und Bereiche

### Neues Tab mit Profil

Dropdown neben `+` verwenden oder per CLI:

```powershell
wt new-tab -p 'PowerShell'
wt new-tab -p 'Command Prompt'
```

### Aktuellen Tab teilen

```powershell
wt split-pane -H -p 'PowerShell'
wt split-pane -V -p 'Ubuntu'
```

- `-H` erzeugt üblicherweise einen horizontal angeordneten Bereich beziehungsweise teilt entlang der horizontalen Achse.
- `-V` teilt vertikal.
- Verhalten und Bezeichnungen im Zweifel mit `wt split-pane --help` prüfen.

Profil duplizieren:

```powershell
wt split-pane -D
```

### Layout speichern?

Windows Terminal kann Startlayouts per `wt`-Befehlsfolge reproduzieren. Für wiederkehrende Arbeitsplätze eine `.cmd`, `.ps1` oder Verknüpfung erstellen:

```powershell
wt -w dev `
  new-tab -p 'PowerShell' -d 'C:\src\app' `; `
  split-pane -V -p 'Ubuntu' -d '//wsl$/Ubuntu/home/alex/src/app' `; `
  new-tab -p 'Command Prompt' -d 'C:\temp'
```

In PowerShell müssen Semikolons für `wt` häufig mit Backtick maskiert oder als Argumentliste übergeben werden.

## wt.exe-Kommandozeile

Grundsyntax:

```text
wt [globale Optionen] [Befehl ; Befehl ; ...]
```

### Häufige Optionen

```powershell
wt -M                         # maximiert
wt -F                         # Vollbild
wt -f                         # Fokusmodus
wt -w 0                       # vorhandenes Fenster 0 ansprechen
wt -w new                     # neues Fenster
```

### Verzeichnisse und Titel

```powershell
wt -d C:\Admin
wt new-tab -d C:\Repos\Projekt --title 'Projekt'
wt new-tab -p 'PowerShell' --tabColor '#336699'
```

### Mehrere Aktionen

```cmd
wt new-tab -p "PowerShell" -d C:\src ; split-pane -V -p "Command Prompt" ; new-tab -p "Ubuntu"
```

Aus PowerShell:

```powershell
wt new-tab -p 'PowerShell' -d 'C:\src' `; split-pane -V -p 'Ubuntu'
```

## Profile und settings.json

Grafische Einstellungen öffnen:

```text
Ctrl + ,
```

JSON-Datei aus dem Einstellungsfenster über **JSON-Datei öffnen** bearbeiten. Pfade sind paket- und installationsabhängig; nicht blind aus fremden Anleitungen kopieren.

### Minimales Profilfragment

```json
{
  "name": "Admin PowerShell",
  "commandline": "pwsh.exe -NoLogo",
  "startingDirectory": "C:\\Admin",
  "hidden": false
}
```

Mit SSH:

```json
{
  "name": "SSH – server01",
  "commandline": "ssh admin@server01.example.org",
  "startingDirectory": "%USERPROFILE%"
}
```

Mit Icon und Farbschema:

```json
{
  "name": "Fedora WSL",
  "source": "Windows.Terminal.Wsl",
  "colorScheme": "Campbell",
  "font": {
    "face": "Cascadia Mono",
    "size": 11
  }
}
```

> [!warning]
> Generierte Profile besitzen oft eine `source`-Eigenschaft. Nicht jedes Feld darf in `profiles.defaults` stehen. Nach JSON-Änderungen auf Syntaxfehler achten und eine Sicherung der funktionierenden Datei behalten.

### Globale Standardwerte

```json
{
  "profiles": {
    "defaults": {
      "historySize": 9001,
      "snapOnInput": true,
      "useAcrylic": false,
      "font": {
        "face": "Cascadia Mono",
        "size": 11
      }
    },
    "list": []
  }
}
```

### Eigene Aktion

```json
{
  "command": {
    "action": "newTab",
    "profile": "PowerShell",
    "startingDirectory": "C:\\src"
  },
  "keys": "ctrl+shift+d"
}
```

Aktionen ändern sich mit Terminal-Versionen. Die integrierte JSON-Schema-Vervollständigung und offizielle Actions-Dokumentation verwenden.

## SSH, WSL und Arbeitsverzeichnisse

### SSH direkt

```powershell
ssh admin@server01.example.org
ssh -J jump.example.org admin@server01.internal
```

Ein Terminal-Profil kann den SSH-Befehl starten. Schlüssel und Hosts weiterhin in `%USERPROFILE%\.ssh\config` verwalten:

```sshconfig
Host prod-web
    HostName web01.example.org
    User admin
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

### WSL öffnen

```powershell
wsl --list --verbose
wsl -d Ubuntu
wt -p Ubuntu
```

Windows-Pfad nach WSL:

```powershell
wsl --cd /home/alex/src
```

UNC-Pfad zu WSL:

```text
\\wsl$\Ubuntu\home\alex
```

> [!tip]
> Linux-Projekte für beste I/O-Leistung häufig im Linux-Dateisystem der WSL-Distribution ablegen, nicht unter `/mnt/c`, sofern Windows-Anwendungen keinen direkten Zugriff benötigen.

## Darstellung, Schrift und Zwischenablage

### Sinnvolle Einstellungen

- Monospace-Schrift mit benötigten Glyphen verwenden.
- Kontrast und Cursorform bewusst wählen.
- Hintergrundtransparenz bei Remote-/Produktionsarbeit eher zurückhaltend einsetzen.
- `copyOnSelect` nur aktivieren, wenn unbeabsichtigtes Überschreiben der Zwischenablage akzeptabel ist.
- Warnung bei mehrzeiligem Einfügen nicht leichtfertig abschalten.
- Bell/Benachrichtigung für lange Jobs konfigurieren.

### Escape-Sequenzen testen

```powershell
$PSStyle.OutputRendering
Write-Host "`e[31mRot`e[0m Normal"
```

UTF-8:

```powershell
[Console]::OutputEncoding
$OutputEncoding
```

## Diagnose

### Terminal startet nicht oder schließt sofort

```powershell
wt --help
Get-AppxPackage Microsoft.WindowsTerminal
winget upgrade --id Microsoft.WindowsTerminal
```

Dann:

1. Standardprofil auf existierende Shell prüfen.
2. `settings.json` sichern und JSON-Syntax validieren.
3. Benutzerdefinierte `commandline` direkt in `Win+R`/PowerShell testen.
4. Ereignisanzeige und Terminal-Logs prüfen.
5. Erweiterungen wie Shell-Profilskripte vorübergehend deaktivieren.

### PowerShell-Profil isolieren

```powershell
pwsh -NoProfile
powershell.exe -NoProfile
```

Profile anzeigen:

```powershell
$PROFILE | Format-List * -Force
Test-Path $PROFILE
```

### Schrift/Glyphen fehlen

- Schriftname exakt prüfen.
- Profil-Override gegen globale Defaults vergleichen.
- Terminal neu starten.
- Nerd-Font-Symbole nur mit rechtmäßig installierter passender Schrift erwarten.

### Farben oder Tasten kollidieren

1. Befehlspalette öffnen und Aktion suchen.
2. Belegung in **Aktionen** prüfen.
3. Shell-/Editorbelegung gegen Terminalbelegung abgrenzen.
4. eigene Aktion eindeutig definieren oder Terminalbindung entfernen.

## Quellen
- [Microsoft: Windows Terminal overview](https://learn.microsoft.com/en-us/windows/terminal/)
- [Microsoft: Command-line arguments](https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments)
- [Microsoft: Custom actions](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/actions)
- [Microsoft: Panes](https://learn.microsoft.com/en-us/windows/terminal/panes)

## Verwandte Notizen
- [[Windows-Terminal-Cheatsheet#PowerShell-Profil isolieren|PowerShell-Profil und Diagnose]]
- [[SSH-Cheatsheet]]
- [[Neovim-Cheatsheet]]
- [[Netzwerk-Konfiguration-Linux-Windows-BSD]]
