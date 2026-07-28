---
title: "Flutter – Cheatsheet"
aliases: ["Glutter", "Flutter Cheatsheet", "Dart Flutter"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [flutter, dart, mobile, web, desktop, development]
source: "https://flutter.dev/"
---

# Flutter – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für Flutter und Dart: Setup, Widgets, Layout, State, Navigation, Async, Netzwerk, Tests, Build, Performance und Diagnose.

> [!note] Interpretation
> Der Wunsch „glutter“ wird hier als **Flutter** interpretiert. Flutter ist ein Open-Source-Framework für nativ kompilierte Anwendungen aus einer gemeinsamen Dart-Codebasis für mehrere Plattformen.

## Inhalt

- [[#Setup und Projekt]]
- [[#Widget-Modell]]
- [[#Layout]]
- [[#State Management]]
- [[#Navigation]]
- [[#Async, HTTP und JSON]]
- [[#Assets, Themes und Internationalisierung]]
- [[#Tests]]
- [[#Build und Release]]
- [[#Performance und Diagnose]]

## Setup und Projekt

```bash
flutter --version
flutter doctor -v
flutter devices
flutter emulators
```

Projekt:

```bash
flutter create meine_app
cd meine_app
flutter run
flutter analyze
flutter test
```

Plattformen anzeigen/aktivieren:

```bash
flutter config --list
flutter create --platforms=android,ios,web,windows,linux,macos .
```

Dependencies:

```bash
flutter pub add http
flutter pub get
flutter pub outdated
flutter pub upgrade --major-versions
```

> [!warning]
> `pub upgrade --major-versions` kann Breaking Changes einführen. Lockfile, Changelog und Tests prüfen; Anwendungen sollten `pubspec.lock` üblicherweise versionieren.

## Widget-Modell

Alles Sichtbare ist ein Widget. Widgets sind unveränderliche Konfigurationsobjekte; Flutter erzeugt daraus Element- und Renderbäume.

```text
Widget Tree      Beschreibung
Element Tree     langlebige Instanzen/State-Verknüpfung
Render Tree      Layout und Paint
```

### Stateless

```dart
class Greeting extends StatelessWidget {
  const Greeting({super.key, required this.name});
  final String name;

  @override
  Widget build(BuildContext context) {
    return Text('Hallo $name');
  }
}
```

### Stateful

```dart
class Counter extends StatefulWidget {
  const Counter({super.key});

  @override
  State<Counter> createState() => _CounterState();
}

class _CounterState extends State<Counter> {
  int count = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('$count'),
        FilledButton(
          onPressed: () => setState(() => count++),
          child: const Text('Erhöhen'),
        ),
      ],
    );
  }
}
```

`setState` nur für synchrone Stateänderung aufrufen; asynchrone Arbeit davor/danach durchführen und `mounted` prüfen.

```dart
final value = await loadValue();
if (!mounted) return;
setState(() => data = value);
```

## Layout

Flutter-Regel:

```text
Constraints go down.
Sizes go up.
Parents set positions.
```

### Häufige Widgets

| Zweck | Widgets |
|---|---|
| linear | `Row`, `Column` |
| Abstand/Größe | `Padding`, `SizedBox`, `ConstrainedBox` |
| flexibel | `Expanded`, `Flexible`, `Spacer` |
| Überlagerung | `Stack`, `Positioned` |
| Scrollen | `ListView`, `GridView`, `CustomScrollView` |
| responsiv | `LayoutBuilder`, `MediaQuery` |
| Ausrichtung | `Align`, `Center` |

Beispiel:

```dart
Row(
  children: [
    const Icon(Icons.info),
    const SizedBox(width: 8),
    Expanded(
      child: Text(
        message,
        overflow: TextOverflow.ellipsis,
      ),
    ),
  ],
)
```

### Unbounded Constraints

Typischer Fehler: `Expanded` in einem unbeschränkt scrollenden Bereich. Lösung hängt vom Ziel ab:

- `Expanded` entfernen
- feste/abgeleitete Höhe geben
- `ListView` statt `Column` verwenden
- `shrinkWrap` nur bewusst, da teurer
- Layout mit `LayoutBuilder` analysieren

## State Management

Stufenmodell:

1. lokaler UI-State: `StatefulWidget`/`setState`
2. abgeleiteter State: Getter/immutable Model
3. geteilte kleine Abhängigkeit: `InheritedWidget`/Provider
4. komplexere App: Riverpod, Bloc, Redux o. Ä. nach Teamstandard

> [!tip]
> Nicht jedes Formularfeld braucht ein globales State-Framework. State so lokal wie möglich halten und Datenfluss eindeutig machen.

Immutable Datenklasse:

```dart
class User {
  const User({required this.id, required this.name});
  final String id;
  final String name;

  User copyWith({String? name}) => User(id: id, name: name ?? this.name);
}
```

State trennen:

```text
UI State: ausgewählter Tab, Animation, Fokus
Domain State: Benutzer, Warenkorb, Berechtigungen
Server Cache: geladene API-Daten, Refresh, Fehler
```

## Navigation

Einfach:

```dart
Navigator.of(context).push(
  MaterialPageRoute(builder: (_) => const DetailPage()),
);
```

Zurück mit Ergebnis:

```dart
final result = await Navigator.of(context).push<String>(...);
```

Für Deep Links, Web-URLs und komplexe verschachtelte Navigation einen deklarativen Router einsetzen. Routeparameter validieren und unbekannte Pfade behandeln.

## Async, HTTP und JSON

### Future

```dart
Future<User> loadUser(String id) async {
  final response = await http.get(Uri.parse('$baseUrl/users/$id'));
  if (response.statusCode != 200) {
    throw HttpException('HTTP ${response.statusCode}');
  }
  return User.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
}
```

Timeout:

```dart
final response = await http
    .get(uri)
    .timeout(const Duration(seconds: 10));
```

### FutureBuilder

```dart
FutureBuilder<User>(
  future: userFuture,
  builder: (context, snapshot) {
    if (snapshot.connectionState != ConnectionState.done) {
      return const CircularProgressIndicator();
    }
    if (snapshot.hasError) return Text('Fehler: ${snapshot.error}');
    return Text(snapshot.requireData.name);
  },
)
```

Future nicht in jedem `build` neu erzeugen; in `initState` oder State-Layer halten.

### Netzwerkregeln

- HTTPS und Zertifikatsprüfung nicht deaktivieren.
- Auth-Tokens in sicherem plattformspezifischem Storage, nicht in Source/SharedPreferences.
- Retries nur bei idempotenten Operationen und mit Backoff.
- Offline-, Timeout- und Fehlerzustände gestalten.
- API-Modelle validieren; unbekannte/null-Felder robust behandeln.
- Logging ohne Token/PII.

## Assets, Themes und Internationalisierung

`pubspec.yaml`:

```yaml
flutter:
  uses-material-design: true
  assets:
    - assets/images/
```

Theme:

```dart
MaterialApp(
  theme: ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
    useMaterial3: true,
  ),
  home: const HomePage(),
)
```

Responsiv/adaptiv:

- Breakpoints aus Inhalt und Nutzung ableiten, nicht aus Gerätenamen.
- Touchziele, Tastatur, Maus, Hover und Screen Reader beachten.
- SafeArea und Textskalierung testen.
- Plattformkonventionen respektieren, ohne getrennte Codebasis zu erzwingen.

Internationalisierung über Flutter-Localization/ARB; Strings nicht hart in Widgets verteilen.

## Tests

### Unit

```dart
test('Summe wird berechnet', () {
  expect(add(2, 3), 5);
});
```

### Widget

```dart
testWidgets('Zähler erhöht sich', (tester) async {
  await tester.pumpWidget(const MaterialApp(home: Counter()));
  await tester.tap(find.text('Erhöhen'));
  await tester.pump();
  expect(find.text('1'), findsOneWidget);
});
```

### Befehle

```bash
flutter test
flutter test test/widget_test.dart
flutter test --coverage
flutter analyze
dart format --output=none --set-exit-if-changed .
```

Integration Tests auf echten Zielplattformen/Emulatoren; Netzwerk und Plattformkanäle gezielt faken oder in Testumgebung prüfen.

## Build und Release

```bash
flutter build apk --release
flutter build appbundle --release
flutter build ios --release
flutter build web --release
flutter build windows --release
flutter build linux --release
flutter build macos --release
```

Vor Release:

```text
[ ] Version/build number
[ ] Signing/Keystore/Provisioning
[ ] Produktions-API und Feature Flags
[ ] Datenschutz/Permissions
[ ] Crash Reporting und Symbole
[ ] Obfuscation/Symbol-Dateien, falls genutzt
[ ] Release Notes
[ ] Smoke Test auf realen Geräten
[ ] Store-Metadaten und Screenshots
```

Android-Berechtigungen minimal; iOS Usage Descriptions vollständig. Signierschlüssel sichern, aber nie ins Repository.

## Performance und Diagnose

### Werkzeuge

```bash
flutter run --profile
flutter run --release
flutter pub deps
flutter clean
flutter doctor -v
```

DevTools:

- Performance Timeline
- CPU Profiler
- Memory
- Network
- Widget Inspector
- App Size

### Häufige Optimierungen

- `const`-Konstruktoren verwenden.
- große Listen mit Buildern erzeugen.
- Rebuild-Grenzen klein halten.
- teure Arbeit aus `build` entfernen.
- Bilder passend dimensionieren und cachen.
- Animationen im Profile Mode messen.
- JSON/CPU-schwere Arbeit gegebenenfalls in Isolate auslagern.
- zuerst messen, dann optimieren.

### Typische Fehler

| Symptom | Prüfung |
|---|---|
| `RenderFlex overflowed` | `Expanded/Flexible`, Umbruch, Scrollcontainer, Bildschirmgröße |
| `setState() called after dispose()` | asynchroner Callback, `mounted`, Subscription abbrechen |
| Hot Reload zeigt Änderung nicht | State/Initialisierung geändert; Hot Restart nötig |
| Plugin fehlt auf Plattform | Plattformunterstützung und native Konfiguration prüfen |
| Build nur in CI kaputt | SDK-/JDK-/Xcode-Version, Lockfile, Secrets, Case Sensitivity |
| App ruckelt | Profile Mode + DevTools, Build-/Raster-Threads untersuchen |

Universelle Diagnose:

```bash
flutter doctor -v
flutter analyze
flutter test
flutter run -v
```

Dann Zielplattform, SDK-Version, reproduzierbares Minimalbeispiel und letzte Dependencyänderung isolieren.

## Quellen
- [Flutter](https://flutter.dev/)
- [Flutter Documentation](https://docs.flutter.dev/)
- [Dart Documentation](https://dart.dev/guides)
- [Flutter Testing](https://docs.flutter.dev/testing/overview)

## Verwandte Notizen
- [[Android-USB-Debugging-Cheatsheet]]
- [[Git-Cheatsheet]]
- [[Neovim-Cheatsheet]]
