---
title: "Rust – Premium-Spickzettel"
aliases: ["Rustlang Cheatsheet", "Cargo Cheatsheet", "Rust Programming"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [rust, cargo, programming, systems, memory-safety]
source: "https://doc.rust-lang.org/book/"
---

# Rust – Premium-Spickzettel

> [!abstract] Zweck
> Ausführliche Praxisreferenz für Rust: Cargo, Ownership/Borrowing, Typen, Pattern Matching, Fehlerbehandlung, Traits/Generics, Module, Tests, Concurrency, Async, FFI, Performance und Diagnose.

> [!abstract] Kernidee
> Rust verbindet statische Typisierung und native Performance mit speichersicherem Ownership-Modell. Viele Fehler werden zur Compile-Zeit verhindert; dafür müssen Besitz, Lebensdauer und Nebenläufigkeit expliziter modelliert werden.

## Inhalt

- [[#Installation und Cargo]]
- [[#Projektstruktur]]
- [[#Variablen, Typen und Kontrollfluss]]
- [[#Ownership, Borrowing und Lifetimes]]
- [[#Structs, Enums und Pattern Matching]]
- [[#Fehlerbehandlung]]
- [[#Traits, Generics und Iteratoren]]
- [[#Module, Crates und Features]]
- [[#Tests, Formatierung und Lints]]
- [[#Concurrency und Async]]
- [[#I/O, Serde und CLI]]
- [[#Unsafe, FFI und Sicherheit]]
- [[#Performance und Diagnose]]

## Installation und Cargo

Rustup ist der übliche Toolchain-Manager:

```bash
rustup show
rustup update
rustup toolchain list
rustc --version
cargo --version
```

Komponenten:

```bash
rustup component add rustfmt clippy
```

Zielplattform:

```bash
rustup target list --installed
rustup target add x86_64-unknown-linux-musl
```

Dokumentation lokal:

```bash
rustup doc
rustup doc --book
```

## Projektstruktur

Binärprojekt:

```bash
cargo new meine_app
cd meine_app
cargo run
```

Bibliothek:

```bash
cargo new meine_lib --lib
```

```text
Cargo.toml
Cargo.lock
src/
├── main.rs       Binärcrate
└── lib.rs        Bibliothekscrate
tests/            Integrationstests
examples/
benches/
build.rs          Buildskript, nur falls nötig
target/           Buildartefakte
```

### Cargo-Befehle

```bash
cargo check                    # schneller Typ-/Borrow-Check
cargo build
cargo build --release
cargo run -- arg1 arg2
cargo test
cargo doc --open
cargo tree
cargo metadata --format-version 1
cargo clean
```

Dependency hinzufügen:

```bash
cargo add serde --features derive
cargo add anyhow
cargo add --dev tempfile
cargo remove anyhow
cargo update
```

> [!warning]
> `cargo update` ändert aufgelöste Versionen innerhalb der in `Cargo.toml` erlaubten Bereiche und aktualisiert `Cargo.lock`. Für Anwendungen `Cargo.lock` versionieren; bei Bibliotheken hängt die Lockfile-Strategie vom Veröffentlichungs- und Workspace-Kontext ab.

## Variablen, Typen und Kontrollfluss

```rust
fn main() {
    let name = "Ada";
    let mut count: u32 = 0;
    count += 1;
    println!("{name}: {count}");
}
```

Shadowing:

```rust
let input = "42";
let input: u32 = input.parse()?;
```

### Häufige Typen

| Gruppe | Beispiele |
|---|---|
| Integer | `i8..i128`, `u8..u128`, `isize`, `usize` |
| Float | `f32`, `f64` |
| Text | `char`, `&str`, `String` |
| Compound | Tuple, Array, Slice |
| Optional | `Option<T>` |
| Ergebnis | `Result<T, E>` |

Arrays und Slices:

```rust
let values = [1, 2, 3, 4];
let slice: &[i32] = &values[1..3];
```

Kontrollfluss ist Ausdruck:

```rust
let label = if score >= 90 { "A" } else { "B" };
```

Schleifen:

```rust
for value in &values {
    println!("{value}");
}

let result = loop {
    break 42;
};
```

## Ownership, Borrowing und Lifetimes

### Ownership-Regeln

1. Jeder Wert hat einen Owner.
2. Es gibt zu einem Zeitpunkt genau einen Owner.
3. Wenn der Owner den Scope verlässt, wird der Wert freigegeben.

Move:

```rust
let a = String::from("Hallo");
let b = a;               // Ownership nach b verschoben
// println!("{a}");     // Compile-Fehler
```

Clone:

```rust
let a = String::from("Hallo");
let b = a.clone();
```

Copy-Typen wie viele Zahlen werden kopiert.

### Borrowing

```rust
fn length(value: &str) -> usize {
    value.len()
}

let text = String::from("Hallo");
let n = length(&text);
```

Mutable Borrow:

```rust
fn append_suffix(value: &mut String) {
    value.push_str("!");
}
```

Grundregel:

```text
beliebig viele unveränderliche Referenzen
ODER
genau eine veränderliche Referenz
```

Non-Lexical Lifetimes beenden Borrows häufig nach letzter Verwendung, nicht erst am Blockende.

### String versus str

| Typ | Bedeutung |
|---|---|
| `String` | besitzender, veränderbarer UTF-8-Puffer |
| `&str` | geliehene UTF-8-Textsicht |

Funktionen bevorzugt `&str` akzeptieren, wenn kein Besitz nötig ist.

### Lifetimes

```rust
fn longest<'a>(left: &'a str, right: &'a str) -> &'a str {
    if left.len() >= right.len() { left } else { right }
}
```

Lifetime-Annotationen verlängern keine Lebensdauer; sie beschreiben Beziehungen zwischen Referenzen.

Struct mit Referenz:

```rust
struct View<'a> {
    title: &'a str,
}
```

> [!tip]
> Bei Lifetime-Problemen zuerst überlegen, ob der Typ wirklich Referenzen speichern muss. Besitzende Typen (`String`, `Vec<T>`, `Arc<T>`) können die API vereinfachen, kosten aber ggf. Allokation/Kopie.

## Structs, Enums und Pattern Matching

### Struct

```rust
#[derive(Debug, Clone)]
struct User {
    id: u64,
    name: String,
    active: bool,
}

impl User {
    fn new(id: u64, name: impl Into<String>) -> Self {
        Self { id, name: name.into(), active: true }
    }

    fn deactivate(&mut self) {
        self.active = false;
    }
}
```

### Enum

```rust
#[derive(Debug)]
enum Command {
    Start,
    Stop { force: bool },
    Write(String),
}
```

Match:

```rust
match command {
    Command::Start => start(),
    Command::Stop { force: true } => force_stop(),
    Command::Stop { force: false } => stop(),
    Command::Write(text) if !text.is_empty() => write(text),
    Command::Write(_) => {}
}
```

`if let`:

```rust
if let Some(value) = optional_value {
    println!("{value}");
}
```

`let else`:

```rust
let Some(user) = find_user(id) else {
    return Err(AppError::NotFound(id));
};
```

## Fehlerbehandlung

### Option

```rust
let first = values.first();              // Option<&T>
let name = user.map(|u| u.name.as_str()).unwrap_or("unbekannt");
```

### Result und `?`

```rust
use std::{fs, io};

fn read_config(path: &str) -> Result<String, io::Error> {
    let content = fs::read_to_string(path)?;
    Ok(content)
}
```

Eigener Fehler:

```rust
#[derive(Debug)]
enum AppError {
    Io(std::io::Error),
    InvalidConfig(String),
}
```

Mit Bibliothek wie `thiserror` ergonomischer für Bibliotheks-/Domänenfehler; `anyhow` eignet sich oft für Anwendungskontext und Fehlerketten.

```rust
use anyhow::{Context, Result};

fn load(path: &str) -> Result<String> {
    std::fs::read_to_string(path)
        .with_context(|| format!("Konfiguration {path} lesen"))
}
```

> [!warning]
> `unwrap()` und `expect()` sind für Invarianten, Tests und Prototypen sinnvoll, aber nicht als allgemeine Fehlerbehandlung an untrusted Eingaben oder Betriebsgrenzen.

Panic:

```rust
panic!("unwiederbringlicher Zustand");
```

Panic ist kein gewöhnlicher Rückgabefehler. Bibliotheken sollten erwartbare Fehler als `Result` modellieren.

## Traits, Generics und Iteratoren

### Trait

```rust
trait Render {
    fn render(&self) -> String;
}

impl Render for User {
    fn render(&self) -> String {
        format!("{} ({})", self.name, self.id)
    }
}
```

Generic Bound:

```rust
fn print_rendered<T: Render>(value: &T) {
    println!("{}", value.render());
}
```

Oder:

```rust
fn print_rendered(value: &impl Render) { ... }
```

Trait Object für dynamische Dispatch:

```rust
fn render_all(values: &[Box<dyn Render>]) { ... }
```

### Iteratoren

```rust
let names: Vec<String> = users
    .iter()
    .filter(|u| u.active)
    .map(|u| u.name.clone())
    .collect();
```

| Methode | Besitz |
|---|---|
| `iter()` | `&T` |
| `iter_mut()` | `&mut T` |
| `into_iter()` | `T`, konsumiert Container typischerweise |

Fehler sammeln:

```rust
let numbers: Result<Vec<i32>, _> = inputs
    .iter()
    .map(|s| s.parse::<i32>())
    .collect();
```

## Module, Crates und Features

```rust
// src/lib.rs
pub mod config;
mod internal;

pub use config::Config;
```

Sichtbarkeit minimal halten:

```rust
pub(crate) fn helper() {}
pub(super) struct Internal {}
```

Workspace:

```toml
[workspace]
members = ["crates/core", "crates/cli"]
resolver = "3"
```

Features:

```toml
[features]
default = ["tls"]
tls = ["dep:rustls"]

[dependencies]
rustls = { version = "0.23", optional = true }
```

```bash
cargo build --no-default-features
cargo build --features tls
cargo tree -e features
```

Features sind additiv gedacht; nicht als gegenseitig exklusive „Build-Modi“ ohne klare Validierung missbrauchen.

## Tests, Formatierung und Lints

### Unit Test

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deactivates_user() {
        let mut user = User::new(1, "Ada");
        user.deactivate();
        assert!(!user.active);
    }
}
```

Result-Test:

```rust
#[test]
fn parses_config() -> Result<(), Box<dyn std::error::Error>> {
    let _cfg = parse("key=value")?;
    Ok(())
}
```

Befehle:

```bash
cargo test
cargo test testname -- --nocapture
cargo test --doc
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
```

CI-Basis:

```bash
cargo check --all-targets --all-features
cargo test --all-features
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
```

> [!note]
> `-D warnings` in Bibliotheken über mehrere Rust-Versionen kann Wartung erzeugen. MSRV und Lintpolitik explizit festlegen.

## Concurrency und Async

### Threads

```rust
use std::thread;

let handle = thread::spawn(|| {
    expensive_work()
});
let result = handle.join().expect("thread panicked");
```

Channels:

```rust
use std::sync::mpsc;
let (tx, rx) = mpsc::channel();
```

Shared State:

```rust
use std::sync::{Arc, Mutex};
let shared = Arc::new(Mutex::new(Vec::new()));
```

Lockscope klein halten und keine blockierende Arbeit unter Mutex durchführen.

### Send und Sync

- `Send`: Wert darf zwischen Threads übertragen werden.
- `Sync`: Referenz auf Wert darf zwischen Threads geteilt werden.

Compiler leitet diese Auto-Traits weitgehend ab.

### Async

```rust
async fn fetch() -> Result<String, reqwest::Error> {
    reqwest::get("https://example.org").await?.text().await
}
```

Ein Runtime-Ökosystem wie Tokio stellt Executor, Timer und Async-I/O bereit.

```rust
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let body = fetch().await?;
    println!("{}", body.len());
    Ok(())
}
```

Regeln:

- CPU-/blocking Arbeit nicht auf Async-Executor blockieren.
- Cancellation und Timeouts modellieren.
- Tasks überwachen; Handles nicht unbeachtet verlieren.
- Concurrency begrenzen, z. B. Semaphore/Buffer.
- Async nur einsetzen, wenn I/O-Parallelität es rechtfertigt.

## I/O, Serde und CLI

### Dateien

```rust
use std::fs;
let content = fs::read_to_string("config.toml")?;
fs::write("output.txt", "Hallo\n")?;
```

Große Dateien gepuffert:

```rust
use std::io::{BufRead, BufReader};
let file = std::fs::File::open(path)?;
for line in BufReader::new(file).lines() {
    let line = line?;
}
```

### Serde

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct Config {
    endpoint: String,
    timeout_seconds: u64,
}

let cfg: Config = serde_json::from_str(json)?;
let text = serde_json::to_string_pretty(&cfg)?;
```

Untrusted Daten mit Größenlimits, strikten Typen und fachlicher Validierung behandeln.

### CLI

`clap`-Derive-Beispiel:

```rust
#[derive(clap::Parser)]
struct Args {
    #[arg(long, default_value_t = 30)]
    timeout: u64,
    path: std::path::PathBuf,
}
```

Exitcodes, stderr/stdout, `--help`, `--version` und maschinenlesbare Ausgabe bewusst gestalten.

## Unsafe, FFI und Sicherheit

`unsafe` erlaubt einige Operationen, hebt aber nicht alle Rust-Regeln auf. Innerhalb einer `unsafe`-Abstraktion müssen Invarianten dokumentiert und getestet sein.

Typische Unsafe-Fähigkeiten:

- Raw Pointer dereferenzieren
- unsafe Funktionen aufrufen
- mutable statics zugreifen
- unsafe Traits implementieren
- Union-Felder lesen

### FFI-Skizze

```rust
unsafe extern "C" {
    fn strlen(s: *const std::ffi::c_char) -> usize;
}
```

Grenzen:

- Ownership des Puffers
- Nullterminierung
- Alignment
- Lebensdauer
- Threading
- Panic darf nicht unkontrolliert über FFI-Grenze laufen
- C-ABI-kompatible Typen mit `#[repr(C)]`

### Dependency-Sicherheit

```bash
cargo tree -d
cargo metadata
cargo audit            # externes Tool
cargo deny check       # externes Tool
```

Lockfile, Reviews, minimale Features und vertrauenswürdige Crates. Buildskripte und proc-macros führen Code beim Build aus.

## Performance und Diagnose

### Releaseprofil

```toml
[profile.release]
lto = "thin"
codegen-units = 1
panic = "abort"
strip = "symbols"
```

Trade-offs in Buildzeit, Debuggability und Panicverhalten prüfen.

### Benchmark

`cargo bench` ist je Setup/Toolchain begrenzt; häufig Criterion verwenden. Immer Warmup, Datenmenge, CPU-Frequenz, Compilerflags und Varianz dokumentieren.

### Größe

```bash
cargo bloat --release       # externes Tool
size target/release/app
strip --strip-debug target/release/app
```

### Compilerfehler lesen

```bash
cargo check --message-format=short
rustc --explain E0382
```

Borrow-Fehler zerlegen:

1. Wer besitzt den Wert?
2. Wird er verschoben oder nur geliehen?
3. Wie lange lebt der Borrow wirklich?
4. Muss Rückgabewert referenzieren oder kann er besitzen?
5. Kann Scope/Datentyp vereinfacht werden?

### Backtrace

```bash
RUST_BACKTRACE=1 cargo run
RUST_BACKTRACE=full cargo test -- --nocapture
```

### Universelle Prüfreihenfolge

```bash
rustc --version --verbose
cargo --version
rustup show
cargo tree -d
cargo check --all-targets --all-features
cargo test
cargo clippy --all-targets --all-features
```

Dann kleinstes reproduzierbares Beispiel, konkrete Fehlermeldung und verwendete Features/Targets isolieren.

## Quellen
- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [The Cargo Book](https://doc.rust-lang.org/cargo/)
- [Rust Standard Library](https://doc.rust-lang.org/std/)
- [Rust Reference](https://doc.rust-lang.org/reference/)
- [Rustonomicon](https://doc.rust-lang.org/nomicon/)

## Verwandte Notizen
- [[Git-Premium-Spickzettel]]
- [[Make-und-Source-Builds-Premium-Spickzettel]]
- [[Neovim-LSP-Debugging-Premium-Spickzettel]]
