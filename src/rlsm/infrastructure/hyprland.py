from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rlsm.domain.game import GameDefinition


_ADDRESS = re.compile(r"0x[0-9a-fA-F]+")


@dataclass(frozen=True, slots=True)
class HyprlandWindow:
    address: str
    pid: int
    class_name: str
    title: str


@dataclass(frozen=True, slots=True)
class ReloadResult:
    sent: bool
    message: str
    window: HyprlandWindow | None = None


class HyprlandIntegration:
    def __init__(self, command: str | None = None) -> None:
        self.command = command or shutil.which("hyprctl") or "/usr/bin/hyprctl"

    @property
    def available(self) -> bool:
        return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")) and Path(self.command).is_file()

    def find_game_window(self, game: GameDefinition) -> HyprlandWindow | None:
        windows = self._clients()
        needles = _game_needles(game)
        matches: list[tuple[int, HyprlandWindow]] = []

        for item in windows:
            address = str(item.get("address") or "")
            if _ADDRESS.fullmatch(address) is None:
                continue
            pid = _integer(item.get("pid"))
            class_name = str(item.get("class") or item.get("initialClass") or "")
            title = str(item.get("title") or item.get("initialTitle") or "")
            fields = (
                class_name,
                str(item.get("initialClass") or ""),
                title,
                str(item.get("initialTitle") or ""),
            )
            score = _match_score(fields, needles)
            process_fields = _process_fields(pid)
            score = max(score, _match_score(process_fields, needles, base=70))
            if score <= 0:
                continue
            if bool(item.get("mapped", True)):
                score += 5
            if bool(item.get("visible", True)):
                score += 5
            if bool(item.get("acceptsInput", True)):
                score += 5
            matches.append((score, HyprlandWindow(address, pid, class_name, title)))

        if not matches:
            return None
        matches.sort(key=lambda item: (item[0], item[1].pid), reverse=True)
        return matches[0][1]

    def reload_game(self, game: GameDefinition) -> ReloadResult:
        if not self.available:
            return ReloadResult(False, "当前会话无法使用 Hyprland 窗口控制")
        try:
            window = self.find_game_window(game)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            return ReloadResult(False, f"读取 Hyprland 窗口失败：{error}")
        if window is None:
            return ReloadResult(False, f"没有找到 {game.display_name} 游戏窗口")

        key = game.reload_key
        lua = (
            "hl.dispatch(hl.dsp.send_shortcut({ "
            f'mods = "", key = "{key}", window = "address:{window.address}"'
            " }))"
        )
        result = self._run(("eval", lua))
        if result.returncode != 0:
            legacy = self._run(
                ("dispatch", "sendshortcut", f",{key},address:{window.address}")
            )
            if legacy.returncode != 0:
                detail = legacy.stdout.strip() or result.stdout.strip() or "Hyprland 拒绝了快捷键"
                return ReloadResult(False, f"发送 {key} 失败：{detail}", window)
        return ReloadResult(True, f"已经向 {window.title or window.class_name} 发送 {key}", window)

    def _clients(self) -> tuple[dict[str, object], ...]:
        result = self._run(("-j", "clients"))
        if result.returncode != 0:
            detail = result.stdout.strip() or f"退出状态 {result.returncode}"
            raise OSError(detail)
        value = json.loads(result.stdout)
        if not isinstance(value, list):
            raise ValueError("Hyprland 返回了无法识别的窗口列表")
        return tuple(item for item in value if isinstance(item, dict))

    def _run(self, arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        command = (self.command, *arguments)
        try:
            return subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(command, 124, "Hyprland 命令等待超时")


def _game_needles(game: GameDefinition) -> tuple[str, ...]:
    values = (
        game.display_name,
        *game.executable_names,
        *game.process_names,
        *game.directory_names,
        *game.lutris_slugs,
    )
    needles: set[str] = set()
    for value in values:
        normalized = _normalize(value)
        stem = _normalize(Path(value).stem)
        if len(normalized) >= 3:
            needles.add(normalized)
        if len(stem) >= 3:
            needles.add(stem)
    return tuple(sorted(needles, key=len, reverse=True))


def _match_score(fields: tuple[str, ...], needles: tuple[str, ...], base: int = 100) -> int:
    score = 0
    for field in fields:
        normalized = _normalize(field)
        if not normalized:
            continue
        for needle in needles:
            if normalized == needle:
                score = max(score, base + 100 + len(needle))
            elif needle in normalized:
                score = max(score, base + len(needle))
    return score


def _process_fields(pid: int) -> tuple[str, ...]:
    if pid <= 0:
        return ()
    process_root = Path("/proc") / str(pid)
    values: list[str] = []
    try:
        values.append((process_root / "comm").read_text(encoding="utf-8", errors="replace"))
    except OSError:
        pass
    try:
        command_line = (process_root / "cmdline").read_bytes().replace(b"\0", b" ")
        values.append(command_line.decode(errors="replace"))
    except OSError:
        pass
    try:
        values.append(os.readlink(process_root / "exe"))
    except OSError:
        pass
    return tuple(values)


def _normalize(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _integer(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
