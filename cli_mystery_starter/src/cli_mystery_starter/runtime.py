from __future__ import annotations

import cmd
import json
import shlex
from pathlib import Path


from . import contract, verifier
from .session import SessionStore


SURFACES = contract.surfaces_map()


def load_title(root: Path) -> str:
    config_path = root / "mystery_config.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            title = data.get("display_title")
            if isinstance(title, str) and title.strip():
                return title.strip()
        except json.JSONDecodeError:
            pass
    return root.name.replace("-", " ").replace("_", " ").title()


def resolve_project_path(current: Path, root: Path, raw: str) -> Path:
    base = root if raw.startswith("/") else current
    raw_target = base / raw.lstrip("/")
    walker = raw_target
    seen = 0
    while seen < 64:
        if walker.is_symlink():
            raise ValueError("Symlinks are not allowed inside the case file.")
        if walker == walker.parent:
            break
        try:
            walker.relative_to(root)
        except ValueError:
            break
        walker = walker.parent
        seen += 1
    candidate = raw_target.resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("Path escapes the case file.") from exc
    return candidate


def format_project_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def check_answer(project_root: Path, guess: str) -> bool:
    encoded = (project_root / "encoded").read_text(encoding="utf-8").strip()
    return verifier.verify(encoded, guess)


_RUNTIME_REQUIRED = ("game", "game/incident", "game/people", "hints", "encoded")


def validate_runtime_project(project_root: Path) -> list[str]:
    errors: list[str] = []
    if not project_root.exists():
        errors.append(f"Project not found: {project_root}")
        return errors
    if not project_root.is_dir():
        errors.append(f"Project root is not a directory: {project_root}")
        return errors
    for rel in _RUNTIME_REQUIRED:
        if not (project_root / rel).exists():
            errors.append(f"Missing runtime path: {rel}")
    return errors


class InvestigationShell(cmd.Cmd):
    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root.resolve()
        self.game_root = self.project_root / "game"
        self.title = load_title(self.project_root)
        self.intro = (
            f"{self.title}\n"
            "Type 'help' for commands. Start with 'ls' or 'cat incident'.\n"
        )
        self.current = self.game_root
        state = SessionStore.load(self.project_root)
        self.case_notes: list[str] = list(state["notes"])
        self.suspects: list[str] = list(state["suspects"])
        self.visited: set[str] = set(state["visited"])
        self.prompt = self._prompt()

    def _prompt(self) -> str:
        rel = self.current.relative_to(self.project_root)
        return f"[{rel.as_posix()}]$ "

    def _set_current(self, path: Path) -> None:
        self.current = path
        self.prompt = self._prompt()

    def _persist(self) -> None:
        SessionStore.save(
            self.project_root,
            notes=self.case_notes,
            suspects=self.suspects,
            visited=self.visited,
        )

    def _read_file(self, path: Path) -> str:
        if not path.exists():
            raise ValueError(f"Not found: {format_project_path(path, self.project_root)}")
        if path.is_dir():
            raise ValueError(f"Is a directory: {format_project_path(path, self.project_root)}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"Cannot read {format_project_path(path, self.project_root)}: not UTF-8 text "
                f"(decode error at byte {exc.start})"
            ) from exc
        self.visited.add(format_project_path(path, self.project_root))
        return text

    def _iter_files(self, path: Path) -> list[Path]:
        if path.is_file():
            return [path]
        return sorted(p for p in path.rglob("*") if p.is_file())

    def do_pwd(self, arg: str) -> None:
        """pwd   print the current working directory inside the case file"""
        print(format_project_path(self.current, self.project_root))

    def do_ls(self, arg: str) -> None:
        """ls [path]   list directory contents"""
        raw = arg.strip()
        try:
            target = resolve_project_path(self.current, self.project_root, raw) if raw else self.current
        except ValueError as exc:
            print(exc)
            return
        if not target.exists():
            print("Path not found.")
            return
        if target.is_file():
            print(format_project_path(target, self.project_root))
            return
        for entry in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            print(f"{entry.name}{'/' if entry.is_dir() else ''}")

    def do_cd(self, arg: str) -> None:
        """cd <path>   change directory; defaults to `game/` when called without an argument"""
        raw = arg.strip() or "game"
        try:
            target = resolve_project_path(self.current, self.project_root, raw)
        except ValueError as exc:
            print(exc)
            return
        if not target.exists() or not target.is_dir():
            print("Directory not found.")
            return
        self._set_current(target)

    def do_cat(self, arg: str) -> None:
        """cat <path>   print the contents of a file"""
        raw = arg.strip()
        if not raw:
            print("Usage: cat <path>")
            return
        try:
            print(self._read_file(resolve_project_path(self.current, self.project_root, raw)))
        except ValueError as exc:
            print(exc)

    def do_head(self, arg: str) -> None:
        """head <path> [count]   print the first `count` lines (default 10)"""
        parts = shlex.split(arg)
        if not parts:
            print("Usage: head <path> [count]")
            return
        try:
            count = int(parts[1]) if len(parts) > 1 else 10
        except ValueError:
            print("Usage: head <path> [count]  (count must be an integer)")
            return
        try:
            text = self._read_file(resolve_project_path(self.current, self.project_root, parts[0]))
        except ValueError as exc:
            print(exc)
            return
        print("\n".join(text.splitlines()[:count]))

    def do_tail(self, arg: str) -> None:
        """tail <path> [count]   print the last `count` lines (default 10)"""
        parts = shlex.split(arg)
        if not parts:
            print("Usage: tail <path> [count]")
            return
        try:
            count = int(parts[1]) if len(parts) > 1 else 10
        except ValueError:
            print("Usage: tail <path> [count]  (count must be an integer)")
            return
        try:
            text = self._read_file(resolve_project_path(self.current, self.project_root, parts[0]))
        except ValueError as exc:
            print(exc)
            return
        print("\n".join(text.splitlines()[-count:]))

    def do_grep(self, arg: str) -> None:
        """grep <text> [path]   case-insensitive substring search across file contents"""
        parts = shlex.split(arg)
        if not parts:
            print("Usage: grep <pattern> [path]")
            return
        pattern = parts[0].lower()
        try:
            base = resolve_project_path(self.current, self.project_root, parts[1]) if len(parts) > 1 else self.current
        except ValueError as exc:
            print(exc)
            return
        if not base.exists():
            print("Path not found.")
            return
        hits = 0
        for file_path in self._iter_files(base):
            try:
                with file_path.open("r", encoding="utf-8") as fh:
                    for idx, line in enumerate(fh, start=1):
                        if pattern in line.lower():
                            line_out = line.rstrip("\n")
                            print(f"{format_project_path(file_path, self.project_root)}:{idx}: {line_out}")
                            hits += 1
            except (UnicodeDecodeError, OSError):
                continue
        if hits == 0:
            print("No matches.")

    def do_find(self, arg: str) -> None:
        """find <substring> [path]   list filenames matching substring (case-insensitive)"""
        parts = shlex.split(arg)
        if not parts:
            print("Usage: find <substring> [path]")
            return
        needle = parts[0].lower()
        try:
            base = (
                resolve_project_path(self.current, self.project_root, parts[1])
                if len(parts) > 1 else self.current
            )
        except ValueError as exc:
            print(exc)
            return
        if not base.exists():
            print("Path not found.")
            return
        hits = 0
        for file_path in self._iter_files(base):
            if needle in file_path.name.lower():
                print(format_project_path(file_path, self.project_root))
                hits += 1
        if hits == 0:
            print("No matching filenames.")

    def do_progress(self, arg: str) -> None:
        """progress   summarize how much of the case file you have read"""
        all_files = self._iter_files(self.game_root)
        total = len(all_files)
        seen = sum(
            1 for p in all_files
            if format_project_path(p, self.project_root) in self.visited
        )
        pct = (seen / total * 100) if total else 0.0
        print(f"Read {seen}/{total} game files ({pct:.0f}%).")
        if self.suspects:
            print(f"Tracking {len(self.suspects)} suspect(s).")
        if self.case_notes:
            print(f"{len(self.case_notes)} note(s) recorded.")

    def do_open(self, arg: str) -> None:
        """open <surface>   jump to a known surface (incident, people, logs, ...)"""
        key = arg.strip().lower()
        path_parts = SURFACES.get(key)
        if path_parts is None:
            print("Unknown surface. Try: " + ", ".join(sorted(SURFACES)))
            return
        target = self.project_root.joinpath(*path_parts)
        if not target.exists():
            print(f"Surface `{key}` is missing on disk: {format_project_path(target, self.project_root)}")
            return
        if target.is_dir():
            self._set_current(target)
            self.do_ls("")
            return
        try:
            print(self._read_file(target))
        except ValueError as exc:
            print(exc)

    def do_note(self, arg: str) -> None:
        """note <text>   record a free-form investigation note"""
        text = arg.strip()
        if not text:
            print("Usage: note <text>")
            return
        self.case_notes.append(text)
        self._persist()
        print(f"Saved note {len(self.case_notes)}.")

    def do_notes(self, arg: str) -> None:
        """notes   list every note recorded this session"""
        if not self.case_notes:
            print("No notes yet.")
            return
        for idx, note in enumerate(self.case_notes, start=1):
            print(f"{idx}. {note}")

    def do_mark(self, arg: str) -> None:
        """mark <name>   add a name to the suspect list"""
        name = arg.strip()
        if not name:
            print("Usage: mark <name>")
            return
        self.suspects.append(name)
        self._persist()
        print(f"Tracked suspect: {name}")

    def do_suspects(self, arg: str) -> None:
        """suspects   list every name marked as a suspect this session"""
        if not self.suspects:
            print("No suspects tracked.")
            return
        for idx, suspect in enumerate(self.suspects, start=1):
            print(f"{idx}. {suspect}")

    def do_hint(self, arg: str) -> None:
        """hint <1-4>   read a progressive hint"""
        num = arg.strip()
        if num not in {"1", "2", "3", "4"}:
            print("Usage: hint <1-4>")
            return
        print((self.project_root / "hints" / f"hint{num}").read_text(encoding="utf-8"))

    def do_accuse(self, arg: str) -> None:
        """accuse <name>   submit your final answer; case-sensitive, whitespace tolerant"""
        name = arg.strip()
        if not name:
            print("Usage: accuse <name>")
            return
        if check_answer(self.project_root, name):
            print("Accusation accepted.")
            print(f"You solved {self.title}.")
        else:
            print("That accusation does not match the evidence trail.")

    def do_help(self, arg: str) -> None:
        topic = arg.strip()
        if topic:
            method = getattr(self, f"do_{topic}", None)
            if method and method.__doc__:
                print(method.__doc__.strip())
                return
            print(f"No help available for {topic!r}.")
            return
        print(
            "Commands:\n"
            "  ls [path]         list files\n"
            "  cd <path>         change directory\n"
            "  pwd               show current location\n"
            "  cat <path>        print a file\n"
            "  head <path> [n]   show first lines\n"
            "  tail <path> [n]   show last lines\n"
            "  grep <text> [p]   search file contents\n"
            "  find <text> [p]   search filenames\n"
            "  open <surface>    jump to incident/people/logs/interviews/locations/registry/memberships/hints/design\n"
            "  progress          show how much of the case you have read\n"
            "  hint <1-4>        read a hint\n"
            "  mark <name>       track a suspect\n"
            "  suspects          list tracked suspects\n"
            "  note <text>       save a note\n"
            "  notes             list notes\n"
            "  journal           recap files read, suspects, and notes\n"
            "  save              persist progress to .session.json\n"
            "  accuse <name>     submit final answer\n"
            "  quit              save progress and exit\n"
        )

    def do_quit(self, arg: str) -> bool:
        """quit   save your progress and exit"""
        self._persist()
        print("Case file closed.")
        return True

    def do_save(self, arg: str) -> None:
        """save   write your notes, suspects, and visited files to .session.json"""
        self._persist()
        print(f"Session saved to {SessionStore.FILENAME}.")

    def do_journal(self, arg: str) -> None:
        """journal   recap of files read, suspects marked, and notes recorded"""
        visited = sorted(self.visited)
        print(f"Files read: {len(visited)}")
        for path in visited:
            print(f"  {path}")
        if self.suspects:
            print(f"\nSuspects ({len(self.suspects)}):")
            for name in self.suspects:
                print(f"  - {name}")
        if self.case_notes:
            print(f"\nNotes ({len(self.case_notes)}):")
            for idx, note in enumerate(self.case_notes, start=1):
                print(f"  {idx}. {note}")

    def do_exit(self, arg: str) -> bool:
        return self.do_quit(arg)

    def do_EOF(self, arg: str) -> bool:
        print()
        return self.do_quit(arg)

    def default(self, line: str) -> None:
        print(f"Unknown command: {line}")

    def emptyline(self) -> None:
        return


def play_project(project_root: Path) -> int:
    errors = validate_runtime_project(project_root)
    if errors:
        for error in errors:
            print(error)
        return 1
    InvestigationShell(project_root).cmdloop()
    return 0
