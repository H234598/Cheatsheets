---
title: "Git – Cheatsheet"
aliases: ["Git Cheatsheet", "Git CLI", "Versionsverwaltung mit Git"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [git, version-control, development, cli, devops]
source: "https://git-scm.com/docs"
---

# Git – Cheatsheet

> [!abstract] Zweck
> Ausführliche Praxisreferenz für Git: Objektmodell, Konfiguration, Staging, Commits, Branches, Merge/Rebase, Remotes, Wiederherstellung, Historienanalyse, Worktrees und sichere Zusammenarbeit.

> [!abstract] Kernidee
> Git speichert keine lineare Folge von Dateikopien, sondern unveränderliche Objekte und Verweise. Ein Branch ist im Wesentlichen ein beweglicher Zeiger auf einen Commit; `HEAD` zeigt auf den aktuell ausgecheckten Branch oder direkt auf einen Commit.

## Inhalt

- [[#Grundmodell]]
- [[#Installation und Konfiguration]]
- [[#Repository anlegen oder klonen]]
- [[#Status, Diff und Staging]]
- [[#Commits]]
- [[#Branches und Wechsel]]
- [[#Merge und Konflikte]]
- [[#Rebase]]
- [[#Remotes, Fetch, Pull und Push]]
- [[#Änderungen rückgängig machen]]
- [[#Stash, Tags und Releases]]
- [[#Historie untersuchen]]
- [[#Worktrees, Submodule und LFS]]
- [[#Hooks, Signaturen und Sicherheit]]
- [[#Diagnose-Reihenfolge]]

## Grundmodell

```text
Working Tree  --git add-->  Index/Staging  --git commit-->  Repository
     ▲                              │                           │
     └-------- git restore ---------┘                           │
                         Branch/HEAD ───────────────────────────┘
```

| Begriff | Bedeutung |
|---|---|
| **Working Tree** | aktuell ausgecheckte Dateien |
| **Index/Staging Area** | exakt vorbereiteter Inhalt des nächsten Commits |
| **Commit** | unveränderlicher Snapshot mit Eltern, Autor, Zeit und Nachricht |
| **Branch** | beweglicher Name, der auf einen Commit zeigt |
| **HEAD** | aktueller Branch beziehungsweise direkt ausgecheckter Commit |
| **Remote-Tracking Branch** | lokaler Stand eines entfernten Branches, z. B. `origin/main` |
| **Tag** | fester Name für einen Commit, häufig für Releases |
| **Ref** | allgemeiner Verweis wie Branch, Tag oder Remote-Tracking-Branch |
| **Reflog** | lokales Protokoll darüber, wohin Referenzen zeigten |

### Objekte ansehen

```bash
git rev-parse --show-toplevel
git rev-parse HEAD
git cat-file -t HEAD
git cat-file -p HEAD
git ls-tree -r --name-only HEAD
```

## Installation und Konfiguration

```bash
git --version
git help -a
git help config
git help revisions
```

### Identität

```bash
git config --global user.name 'Ada Admin'
git config --global user.email 'ada@example.org'
```

### Sinnvolle Defaults

```bash
git config --global init.defaultBranch main
git config --global pull.ff only
git config --global fetch.prune true
git config --global rerere.enabled true
git config --global diff.colorMoved zebra
git config --global core.autocrlf input   # Linux/macOS; Teamkonvention beachten
```

Windows je nach Projekt:

```powershell
git config --global core.autocrlf true
```

> [!warning] Zeilenenden sind Projektpolitik
> `core.autocrlf` nicht isoliert festlegen. Eine `.gitattributes` im Repository ist reproduzierbarer und gilt für alle Beteiligten.

Beispiel `.gitattributes`:

```gitattributes
* text=auto
*.sh text eol=lf
*.ps1 text eol=crlf
*.png binary
*.jpg binary
```

Konfiguration und Herkunft:

```bash
git config --list --show-origin
git config --show-scope --list
git config --get-regexp '^(user|core|pull|fetch)\.'
```

## Repository anlegen oder klonen

```bash
mkdir projekt && cd projekt
git init
```

```bash
git clone git@example.org:team/projekt.git
git clone --branch release/2.x --single-branch URL
git clone --filter=blob:none URL      # partieller Clone, Serverunterstützung nötig
```

Remote prüfen:

```bash
git remote -v
git remote show origin
```

## Status, Diff und Staging

### Status

```bash
git status
git status --short --branch
git status --porcelain=v2
```

Kurzstatus:

```text
??  untracked
 M  geändert, nicht gestaged
M   gestaged
MM  gestaged und danach erneut geändert
A   neu gestaged
D   gelöscht
UU  Mergekonflikt
```

### Diffs

```bash
git diff                         # Working Tree gegen Index
git diff --staged                # Index gegen HEAD
git diff HEAD                    # Working Tree + Index gegen HEAD
git diff main...feature          # Änderungen seit gemeinsamem Vorfahren
git diff --stat
git diff --word-diff
```

Pfad vom Optionsende trennen:

```bash
git diff -- path/mit-datei.txt
```

### Staging

```bash
git add datei.txt
git add src/
git add -p                         # Hunk-weise auswählen
git add -A                         # alle Änderungen inkl. Löschungen
git restore --staged datei.txt     # aus Index entfernen
```

Interaktives Patch-Staging:

```text
y = Hunk übernehmen
n = nicht übernehmen
s = Hunk teilen
e = Patch manuell bearbeiten
q = beenden
? = Hilfe
```

> [!tip]
> Vor jedem Commit mindestens `git diff` und `git diff --staged` lesen. Der Index ist kein lästiger Zwischenschritt, sondern das Werkzeug für atomare Commits.

## Commits

```bash
git commit -m 'fix: Zeitüberschreitung beim Import behandeln'
git commit -v                       # Diff im Editor
git commit --dry-run
git commit --amend                  # letzten lokalen Commit ersetzen
```

Alle bereits verfolgten Änderungen automatisch stagen:

```bash
git commit -am 'refactor: Parser vereinfachen'
```

Neue untracked Dateien sind dabei **nicht** enthalten.

### Gute Commit-Nachricht

```text
Kurzer Imperativ, idealerweise unter ca. 72 Zeichen

Warum war die Änderung nötig?
Welche fachliche/technische Wirkung hat sie?
Welche Randbedingungen oder Migrationen gelten?

Refs: ISSUE-123
```

### Atomarer Commit

Ein guter Commit:

- erfüllt genau einen nachvollziehbaren Zweck
- baut und testet möglichst erfolgreich
- enthält keine Zugangsdaten oder Zufallsdateien
- trennt reine Formatierung von Logikänderungen
- kann einzeln reviewed und notfalls revertiert werden

Fixup-Workflow:

```bash
git commit --fixup=<zielcommit>
git rebase -i --autosquash <basis>
```

## Branches und Wechsel

```bash
git branch
git branch --all --verbose --verbose
git switch -c feature/login
git switch main
git switch -                         # vorheriger Branch
git branch -d feature/login          # nur wenn gemergt
git branch -D experiment             # erzwingen
```

Remote-Branch auschecken:

```bash
git fetch origin
git switch --track origin/feature/login
```

Branch umbenennen:

```bash
git branch -m alter-name neuer-name
git push origin -u neuer-name
git push origin --delete alter-name
```

### Detached HEAD

```bash
git switch --detach <commit>
```

Arbeit retten:

```bash
git switch -c rescue/meine-arbeit
```

## Merge und Konflikte

```bash
git switch main
git fetch origin
git merge --ff-only origin/main
git merge feature/login
```

### Mergearten

| Art | Ergebnis |
|---|---|
| Fast-forward | Branchzeiger wird ohne Mergecommit vorgeschoben |
| Three-way merge | neuer Mergecommit mit zwei Eltern |
| Squash merge | Änderungen werden als ein neuer Commit übernommen; keine Mergebeziehung |

Explizit:

```bash
git merge --no-ff feature/login
git merge --squash feature/login
git merge --abort
```

### Konflikte lösen

```bash
git status
git diff --name-only --diff-filter=U
git checkout --ours -- path
git checkout --theirs -- path
# Datei bewusst bearbeiten
git add path
git commit
```

`ours` und `theirs` hängen vom Vorgang ab; bei Rebase ist die intuitive Zuordnung oft überraschend. Inhalt prüfen, nicht blind auswählen.

Konfliktmarker:

```text
<<<<<<< HEAD
aktuelle Seite
=======
andere Seite
>>>>>>> feature/login
```

## Rebase

Rebase setzt Commits auf eine neue Basis und schreibt deren IDs neu.

```bash
git switch feature/login
git fetch origin
git rebase origin/main
```

Konfliktablauf:

```bash
git status
# bearbeiten
git add konfliktdatei
git rebase --continue
# oder
git rebase --abort
```

Interaktiv:

```bash
git rebase -i HEAD~5
```

Aktionen:

```text
pick    übernehmen
reword  Nachricht ändern
edit    Commit anhalten und ändern
squash  mit Vorgänger zusammenführen, Nachrichten kombinieren
fixup   mit Vorgänger zusammenführen, Nachricht verwerfen
drop    entfernen
```

> [!danger] Öffentliche Historie
> Bereits von anderen genutzte Commits nicht ohne abgestimmten Prozess rebasen/umschreiben. Erforderlichenfalls `--force-with-lease`, niemals reflexartig `--force`.

Sicherer Force-Push:

```bash
git push --force-with-lease origin feature/login
```

## Remotes, Fetch, Pull und Push

```bash
git remote -v
git remote add upstream https://example.org/original/projekt.git
git fetch --all --prune
git fetch origin main
git push -u origin feature/login
```

### Unterschiede

| Befehl | Wirkung |
|---|---|
| `fetch` | lädt Objekte/Refs, verändert aktuellen Branch nicht |
| `merge origin/main` | integriert den geladenen Stand |
| `pull` | `fetch` plus konfiguriertes Integrationsverfahren |
| `push` | überträgt lokale Refs/Objekte zum Remote |

Bewusste Pull-Strategien:

```bash
git pull --ff-only
git pull --rebase
git pull --no-rebase
```

### Divergenz ansehen

```bash
git log --oneline --left-right --graph HEAD...origin/main
git rev-list --left-right --count HEAD...origin/main
```

### Remote-URL ändern

```bash
git remote set-url origin git@example.org:team/projekt.git
```

## Änderungen rückgängig machen

### Uncommitted

Datei auf Indexstand zurücksetzen:

```bash
git restore datei.txt
```

Datei aus Index nehmen:

```bash
git restore --staged datei.txt
```

Alles Untracked zunächst nur anzeigen:

```bash
git clean -nd
git clean -ndX       # nur ignorierte Dateien
```

Dann bewusst löschen:

```bash
git clean -fd
```

> [!danger]
> `git restore`, `git reset --hard` und `git clean` können nicht committete Daten zerstören. Vorher `status`, Diff und gegebenenfalls Stash/Kopie.

### Commit rückgängig machen

Öffentliche Historie:

```bash
git revert <commit>
git revert -m 1 <mergecommit>
```

Lokale Historie verschieben:

```bash
git reset --soft HEAD~1    # Änderungen bleiben gestaged
git reset --mixed HEAD~1   # Änderungen bleiben ungestaged
git reset --hard HEAD~1    # Working Tree ebenfalls zurück
```

### Verlorenen Stand finden

```bash
git reflog
git show HEAD@{3}
git branch rescue HEAD@{3}
```

Nach Objektverlust:

```bash
git fsck --lost-found
```

## Stash, Tags und Releases

### Stash

```bash
git stash push -u -m 'WIP Loginmaske'
git stash list
git stash show -p stash@{0}
git stash apply stash@{0}
git stash pop
git stash branch rescue/stash stash@{0}
git stash drop stash@{0}
```

### Tags

Annotierter Tag:

```bash
git tag -a v2.1.0 -m 'Release 2.1.0'
git show v2.1.0
git push origin v2.1.0
```

Signiert:

```bash
git tag -s v2.1.0 -m 'Release 2.1.0'
git tag -v v2.1.0
```

Tag löschen:

```bash
git tag -d v2.1.0
git push origin :refs/tags/v2.1.0
```

## Historie untersuchen

```bash
git log --oneline --decorate --graph --all
git log --stat
git log -p -- path/datei
git log --follow -- path/datei
git show <commit>
git blame -L 20,40 datei.py
```

Suche nach Textänderung:

```bash
git log -S'alterFunktionsname' -p
git log -G'regul[aä]r' -p
```

Fehlerursache binär suchen:

```bash
git bisect start
git bisect bad
git bisect good v2.0.0
# testen, dann jeweils:
git bisect good
# oder
git bisect bad
git bisect reset
```

Automatisch:

```bash
git bisect run ./test.sh
```

## Worktrees, Submodule und LFS

### Worktrees

Mehrere Branches parallel auschecken:

```bash
git worktree list
git worktree add ../projekt-hotfix -b hotfix/2.1 origin/main
git worktree remove ../projekt-hotfix
git worktree prune
```

Ideal für parallele Reviews, Hotfixes und Builds ohne ständiges Stashen.

### Submodule

```bash
git submodule add https://example.org/lib.git vendor/lib
git submodule update --init --recursive
git clone --recurse-submodules URL
git submodule foreach --recursive git status
```

Ein Submodule speichert im Elternrepository einen Commitzeiger. „Neuester Branchstand“ wird nicht automatisch übernommen.

### Git LFS

```bash
git lfs install
git lfs track '*.psd'
git add .gitattributes
git lfs ls-files
```

Große Binärdateien nicht nachträglich ohne Migrationsplanung umschreiben.

## Hooks, Signaturen und Sicherheit

### Hooks

Lokale Hooks liegen in `.git/hooks/`, werden aber nicht normal versioniert. Teamweite Hooks über Framework, `core.hooksPath` oder CI reproduzierbar machen.

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

### Commit signieren

SSH-Signaturen:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

Oder GPG entsprechend Teamrichtlinie. Verifikation:

```bash
git log --show-signature -1
git verify-commit HEAD
```

### Geheimnisse

- Geheimnisse nie committen.
- `.gitignore` verhindert nur neues Tracking, entfernt keine Historie.
- Bei Leak: Zugang widerrufen/rotieren **vor** Historienbereinigung.
- Secret Scanner und Push Protection einsetzen.
- Historienrewrite mit `git filter-repo` geplant und teamweit koordinieren.

## Diagnose-Reihenfolge

```bash
git status --short --branch
git remote -v
git branch -vv
git log --oneline --decorate --graph --all -20
git diff
git diff --staged
git config --list --show-origin
```

Dann:

1. Ziel klären: Daten retten, Branch synchronisieren oder Historie korrigieren?
2. Vor destruktiven Befehlen neuen Rettungsbranch erstellen:
   ```bash
   git branch rescue/$(date +%Y%m%d-%H%M%S)
   ```
3. `reflog` prüfen.
4. Lokalen, Index- und Remote-Stand getrennt betrachten.
5. Bei Pushproblem Authentisierung, Remote-URL und Branchschutz prüfen.
6. Bei Konflikt gemeinsamen Vorfahren und Integrationsrichtung klären.
7. Erst nach Sicherung `reset --hard`, `clean` oder Force-Push verwenden.

### Universelle Merksätze

```text
fetch verändert deinen Branch nicht.
add bereitet Inhalt vor, nicht nur Dateinamen.
commit speichert den Index.
branch ist ein Zeiger.
rebase schreibt Commit-IDs neu.
revert ist für veröffentlichte Historie.
reflog rettet viele lokale Fehler.
--force-with-lease ist sicherer als --force.
```

## Quellen
- [Offizielle Git-Dokumentation](https://git-scm.com/docs)
- [Pro Git Buch](https://git-scm.com/book/en/v2)
- [git-diff](https://git-scm.com/docs/git-diff)
- [git-commit](https://git-scm.com/docs/git-commit)

## Verwandte Notizen
- [[GitHub-Cheatsheet]]
- [[GitLab-Cheatsheet]]
- [[SSH-Cheatsheet]]
- [[Neovim-Cheatsheet]]
