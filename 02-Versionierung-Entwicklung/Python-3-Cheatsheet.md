---
title: "Python 3 – Cheatsheet"
aliases: ["Python Cheatsheet", "Python3", "Python CLI und Packaging"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [python, programming, pip, venv, testing, typing]
source: "https://docs.python.org/3/"
---

# Python 3 – Cheatsheet

> [!abstract] Zweck
> Ausführliche Praxisreferenz für Python 3: Interpreter, virtuelle Umgebungen, Sprache, Datenstrukturen, Dateien, Fehler, Module, Packaging, Typisierung, Tests, Async, Logging, Sicherheit, Performance und Diagnose.

> [!important]
> In Skripten und Automatisierung immer gezielt den Interpreter und dessen Paketmanager koppeln: `python -m pip`, `python -m pytest`, `python -m venv`. So wird vermieden, dass `pip` oder ein Tool aus einer anderen Umgebung verwendet wird.

## Inhalt

- [[#Interpreter und virtuelle Umgebungen]]
- [[#Projektstruktur]]
- [[#Syntax und Datenstrukturen]]
- [[#Funktionen, Typisierung und Dataclasses]]
- [[#Fehlerbehandlung]]
- [[#Dateien, Pfade, JSON und CSV]]
- [[#Module und Imports]]
- [[#Packaging mit pyproject.toml]]
- [[#Tests und Qualität]]
- [[#Logging und CLI]]
- [[#Async und Concurrency]]
- [[#Sicherheit]]
- [[#Performance und Diagnose]]

## Interpreter und virtuelle Umgebungen

```bash
python3 --version
python3 -c 'import sys; print(sys.executable); print(sys.version)'
python3 -m site
```

Virtuelle Umgebung:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS
```

PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Prüfen:

```bash
python -c 'import sys; print(sys.executable)'
python -m pip --version
python -m pip install --upgrade pip
```

Verlassen:

```bash
deactivate
```

> [!warning]
> System-Python einer Distribution nicht mit globalem `sudo pip install` verändern. Distributionpakete, venv, `pipx` oder einen Projektmanager verwenden.

## Projektstruktur

```text
projekt/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── paketname/
│       ├── __init__.py
│       ├── cli.py
│       └── core.py
├── tests/
│   └── test_core.py
└── .venv/
```

`src`-Layout verhindert, dass Tests versehentlich das uninstallierte Arbeitsverzeichnis statt des gebauten Pakets importieren.

## Syntax und Datenstrukturen

### Variablen und f-Strings

```python
name = "Ada"
count = 3
message = f"{name}: {count=}, doppelt={count * 2}"
```

### Collections

```python
items = ["a", "b", "c"]
point = (10, 20)
unique = {"admin", "user"}
config = {"timeout": 30, "debug": False}
```

Comprehensions:

```python
squares = [n * n for n in range(10) if n % 2 == 0]
by_id = {user.id: user for user in users}
```

Generator statt großer Liste:

```python
squares = (n * n for n in range(1_000_000))
```

### Slicing

```python
values[1:5]
values[:10]
values[-3:]
values[::2]
values[::-1]
```

### Unpacking

```python
first, *middle, last = values
for index, value in enumerate(values, start=1):
    ...
for left, right in zip(a, b, strict=True):
    ...
```

`strict=True` erkennt unterschiedlich lange Eingaben.

### Match

```python
match response:
    case {"status": "ok", "data": data}:
        handle(data)
    case {"status": "error", "message": message}:
        raise RuntimeError(message)
    case _:
        raise ValueError("unbekanntes Format")
```

## Funktionen, Typisierung und Dataclasses

```python
from collections.abc import Iterable

def total(values: Iterable[float], *, tax: float = 0.0) -> float:
    """Summiert Werte und addiert einen Steuersatz."""
    subtotal = sum(values)
    return subtotal * (1 + tax)
```

- Positionsargumente sparsam.
- `*` erzwingt benannte Argumente danach.
- mutable Defaults vermeiden.

Falsch:

```python
def add(value, items=[]):
    items.append(value)
    return items
```

Richtig:

```python
def add(value: str, items: list[str] | None = None) -> list[str]:
    result = [] if items is None else items
    result.append(value)
    return result
```

### Dataclass

```python
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class User:
    id: int
    name: str
    roles: tuple[str, ...] = field(default_factory=tuple)
```

### Protocol

```python
from typing import Protocol

class Writer(Protocol):
    def write(self, data: str) -> int: ...

def emit(target: Writer, text: str) -> None:
    target.write(text)
```

Typen verbessern Lesbarkeit und Tooling, sind zur Laufzeit aber nicht automatisch Validierung.

## Fehlerbehandlung

```python
try:
    value = int(raw)
except ValueError as exc:
    raise ConfigError(f"Ungültige Zahl: {raw!r}") from exc
else:
    use(value)
finally:
    cleanup()
```

### Eigene Exception

```python
class AppError(Exception):
    """Basisklasse für erwartbare Anwendungsfehler."""

class ConfigError(AppError):
    pass
```

Regeln:

- nur erwartete, konkrete Exceptions fangen
- Kontext mit `raise ... from exc` erhalten
- Exceptions nicht als normale Schleifensteuerung missbrauchen
- `except Exception` nur an Prozessgrenzen mit Logging/Weiterwurf
- `BaseException` normalerweise nicht fangen; dazu gehören `KeyboardInterrupt` und `SystemExit`

Exitcodes:

```python
import sys

def main() -> int:
    try:
        run()
    except ConfigError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

## Dateien, Pfade, JSON und CSV

### pathlib

```python
from pathlib import Path

path = Path("config") / "app.json"
text = path.read_text(encoding="utf-8")
path.write_text("Hallo\n", encoding="utf-8")
```

Sicher atomisch schreiben:

```python
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_name = tmp.name
    os.replace(temp_name, path)
```

### Context Manager

```python
with path.open("r", encoding="utf-8") as handle:
    for line in handle:
        process(line.rstrip("\n"))
```

### JSON

```python
import json

data = json.loads(text)
text = json.dumps(data, ensure_ascii=False, indent=2)
```

Untrusted JSON kann extrem groß/tief sein; Größenlimit und Schema-/Fachvalidierung einsetzen.

### CSV

```python
import csv

with open("input.csv", newline="", encoding="utf-8-sig") as handle:
    reader = csv.DictReader(handle, delimiter=";")
    for row in reader:
        print(row["Name"])
```

Beim Schreiben `newline=""` verwenden. Für CSV-Exporte in Tabellenprogramme Formel-Injektion durch Werte mit `=`, `+`, `-`, `@` bedenken.

## Module und Imports

```python
# paketname/core.py
def calculate(): ...

# paketname/cli.py
from .core import calculate
```

Ausführung als Modul:

```bash
python -m paketname.cli
```

Importpfad untersuchen:

```bash
python -c 'import sys; print(*sys.path, sep="\n")'
python -c 'import paketname; print(paketname.__file__)'
```

> [!warning]
> Datei nicht wie ein Standardmodul nennen (`json.py`, `typing.py`, `email.py`). Das kann das echte Modul überschatten.

Lazy/circular Imports sind häufig Architekturhinweis. Gemeinsame Typen/Interfaces in neutrales Modul ziehen; keine Importtricks ohne Grund.

## Packaging mit pyproject.toml

Minimal mit setuptools:

```toml
[build-system]
requires = ["setuptools>=75", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "meine-app"
version = "0.1.0"
description = "Beispiel"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27,<1",
]

[project.scripts]
meine-app = "paketname.cli:main"
```

Editable installieren:

```bash
python -m pip install -e .
```

Build:

```bash
python -m pip install build
python -m build
python -m pip install dist/*.whl
```

Dependencyzustand:

```bash
python -m pip list
python -m pip show paketname
python -m pip check
python -m pip freeze
```

Für reproduzierbare Anwendungen Lock-/Constraints-Werkzeug nach Teamstandard verwenden. `pip freeze` allein beschreibt Umgebung, aber nicht Herkunft, Plattformmarker oder Buildprozess vollständig.

### pipx für CLI-Tools

```bash
pipx install ruff
pipx list
pipx upgrade-all
```

## Tests und Qualität

### unittest

```python
import unittest

class TotalTest(unittest.TestCase):
    def test_total(self):
        self.assertEqual(total([1, 2]), 3)
```

```bash
python -m unittest discover -v
```

### pytest

```python
def test_total() -> None:
    assert total([1, 2]) == 3
```

```bash
python -m pytest
python -m pytest tests/test_core.py::test_total -vv
python -m pytest -x --pdb
```

### Temporäre Pfade und Mocks

- `tmp_path` für Dateitests
- `monkeypatch` für Umgebung
- Netzwerk nicht in Unit Tests real aufrufen
- Zeit, Zufall und UUID injizierbar machen

### Qualitätstools

```bash
ruff check .
ruff format --check .
python -m mypy src
python -m pytest
```

Werkzeuge und Konfiguration in `pyproject.toml` fixieren. CI und lokal denselben Befehl verwenden.

## Logging und CLI

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def run() -> None:
    logger.info("Import gestartet", extra={"job_id": "123"})
```

Konfiguration an Prozessgrenze:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
```

Regeln:

- Bibliotheken rufen nicht global `basicConfig` auf.
- Geheimnisse, Tokens und unnötige PII nicht loggen.
- Korrelation-ID/Job-ID strukturiert führen.
- Exception mit Stacktrace: `logger.exception("...")` innerhalb `except`.

### argparse

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("path", type=Path)
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()
```

CLI-Konvention:

- stdout für Ergebnis, stderr für Diagnose
- nicht-interaktiver Modus
- sinnvolle Exitcodes
- `--help` und `--version`
- `--json` für Automation
- `--dry-run` für destruktive Operationen

## Async und Concurrency

### asyncio

```python
import asyncio

async def fetch_one(client, url: str) -> str:
    async with asyncio.timeout(10):
        response = await client.get(url)
        response.raise_for_status()
        return response.text

async def main() -> None:
    async with asyncio.TaskGroup() as group:
        for url in urls:
            group.create_task(fetch_one(client, url))

asyncio.run(main())
```

- blockierendes I/O nicht direkt im Event Loop
- Concurrency begrenzen
- Timeouts und Cancellation behandeln
- Tasks nicht „fire and forget“ verlieren

### Threads versus Prozesse

| Werkzeug | Geeignet für |
|---|---|
| `asyncio` | viele kooperative I/O-Aufgaben |
| Threads | blockierendes I/O, Libraries ohne Async-API |
| Prozesse | CPU-intensive Python-Arbeit, Isolation |

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
```

Für kleine Arbeitspakete kann Prozess-Serialisierung mehr kosten als sie spart.

## Sicherheit

### Keine untrusted Deserialisierung

Nicht auf untrusted Daten:

```python
pickle.loads(data)
yaml.load(data)          # ohne sicheren Loader
exec(text)
eval(text)
```

Subprocess sicher:

```python
import subprocess

subprocess.run(
    ["git", "status", "--short"],
    check=True,
    text=True,
    capture_output=True,
)
```

Nicht untrusted Text mit `shell=True` zusammensetzen.

### Secrets

- nicht im Sourcecode oder Defaultargument
- Umgebung/Secret Manager
- Logs und Tracebacks filtern
- minimale Lebensdauer und Rechte
- Konfigurationsdateirechte prüfen

### Dependencies

- virtuelle Umgebung
- Hash/Lock/Constraints je Prozess
- Paketquelle und Typosquatting prüfen
- automatische Security-Scans
- Buildbackend und Setupcode sind ausführbarer Code

## Performance und Diagnose

### Messen

```bash
python -m timeit 'sum(range(1000))'
python -m cProfile -o profile.out -m paketname.cli
python -m pstats profile.out
```

Memory:

```bash
python -X tracemalloc=25 script.py
```

Importzeit:

```bash
python -X importtime -c 'import paketname' 2> importtime.log
```

### Optimierungsreihenfolge

1. Algorithmus/Datenstruktur
2. unnötige I/O/DB-Aufrufe
3. Batch/Streaming
4. Profiling-Hotspot
5. stdlib/C-optimierte Primitive
6. Parallelität/Native Extension nur bei Bedarf

### Debugger

```python
breakpoint()
```

```bash
python -m pdb script.py
```

Post-mortem mit pytest:

```bash
python -m pytest --pdb
```

### Häufige Fehler

| Fehler | Prüfung |
|---|---|
| `ModuleNotFoundError` | aktive venv, `sys.executable`, Installationsmodus, Dateiname |
| falsches Paket geladen | `module.__file__`, `sys.path`, Schattenmodul |
| `PermissionError` | Pfad, Eigentümer, Lock, Sandbox/SELinux |
| Encodingfehler | explizites `encoding`, tatsächliches Dateiformat |
| SSL-Fehler | CA-Trust, Proxy, Uhrzeit; Prüfung nicht deaktivieren |
| nur CI fehlerhaft | Pythonversion, OS, Lockfile, Case Sensitivity, Zeitzone |

### Universelle Prüfreihenfolge

```bash
python --version
python -c 'import sys,platform; print(sys.executable); print(platform.platform()); print(sys.path)'
python -m pip --version
python -m pip check
python -m pip list
```

Dann kleinstes reproduzierbares Beispiel, vollständigen Traceback von unten nach oben und konkrete Eingabedaten isolieren.

## Quellen
- [Python 3 Documentation](https://docs.python.org/3/)
- [Python Tutorial](https://docs.python.org/3/tutorial/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [venv](https://docs.python.org/3/library/venv.html)
- [asyncio](https://docs.python.org/3/library/asyncio.html)

## Verwandte Notizen
- [[Git-Cheatsheet]]
- [[Make-und-Source-Builds-Cheatsheet]]
- [[Neovim-LSP-Debugging-Cheatsheet]]
- [[Microsoft-Excel-Cheatsheet]]
