---
title: Make, Source-Builds und Buildsysteme – Cheatsheet
aliases:
- make source configure
- Aus Quellcode kompilieren
- Buildsysteme Cheatsheet
- Make und Source-Builds – Cheatsheet
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags:
- make
- build
- source
- cmake
- meson
- ninja
- compiler
source: https://www.gnu.org/software/make/manual/
---

# Make, Source-Builds und Buildsysteme – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz zum Bauen aus Quellcode: Toolchain, configure/make, Makefiles, CMake, Meson/Ninja, pkg-config, Installation, Packaging, Reproduzierbarkeit und Fehlerdiagnose.

> [!danger]
> `sudo make install` außerhalb des Paketmanagers kann Dateien unkontrolliert über das System verteilen und spätere Updates erschweren. Bevorzugt Benutzerpräfix, Staging-Verzeichnis oder ein natives Paket bauen.

## Inhalt

- [[#Grundbegriffe]]
- [[#Toolchain vorbereiten]]
- [[#Klassischer configure-make-install-Ablauf]]
- [[#Makefile-Grundlagen]]
- [[#CMake]]
- [[#Meson und Ninja]]
- [[#pkg-config und Bibliotheken]]
- [[#Installationsziele und DESTDIR]]
- [[#Patches, Versionen und Reproduzierbarkeit]]
- [[#Diagnose]]

## Grundbegriffe

| Begriff | Bedeutung |
|---|---|
| Compiler | übersetzt Quellcode in Objektcode |
| Linker | verbindet Objekte und Bibliotheken |
| Buildsystem | beschreibt Abhängigkeiten und Schritte |
| Generator | erzeugt Dateien für ein anderes Buildsystem, z. B. CMake → Ninja |
| Toolchain | Compiler, Linker, Archiver, SDK und Einstellungen |
| Prefix | Installationswurzel, typischerweise `/usr/local` |
| Staging/DESTDIR | temporäre Paketwurzel für Packaging |
| Out-of-tree build | Buildartefakte außerhalb des Sourceverzeichnisses |

### Archiv prüfen

```bash
file projekt.tar.xz
sha256sum projekt.tar.xz
tar -tf projekt.tar.xz | head
```

Signatur, Releasequelle und Prüfsumme aus unabhängiger vertrauenswürdiger Quelle prüfen.

## Toolchain vorbereiten

Fedora/RHEL:

```bash
sudo dnf group install 'Development Tools'
sudo dnf install gcc gcc-c++ make cmake meson ninja-build pkgconf-pkg-config
```

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install build-essential cmake meson ninja-build pkg-config
```

Versionen:

```bash
cc --version
c++ --version
make --version
cmake --version
meson --version
ninja --version
pkg-config --version
```

> [!tip]
> Fehlende Header/Bibliotheken möglichst über `*-devel` (RPM) beziehungsweise `*-dev` (Debian) installieren, nicht durch zufälliges Kopieren einzelner Dateien.

## Klassischer configure-make-install-Ablauf

Autotools-Projekt:

```bash
tar -xf projekt-1.2.3.tar.xz
cd projekt-1.2.3
./configure --prefix=/usr/local
make -j"$(nproc)"
make check
sudo make install
```

Besser zunächst Optionen prüfen:

```bash
./configure --help
```

Out-of-tree, falls unterstützt:

```bash
mkdir build && cd build
../configure --prefix="$HOME/.local"
make -j"$(nproc)"
make check
make install
```

### Wo landen Dateien?

Bei Prefix `/usr/local` typischerweise:

```text
/usr/local/bin
/usr/local/lib oder lib64
/usr/local/include
/usr/local/share
/usr/local/etc
```

Benutzerpräfix:

```bash
./configure --prefix="$HOME/.local"
make
make install
```

Pfad ergänzen:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Makefile-Grundlagen

```make
CC      ?= cc
CFLAGS  ?= -O2 -g -Wall -Wextra
LDLIBS  ?=

.PHONY: all clean test install

all: app

app: main.o util.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS)

main.o: main.c util.h
util.o: util.c util.h

test: app
	./app --self-test

install: app
	install -Dm755 app "$(DESTDIR)$(PREFIX)/bin/app"

clean:
	rm -f app *.o
```

Aufruf:

```bash
make
make -j8
make V=1
make clean
make PREFIX=/usr/local
make -n install       # Dry Run
make -pRrq : 2>/dev/null | less
```

### Automatische Variablen

| Variable | Bedeutung |
|---|---|
| `$@` | Ziel |
| `$<` | erste Abhängigkeit |
| `$^` | alle Abhängigkeiten ohne Duplikate |
| `$?` | neuere Abhängigkeiten |
| `$*` | Stamm eines Pattern-Ziels |

### Parallelität

```bash
make -j"$(nproc)"
```

Nicht jedes alte Makefile ist parallel-sicher. Bei sporadischen Fehlern einmal `make -j1` testen.

## CMake

Modernes Out-of-source-Build:

```bash
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$HOME/.local"
cmake --build build --parallel
ctest --test-dir build --output-on-failure
cmake --install build
```

Optionen und Cache:

```bash
cmake -S . -B build -LH
cmake -S . -B build -LAH
cmake --build build --target help
```

Debug:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --verbose
```

Multi-config-Generatoren können `--config Release` benötigen.

### CMake-Preset

```json
{
  "version": 6,
  "configurePresets": [
    {
      "name": "dev",
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/dev",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug"
      }
    }
  ]
}
```

```bash
cmake --preset dev
cmake --build --preset dev
```

## Meson und Ninja

```bash
meson setup build --prefix="$HOME/.local" --buildtype=release
meson compile -C build
meson test -C build --print-errorlogs
meson install -C build
```

Optionen:

```bash
meson configure build
meson setup build --wipe
ninja -C build -v
```

Staging:

```bash
DESTDIR="$PWD/pkgroot" meson install -C build
```

## pkg-config und Bibliotheken

```bash
pkg-config --modversion openssl
pkg-config --cflags openssl
pkg-config --libs openssl
pkg-config --exists libcurl && echo vorhanden
```

Suchpfad:

```bash
pkg-config --variable pc_path pkg-config
export PKG_CONFIG_PATH="$HOME/.local/lib/pkgconfig:$HOME/.local/share/pkgconfig:$PKG_CONFIG_PATH"
```

Bibliotheken finden:

```bash
ldconfig -p | grep ssl
find /usr/include -name 'openssl' -type d 2>/dev/null
```

RPM-Paket für Datei:

```bash
dnf provides '*/openssl/ssl.h'
```

Debian:

```bash
apt-file search '/openssl/ssl.h'
```

`apt-file` muss eventuell installiert und aktualisiert werden.

## Installationsziele und DESTDIR

Unterschied:

```text
PREFIX=/usr              finaler Pfad im Zielsystem
DESTDIR=/tmp/pkgroot     vorgeschaltete temporäre Paketwurzel
```

Beispiel:

```bash
make PREFIX=/usr DESTDIR="$PWD/pkgroot" install
find pkgroot -type f -o -type l
```

So kann daraus ein RPM/DEB/pkg-Archiv gebaut werden, ohne das Buildsystem direkt ins laufende System schreiben zu lassen.

### Deinstallation

Manche Projekte:

```bash
sudo make uninstall
```

Darauf nicht verlassen. Installationsmanifest/Staging oder natives Paket erzeugen.

CMake kann je Projekt `install_manifest.txt` erzeugen:

```bash
cat build/install_manifest.txt
```

## Patches, Versionen und Reproduzierbarkeit

### Quellstand fixieren

```bash
git clone URL
cd projekt
git switch --detach v1.2.3
git verify-tag v1.2.3
```

Patch:

```bash
git apply --check fix.patch
git apply fix.patch
# oder für Mailpatch mit Metadaten
git am 0001-fix.patch
```

Reproduzierbare Notiz:

```text
Upstream URL/Commit/Tag
Prüfsumme/Signatur
Compiler- und Buildsystemversion
Distribution/Architektur
Buildoptionen
Patches
Dependencies
Testresultate
Installationsmanifest
```

### Compilerflags

```bash
export CFLAGS='-O2 -g -pipe'
export CXXFLAGS="$CFLAGS"
```

Nicht blind `-march=native` für verteilte Binärpakete verwenden; es kann Instruktionen des Buildhosts voraussetzen.

Sanitizer für Tests:

```bash
export CFLAGS='-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer'
export LDFLAGS='-fsanitize=address,undefined'
```

## Diagnose

### `No rule to make target`

- richtiges Verzeichnis?
- Zieldatei/Abhängigkeit existiert und Groß-/Kleinschreibung korrekt?
- generierter Buildschritt ausgeführt?
- stale Buildverzeichnis löschen/neu konfigurieren?

### Header fehlt

```text
fatal error: foo/bar.h: No such file or directory
```

Prüfen:

```bash
pkg-config --cflags foo
find /usr/include /usr/local/include -path '*foo/bar.h' 2>/dev/null
gcc -E -Wp,-v - </dev/null
```

Passendes Development-Paket installieren oder Include-Pfad korrekt konfigurieren.

### Linkerfehler `undefined reference`

- Bibliothek wirklich verlinkt?
- Reihenfolge bei statischen Bibliotheken?
- C versus C++ Namensmangling?
- benötigte Version/Symbole vorhanden?
- `LDFLAGS` versus `LDLIBS` richtig?

```bash
nm -D libfoo.so | grep symbol
readelf -Ws libfoo.so | grep symbol
ldd ./app
```

### Laufzeitbibliothek nicht gefunden

```bash
ldd ./app
readelf -d ./app | grep -E 'RPATH|RUNPATH|NEEDED'
LD_DEBUG=libs ./app
```

Dauerhafte Bibliothekspfade über Paketierung/Loaderkonfiguration, nicht pauschal mit unsicherem `LD_LIBRARY_PATH` lösen.

### Build sporadisch fehlerhaft

```bash
make clean
make -j1 V=1
```

Parallelitätsfehler, unvollständige Abhängigkeiten, Race Conditions, RAM/Storage und Compileroutput prüfen.

### Universelle Prüfreihenfolge

```bash
uname -a
cc --version
make --version
pkg-config --version
printenv | grep -E '^(CC|CXX|CFLAGS|CXXFLAGS|LDFLAGS|PKG_CONFIG_PATH)='
```

Dann vollständigen ersten Fehler lesen, nicht nur den letzten Folgefehler; Build mit verbose und sauberem Verzeichnis wiederholen.

## Quellen
- [GNU Make Manual](https://www.gnu.org/software/make/manual/)
- [CMake Documentation](https://cmake.org/documentation/)
- [Meson Documentation](https://mesonbuild.com/)
- [Ninja Manual](https://ninja-build.org/manual.html)
- [pkg-config Guide](https://people.freedesktop.org/~dbn/pkg-config-guide.html)

## Verwandte Notizen
- [[dnf-Cheatsheet]]
- [[apt-Cheatsheet]]
- [[RPM-Cheatsheet]]
- [[Git-Cheatsheet]]
