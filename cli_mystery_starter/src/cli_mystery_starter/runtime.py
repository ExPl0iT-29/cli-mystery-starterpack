from __future__ import annotations

import cmd
import hashlib
import json
import shlex
from pathlib import Path


SURFACES = {
    "incident": ("game", "incident"),
    "people": ("game", "people"),
    "logs": ("game", "logs"),
    "interviews": ("game", "interviews"),
    "locations": ("game", "locations"),
    "registry": ("game", "registry"),
    "memberships": ("game", "memberships"),
    "hints": ("hints",),
    "design": ("design",),
}


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
    expected = (project_root / "encoded").read_text(encoding="utf-8").strip()
    digest = hashlib.md5(guess.strip().encode("utf-8"), usedforsecurity=False).hexdigest()
    return digest == expected


def validate_runtime_project(project_root: Path) -> list[str]:
    errors: list[str] = []
    if not project_root.exists():
        errors.append(f"Project not found: {project_root}")
        return errors
    if not project_root.is_dir():
        errors.append(f"Project root is not a directory: {project_root}")
        return errors
    for rel in ("game", "game/incident", "game/people", "hints", "encoded"):
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
        self.suspects: list[str] = []
        self.case_notes: list[str] = []
        self.prompt = self._prompt()

    def _prompt(self) -> str:
        rel = self.current.relative_to(self.project_root)
        return f"[{rel.as_posix()}]$ "

    def _set_current(self, path: Path) -> None:
        self.current = path
        self.prompt = self._prompt()

    def _read_file(self, path: Path) -> str:
        if not path.exists():
            raise ValueError(f"Not found: {format_project_path(path, self.project_root)}")
        if path.is_dir():
            raise ValueError(f"Is a directory: {format_project_path(path, self.project_root)}")
        return path.read_text(encoding="utf-8")

    def _iter_files(self, path: Path) -> list[Path]:
        if path.is_file():
            return [path]
        return sorted(p for p in path.rglob("*") if p.is_file())

    def do_pwd(self, arg: str) -> None:
        print(format_project_path(self.current, self.project_root))

    def do_ls(self, arg: str) -> None:
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
        raw = arg.strip()
        if not raw:
            print("Usage: cat <path>")
            return
        try:
            print(self._read_file(resolve_project_path(self.current, self.project_root, raw)))
        except ValueError as exc:
            print(exc)

    def do_head(self, arg: str) -> None:
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
            lines = file_path.read_text(encoding="utf-8").splitlines()
            for idx, line in enumerate(lines, start=1):
                if pattern in line.lower():
                    print(f"{format_project_path(file_path, self.project_root)}:{idx}: {line}")
                    hits += 1
        if hits == 0:
            print("No matches.")

    def do_open(self, arg: str) -> None:
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
        text = arg.strip()
        if not text:
            print("Usage: note <text>")
            return
        self.case_notes.append(text)
        print(f"Saved note {len(self.case_notes)}.")

    def do_notes(self, arg: str) -> None:
        if not self.case_notes:
            print("No notes yet.")
            return
        for idx, note in enumerate(self.case_notes, start=1):
            print(f"{idx}. {note}")

    def do_mark(self, arg: str) -> None:
        name = arg.strip()
        if not name:
            print("Usage: mark <name>")
            return
        self.suspects.append(name)
        print(f"Tracked suspect: {name}")

    def do_suspects(self, arg: str) -> None:
        if not self.suspects:
            print("No suspects tracked.")
            return
        for idx, suspect in enumerate(self.suspects, start=1):
            print(f"{idx}. {suspect}")

    def do_hint(self, arg: str) -> None:
        num = arg.strip()
        if num not in {"1", "2", "3", "4"}:
            print("Usage: hint <1-4>")
            return
        print((self.project_root / "hints" / f"hint{num}").read_text(encoding="utf-8"))

    def do_accuse(self, arg: str) -> None:
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
        if arg.strip():
            super().do_help(arg)
            return
        print(
            "Commands:\n"
            "  ls [path]         list files\n"
            "  cd <path>         change directory\n"
            "  pwd               show current location\n"
            "  cat <path>        print a file\n"
            "  head <path> [n]   show first lines\n"
            "  tail <path> [n]   show last lines\n"
            "  grep <text> [p]   search files\n"
            "  open <surface>    jump to incident/people/logs/interviews/locations/registry/memberships/hints/design\n"
            "  hint <1-4>        read a hint\n"
            "  mark <name>       track a suspect\n"
            "  suspects          list tracked suspects\n"
            "  note <text>       save a note\n"
            "  notes             list notes\n"
            "  accuse <name>     submit final answer\n"
            "  quit              exit the game\n"
        )

    def do_quit(self, arg: str) -> bool:
        print("Case file closed.")
        return True

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
