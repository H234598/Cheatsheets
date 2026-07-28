---
title: "X11 – Cheatsheet"
aliases: ["X Window System Cheatsheet", "Xorg", "X11 Forwarding"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [linux, x11, xorg, display, desktop, ssh]
source: "https://www.x.org/wiki/Documentation/"
---

# X11 – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz zu X11-Architektur, DISPLAY/XAUTHORITY, Xorg, xrandr, xinput, xauth, SSH-X11-Forwarding, Sicherheit, Wayland-Kompatibilität und Diagnose.

> [!warning] X11-Vertrauensmodell
> Ein autorisierter X11-Client kann häufig Eingaben beobachten, Fensterinhalte lesen oder Eingaben simulieren. `xhost +` schaltet Zugriffskontrolle praktisch ab und darf nicht als dauerhafte Fehlerbehebung verwendet werden.

## Inhalt

- [[#Architektur]]
- [[#DISPLAY und XAUTHORITY]]
- [[#Sitzung erkennen]]
- [[#Monitore mit xrandr]]
- [[#Eingabegeräte mit xinput]]
- [[#Zugriffskontrolle mit xauth]]
- [[#SSH X11-Forwarding]]
- [[#Xorg-Konfiguration und Logs]]
- [[#Wayland und XWayland]]
- [[#Diagnose]]

## Architektur

Historisch überraschend:

- **X-Server** läuft dort, wo Bildschirm, Tastatur und Maus sind.
- **X-Client** ist die grafische Anwendung.
- Das X11-Protokoll verbindet beide.
- Window Manager/Compositor zeichnet Rahmen und steuert Fenster.
- Desktopumgebung ergänzt Panels, Einstellungen und Dienste.

Typische Komponenten:

```text
Anwendung → Xlib/XCB → X11-Protokoll → Xorg/Xwayland → DRM/KMS/GPU
                              ↓
                     Window Manager/Compositor
```

## DISPLAY und XAUTHORITY

```bash
echo "$DISPLAY"
echo "$XAUTHORITY"
```

Typische Werte:

```text
:0
:0.0
localhost:10.0     # SSH-Forwarding
```

Format:

```text
[hostname]:display.screen
```

Testprogramm:

```bash
xdpyinfo | head
xset q
xeyes
xclock
```

Fehler `Can't open display`:

- `DISPLAY` fehlt/falsch.
- Prozess läuft als anderer Benutzer ohne Cookie.
- kein X-Server/XWayland.
- SSH-Forwarding nicht aktiviert.
- Socket/Namespace/Container nicht zugänglich.

## Sitzung erkennen

```bash
echo "$XDG_SESSION_TYPE"
loginctl show-session "$XDG_SESSION_ID" -p Type -p Display -p Remote
```

Prozesse:

```bash
pgrep -a Xorg
pgrep -a Xwayland
```

Grafikrenderer:

```bash
glxinfo -B
eglinfo
```

Aktive Displays:

```bash
ls -l /tmp/.X11-unix/
```

## Monitore mit xrandr

Ausgänge und Modi:

```bash
xrandr
xrandr --query
xrandr --listmonitors
```

Auflösung setzen:

```bash
xrandr --output HDMI-1 --mode 1920x1080 --rate 60
```

Monitor rechts anordnen:

```bash
xrandr --output HDMI-1 --right-of eDP-1 --auto
```

Internes Display aus:

```bash
xrandr --output eDP-1 --off
```

Rotation:

```bash
xrandr --output HDMI-1 --rotate left
```

Neue Modeline, nur wenn EDID/Modus fehlt:

```bash
cvt 1920 1080 60
xrandr --newmode '1920x1080_60.00' ...
xrandr --addmode HDMI-1 '1920x1080_60.00'
xrandr --output HDMI-1 --mode '1920x1080_60.00'
```

> [!note]
> Unter einer nativen Wayland-Sitzung beeinflusst `xrandr` meist nur XWayland-Sicht oder gar nicht die echte Compositor-Ausgabe. Dann Desktop-/Compositor-Werkzeuge verwenden.

## Eingabegeräte mit xinput

```bash
xinput list
xinput list-props 'Gerätename'
xinput test-xi2 --root
```

Eigenschaft setzen:

```bash
xinput set-prop 'Touchpad' 'libinput Natural Scrolling Enabled' 1
```

Gerät temporär deaktivieren:

```bash
xinput disable 'Gerätename'
xinput enable 'Gerätename'
```

Unter Wayland ist `xinput` nicht für native Geräteverwaltung zuständig. `libinput list-devices`, Desktopsettings oder Compositor-Konfiguration verwenden.

## Zugriffskontrolle mit xauth

Cookies anzeigen:

```bash
xauth list
xauth info
```

Cookie für anderen Benutzer gezielt übertragen:

```bash
xauth nlist "$DISPLAY" | sudo -u anderer xauth nmerge -
```

`xhost` anzeigen:

```bash
xhost
```

Lokalen Benutzer gezielt erlauben:

```bash
xhost +SI:localuser:anderer
```

Danach wieder entziehen:

```bash
xhost -SI:localuser:anderer
```

Niemals dauerhaft:

```bash
xhost +
```

## SSH X11-Forwarding

Vertrauensunwürdig/mit Einschränkungen:

```bash
ssh -X user@server
```

Trusted Forwarding:

```bash
ssh -Y user@server
```

Clientconfig:

```sshconfig
Host grafikserver
    ForwardX11 yes
    ForwardX11Trusted no
```

Server:

```ini
X11Forwarding yes
```

Abhängigkeiten: `xauth` auf Server, X-Server/XQuartz/VcXsrv-ähnliche Umgebung am Client je Betriebssystem.

Prüfen remote:

```bash
echo "$DISPLAY"
xauth list
xdpyinfo | head
```

> [!warning]
> `ssh -Y` vertraut Remoteanwendungen weitreichend. Nur auf vertrauenswürdigen Servern verwenden. Für moderne Anwendungen sind RDP/VNC/Waypipe/Web-UIs je nach Fall sicherer oder performanter.

## Xorg-Konfiguration und Logs

Moderne Systeme erkennen Hardware meist automatisch. Manuelle Dateien:

```text
/etc/X11/xorg.conf
/etc/X11/xorg.conf.d/*.conf
/usr/share/X11/xorg.conf.d/*.conf
```

Eigene Overrides nach `/etc/X11/xorg.conf.d/` statt Vendor-Dateien unter `/usr/share`.

Konfiguration generieren – nur Diagnose, nicht blind installieren:

```bash
sudo Xorg -configure
```

Logs je System:

```bash
journalctl -b _COMM=Xorg
journalctl -b | grep -Ei 'Xorg|X11|drm|gpu'
ls ~/.local/share/xorg/
ls /var/log/Xorg.*.log
```

Fehler/Warnungen in klassischem Log:

```bash
grep -E '\(EE\)|\(WW\)' /var/log/Xorg.0.log
```

## Wayland und XWayland

- Wayland ist ein anderes Displayprotokoll.
- XWayland stellt X11-Kompatibilität innerhalb einer Wayland-Sitzung bereit.
- `DISPLAY` kann gesetzt sein, obwohl die Sitzung Wayland ist.
- Native Wayland-Apps nutzen `WAYLAND_DISPLAY`, oft `wayland-0`.

```bash
echo "$XDG_SESSION_TYPE"
echo "$WAYLAND_DISPLAY"
echo "$DISPLAY"
```

App testweise erzwingen, abhängig vom Toolkit:

```bash
GDK_BACKEND=x11 app
QT_QPA_PLATFORM=xcb app
```

Nur zur Diagnose; dauerhafte Toolkit-Overrides können Nebenwirkungen haben.

## Diagnose

```bash
printf 'session=%s display=%s wayland=%s\n' "$XDG_SESSION_TYPE" "$DISPLAY" "$WAYLAND_DISPLAY"
loginctl session-status
xauth list
xdpyinfo | head
xrandr --query
lspci -nnk | grep -A3 -Ei 'VGA|3D|Display'
journalctl -b --priority=warning | grep -Ei 'xorg|xwayland|drm|gpu'
```

Prüfreihenfolge:

1. X11 oder Wayland bestimmen.
2. Benutzer/Sitzung und Environment prüfen.
3. X-Socket und Authcookie prüfen.
4. Lokale App im selben Benutzer testen.
5. Bei SSH `-vvv`, `X11Forwarding` und `xauth` prüfen.
6. GPU-/DRM-Logs und Renderer prüfen.
7. Temporäre Overrides entfernen.
8. Manuelle Xorg-Konfiguration aus dem Weg nehmen und Autodetect testen.

## Quellen
- [X.Org Documentation](https://www.x.org/wiki/Documentation/)
- [xrandr man page](https://www.x.org/releases/current/doc/man/man1/xrandr.1.xhtml)
- [OpenSSH ssh manual](https://man.openbsd.org/ssh)

## Verwandte Notizen
- [[SSH – Cheatsheet]]
- [[Cinnamon – Cheatsheet]]
- [[Linux-Netzwerk – Cheatsheet]]
