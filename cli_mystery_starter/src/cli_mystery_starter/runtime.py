from __future__ import annotations

import cmd
import json
import shlex
from pathlib import Path


from . import contract, verifier
from .clues import ClueRegistry, load_clues
from .dialogue import load_dialogue
from .events import EventBus
from .scenes import SceneRouter, load_scenes
from .session import SessionStore
from .solutions import load_solutions, parse_accusation


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
        self.topics_asked: set[str] = set(state.get("topics_asked", []))
        self.events = EventBus()
        clues, _clue_errors = load_clues(self.project_root)
        self.clue_registry = ClueRegistry(clues)
        self.clue_registry.attach(self.events, initial=state.get("discovered_clues", []))
        self.solutions, _solution_errors = load_solutions(self.project_root)
        self.npcs, _dialogue_errors = load_dialogue(self.project_root)
        scenes, start_scene, _scene_errors = load_scenes(self.project_root)
        self.scene_router = SceneRouter(scenes, start_scene)
        scene_initial = {
            "current_scene": state.get("current_scene") or start_scene,
            "files_read": list(self.visited),
            "suspects": list(self.suspects),
            "topics": list(state.get("topics_asked", [])),
        }
        self.scene_router.attach(self.events, initial=scene_initial)
        self.scene_router.seed_clues(set(self.clue_registry.discovered))
        self._wire_default_subscribers()
        self.prompt = self._prompt()

    def _wire_default_subscribers(self) -> None:
        """Subclasses or extensions can override to register more handlers."""
        self.events.subscribe("scene:advanced", self._on_scene_advanced)

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
            discovered_clues=self.clue_registry.discovered,
            topics_asked=self.topics_asked,
            current_scene=self.scene_router.current,
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
        rel = format_project_path(path, self.project_root)
        self.visited.add(rel)
        self.events.emit("file:read", {"path": rel})
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
        self.events.emit("note:added", {"text": text, "index": len(self.case_notes)})
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
        self.events.emit("suspect:marked", {"name": name})
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
        self.events.emit("hint:read", {"number": int(num)})
        print((self.project_root / "hints" / f"hint{num}").read_text(encoding="utf-8"))

    def do_accuse(self, arg: str) -> None:
        """accuse <name>                                 (legacy: culprit only)
        accuse culprit=<x> motive=<y> weapon=<z>      (multi-field, when solutions.json declares fields)
        """
        raw = arg.strip()
        if not raw:
            print("Usage: accuse <name>  OR  accuse culprit=<x> motive=<y> ...")
            return

        if self.solutions is not None:
            guesses = parse_accusation(raw)
            correct, ending = self.solutions.evaluate(guesses)
            payload = {
                "guess": raw,
                "correct": ending is not None,
                "fields_correct": sorted(correct),
                "ending": ending.id if ending else None,
            }
            self.events.emit("accuse:attempt", payload)
            if ending is None:
                missed = [k for k in self.solutions.fields if k not in correct]
                print("That accusation does not unlock any ending.")
                if correct:
                    print(f"You got right: {', '.join(sorted(correct))}")
                if missed:
                    print(f"Still wrong or unanswered: {', '.join(missed)}")
                return
            if ending.text:
                print(ending.text)
            print(f"You completed {self.title}: {ending.id}")
            return

        # Legacy fallback: single-field MD5 check against `encoded`.
        correct_legacy = check_answer(self.project_root, raw)
        self.events.emit("accuse:attempt", {"guess": raw, "correct": correct_legacy})
        if correct_legacy:
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
            "  clues             list discovered clues (if the case declares any)\n"
            "  ask <npc> [about <topic>]   probe an NPC (if the case declares any)\n"
            "  scene             show the current scene/beat (if declared)\n"
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

    def do_scene(self, arg: str) -> None:
        """scene   show the current scene and its advancement criteria"""
        if not self.scene_router.has_scenes:
            print("This case does not declare a scene graph.")
            return
        print(self.scene_router.describe_current())

    def _on_scene_advanced(self, payload: dict) -> None:
        narration = payload.get("narration", "")
        target = payload.get("to", "?")
        print(f"\n— scene: {target} —")
        if narration:
            print(narration)
        self._persist()

    def do_ask(self, arg: str) -> None:
        """ask <npc>                       list available topics for an NPC
        ask <npc> about <topic-id>     hear what they have to say on that topic
        """
        if not self.npcs:
            print("No NPCs declared for this case (add files under game/dialogue/).")
            return
        raw = arg.strip()
        if not raw:
            print("Usage: ask <npc> [about <topic>]")
            print("Available NPCs: " + ", ".join(sorted(self.npcs)))
            return

        try:
            tokens = shlex.split(raw)
        except ValueError:
            tokens = raw.split()

        npc_key = tokens[0].lower()
        npc = self.npcs.get(npc_key)
        if npc is None:
            print(f"Unknown NPC `{tokens[0]}`. Try: " + ", ".join(sorted(self.npcs)))
            return

        # `ask <npc>` → greet + list available topics
        if len(tokens) == 1:
            if npc.greeting:
                print(f"{npc.name}: {npc.greeting}")
            available = [t for t in npc.topics
                         if t.is_available(self.clue_registry.discovered)]
            if not available:
                print("(No topics are available yet — keep investigating.)")
                return
            print("Topics you can ask about:")
            for topic in available:
                print(f"  - {topic.id}: {topic.summary}")
            return

        # `ask <npc> about <topic>`
        if len(tokens) < 3 or tokens[1].lower() != "about":
            print("Usage: ask <npc> about <topic>")
            return

        topic_id = tokens[2]
        topic = npc.topic(topic_id)
        if topic is None:
            print(f"{npc.name} does not have anything to say about `{topic_id}`.")
            return
        if not topic.is_available(self.clue_registry.discovered):
            print(f"{npc.name} deflects — you do not have enough evidence to "
                  f"press them on `{topic_id}` yet.")
            return

        print(f"{npc.name}: {topic.response}")
        self.topics_asked.add(f"{npc.slug}:{topic.id}")
        self.events.emit("dialogue:asked",
                         {"npc": npc.slug, "topic": topic.id})

        if topic.reveals_clue:
            valid_ids = {c.id for c in self.clue_registry.clues}
            if topic.reveals_clue in valid_ids and (
                topic.reveals_clue not in self.clue_registry.discovered
            ):
                self.clue_registry.discovered.add(topic.reveals_clue)
                self.events.emit("clue:revealed", {"id": topic.reveals_clue,
                                                    "via": f"ask:{npc.slug}"})
                print(f"  (new clue discovered: {topic.reveals_clue})")
        self._persist()

    def do_clues(self, arg: str) -> None:
        """clues   list clues you have discovered (requires game/clues.json)"""
        if not self.clue_registry.clues:
            print("This case does not declare a clues registry.")
            return
        found = self.clue_registry.discovered_clues()
        if not found:
            print(f"Discovered 0 / {len(self.clue_registry.clues)} clues. "
                  "Keep reading evidence files.")
            return
        print(f"Discovered {len(found)} / {len(self.clue_registry.clues)} clues:")
        for clue in found:
            tags = f"  [{', '.join(clue.tags)}]" if clue.tags else ""
            print(f"  - {clue.id}: {clue.title}{tags}")

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
        if self.clue_registry.clues:
            found = self.clue_registry.discovered_clues()
            print(f"\nClues: {len(found)}/{len(self.clue_registry.clues)} discovered")

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
