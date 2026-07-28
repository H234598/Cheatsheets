---
title: "Cinnamon – Cheatsheet"
aliases: ["Cinnamon Desktop Cheatsheet", "Linux Mint Cinnamon", "Cinnamon Shortcuts"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, cinnamon, desktop, nemo, dconf, shortcuts]
source: "https://github.com/linuxmint/cinnamon"
---

# Cinnamon – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz zur Cinnamon-Desktopumgebung: Bedienung, Tastenkürzel, Panels/Applets/Desklets, Nemo, Einstellungen per gsettings/dconf, Session, Erweiterungen, Reset und Diagnose.

> [!warning] Reset mit Bedacht
> `dconf reset -f /org/cinnamon/` entfernt benutzerspezifische Cinnamon-Einstellungen. Vorher mit `dconf dump` sichern und möglichst nur den betroffenen Teilbaum zurücksetzen.

## Inhalt

- [[#Komponenten]]
- [[#Wichtige Shortcuts]]
- [[#Panels, Applets, Desklets und Extensions]]
- [[#Nemo Dateimanager]]
- [[#gsettings und dconf]]
- [[#Session und Neustart]]
- [[#Autostart]]
- [[#Themes und Skalierung]]
- [[#Backup und Reset]]
- [[#Diagnose]]

## Komponenten

| Komponente | Aufgabe |
|---|---|
| Cinnamon | Shell/Desktopumgebung |
| Muffin | Window Manager/Compositor |
| Nemo | Dateimanager/Desktopicons |
| cinnamon-settings | grafische Einstellungen |
| cinnamon-session | Sitzung/Autostart |
| Applets | Panel-Erweiterungen |
| Desklets | Desktop-Widgets |
| Spices/Extensions | zusätzliche Funktionen/Themes |

Version:

```bash
cinnamon --version
cinnamon-settings --version
```

Sitzung:

```bash
echo "$XDG_CURRENT_DESKTOP"
echo "$XDG_SESSION_TYPE"
loginctl session-status
```

## Wichtige Shortcuts

Standardbelegung kann je Distribution/Version variieren. In **Systemeinstellungen → Tastatur → Tastenkombinationen** prüfen.

| Aktion | Häufige Taste |
|---|---|
| Menü öffnen | `Super` |
| Fenster wechseln | `Alt+Tab` |
| Rückwärts wechseln | `Alt+Shift+Tab` |
| Fenster schließen | `Alt+F4` |
| Fenster maximieren | `Super+↑` oder Doppelklick Titelleiste |
| Fenster links/rechts kacheln | `Super+←` / `Super+→` |
| Arbeitsplatz wechseln | `Ctrl+Alt+←/→` |
| Fenster auf anderen Arbeitsplatz | `Ctrl+Alt+Shift+←/→` |
| Desktop zeigen | häufig `Super+D` |
| Ausführen-Dialog | `Alt+F2` |
| Screenshot | `Print`, `Alt+Print`, `Shift+Print` |
| Terminal | oft `Ctrl+Alt+T` |
| Bildschirm sperren | häufig `Super+L` oder `Ctrl+Alt+L` |

Eigene Shortcuts über `cinnamon-settings keyboard`.

## Panels, Applets, Desklets und Extensions

Grafisch:

```bash
cinnamon-settings panel
cinnamon-settings applets
cinnamon-settings desklets
cinnamon-settings extensions
cinnamon-settings themes
```

Spices liegen typischerweise in:

```text
~/.local/share/cinnamon/applets/
~/.local/share/cinnamon/desklets/
~/.local/share/cinnamon/extensions/
~/.themes/
~/.icons/
```

Systemweit häufig:

```text
/usr/share/cinnamon/applets/
/usr/share/themes/
/usr/share/icons/
```

> [!important]
> Drittanbieter-Spices laufen im Desktopkontext des Benutzers. Quelle, Aktualität und Berechtigungen prüfen; nicht wahllos installieren.

Problematische Erweiterung temporär verschieben:

```bash
mkdir -p ~/.local/share/cinnamon-disabled
mv ~/.local/share/cinnamon/extensions/NAME@UUID \
   ~/.local/share/cinnamon-disabled/
```

## Nemo Dateimanager

```bash
nemo
nemo /pfad
nemo --no-desktop
```

Desktopprozess prüfen:

```bash
pgrep -af nemo
```

Nemo neu starten:

```bash
nemo -q
nohup nemo-desktop >/dev/null 2>&1 &
```

Häufige Shortcuts:

| Aktion | Taste |
|---|---|
| neuer Tab | `Ctrl+T` |
| neuer Ordner | `Ctrl+Shift+N` |
| Ort bearbeiten | `Ctrl+L` |
| versteckte Dateien | `Ctrl+H` |
| Suche | `Ctrl+F` |
| Eigenschaften | `Alt+Enter` |
| umbenennen | `F2` |
| aktualisieren | `Ctrl+R` oder `F5` |

Skripte/Aktionen:

```text
~/.local/share/nemo/scripts/
~/.local/share/nemo/actions/
```

Skripte ausführbar machen:

```bash
chmod +x ~/.local/share/nemo/scripts/mein-skript
```

## gsettings und dconf

Schemas suchen:

```bash
gsettings list-schemas | grep -i cinnamon
gsettings list-recursively org.cinnamon.desktop.interface
```

Wert lesen:

```bash
gsettings get org.cinnamon.desktop.interface clock-use-24h
```

Wert setzen:

```bash
gsettings set org.cinnamon.desktop.interface clock-use-24h true
```

Schlüssel zurücksetzen:

```bash
gsettings reset org.cinnamon.desktop.interface clock-use-24h
```

Mit dconf inspizieren:

```bash
dconf dump /org/cinnamon/ | less
dconf watch /org/cinnamon/
```

`dconf watch` ist hilfreich, um beim Ändern einer GUI-Option den passenden Schlüssel zu erkennen.

## Session und Neustart

Alt+F2, dann je X11-Version häufig:

```text
r
```

Das Neustarten der Shell ist unter Wayland nicht gleich möglich und kann je Version anders funktionieren.

CLI vorsichtig:

```bash
cinnamon --replace &
```

Dies kann die laufende Sitzung stören. Besser zuerst Logs ansehen oder ab-/anmelden.

Abmelden:

```bash
cinnamon-session-quit --logout
```

Sperren:

```bash
cinnamon-screensaver-command --lock
```

## Autostart

Grafisch:

```bash
cinnamon-settings startup
```

Benutzerspezifisch:

```text
~/.config/autostart/*.desktop
```

Beispiel:

```ini
[Desktop Entry]
Type=Application
Name=Mein Dienst
Exec=/home/alice/bin/start-mein-dienst
X-GNOME-Autostart-enabled=true
```

Für echte Hintergrunddienste ist eine `systemd --user`-Unit oft robuster als Desktop-Autostart.

## Themes und Skalierung

```bash
cinnamon-settings themes
cinnamon-settings fonts
cinnamon-settings display
```

GTK Theme lesen:

```bash
gsettings get org.cinnamon.desktop.interface gtk-theme
```

Icon Theme:

```bash
gsettings get org.cinnamon.desktop.interface icon-theme
```

HiDPI/Skalierung hängt von Cinnamon-, X11-/Wayland- und Anwendungsversion ab. Unterschiedliche Toolkits können anders skalieren; nicht mehrere globale Variablen gleichzeitig setzen, ohne Wirkung zu dokumentieren.

## Backup und Reset

Backup:

```bash
mkdir -p ~/cinnamon-backup
dconf dump /org/cinnamon/ > ~/cinnamon-backup/cinnamon.dconf
cp -a ~/.local/share/cinnamon ~/cinnamon-backup/
cp -a ~/.config/autostart ~/cinnamon-backup/
```

Restore:

```bash
dconf load /org/cinnamon/ < ~/cinnamon-backup/cinnamon.dconf
```

Gezielter Reset:

```bash
dconf reset -f /org/cinnamon/desktop/keybindings/
```

Komplettreset – letzte Stufe:

```bash
dconf reset -f /org/cinnamon/
```

Danach ab- und wieder anmelden.

## Diagnose

Logs aktueller Sitzung:

```bash
journalctl --user -b --priority=warning
journalctl -b | grep -Ei 'cinnamon|muffin|nemo'
```

Cinnamon Looking Glass öffnen, häufig über Menü/Alt+F2 und `lg`, je Version. Dort Extensions, Fehler und Fenster inspizieren.

Prozesse:

```bash
pgrep -af 'cinnamon|muffin|nemo'
```

Grafik:

```bash
echo "$XDG_SESSION_TYPE"
glxinfo -B
lspci -nnk | grep -A3 -Ei 'VGA|3D|Display'
journalctl -k -b | grep -Ei 'drm|gpu|amdgpu|i915|nouveau|nvidia'
```

Prüfreihenfolge:

1. Problem nur in einem Benutzer oder systemweit?
2. Drittanbieter-Applet/Theme/Extension deaktivieren.
3. Grafiksession und Treiberlogs prüfen.
4. Relevanten dconf-Schlüssel mit `dconf watch` identifizieren.
5. Konfiguration sichern.
6. Nur betroffenen Teilbaum zurücksetzen.
7. Testbenutzer anlegen, um System-/Benutzerursache zu trennen.

## Quellen
- [Linux Mint Cinnamon GitHub](https://github.com/linuxmint/cinnamon)
- [Cinnamon Spices](https://cinnamon-spices.linuxmint.com/)
- [GSettings Documentation](https://docs.gtk.org/gio/class.Settings.html)

## Verwandte Notizen
- [[X11 – Cheatsheet]]
- [[Fedora-RHEL – Cheatsheet]]
- [[Linux-Benutzer- und Gruppenmanagement – Cheatsheet]]
