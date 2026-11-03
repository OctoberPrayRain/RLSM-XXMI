from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from rlsm.domain.game import GameDefinition


ZZMI = GameDefinition(
    key="zzmi",
    display_name="绝区零",
    importer_name="ZZMI",
    module_directory_names=("ZZMI",),
    process_names=("ZenlessZoneZero.exe",),
)

GAME_DEFINITIONS: tuple[GameDefinition, ...] = (ZZMI,)


@dataclass(frozen=True, slots=True)
class EnvironmentInspection:
    game: GameDefinition
    selected_path: Path
    module_path: Path | None
    mods_path: Path | None
    config_path: Path | None
    user_config_path: Path | None
    has_recursive_mods: bool
    excludes_disabled: bool
    issues: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.issues


def inspect_environment(selected_path: Path, game: GameDefinition = ZZMI) -> EnvironmentInspection:
    selected = selected_path.expanduser().resolve(strict=False)
    issues: list[str] = []
    module_path = _resolve_module_path(selected, game)

    if module_path is None:
        issues.append(f"没有找到 {game.importer_name} 模块目录")
        return EnvironmentInspection(game, selected, None, None, None, None, False, False, tuple(issues))

    mods_path = module_path / game.mods_directory_name
    config_path = module_path / game.config_file_name
    user_config_path = module_path / game.user_config_file_name

    if not mods_path.is_dir():
        issues.append(f"Mods 目录不存在：{mods_path}")
    elif not os.access(mods_path, os.R_OK | os.W_OK | os.X_OK):
        issues.append(f"Mods 目录缺少读写权限：{mods_path}")

    has_recursive_mods = False
    excludes_disabled = False
    if not config_path.is_file():
        issues.append(f"XXMI 配置不存在：{config_path}")
    else:
        entries = _read_ini_entries(config_path)
        has_recursive_mods = any(
            value.strip().strip('"').casefold() == game.mods_directory_name.casefold()
            for value in entries.get("include_recursive", ())
        )
        excludes_disabled = any(
            value.strip().strip('"').casefold().startswith("disabled")
            for value in entries.get("exclude_recursive", ())
        )
        if not has_recursive_mods:
            issues.append("d3dx.ini 没有递归载入 Mods 目录")
        if not excludes_disabled:
            issues.append("d3dx.ini 没有排除 DISABLED* 目录")

    return EnvironmentInspection(
        game=game,
        selected_path=selected,
        module_path=module_path,
        mods_path=mods_path,
        config_path=config_path,
        user_config_path=user_config_path,
        has_recursive_mods=has_recursive_mods,
        excludes_disabled=excludes_disabled,
        issues=tuple(issues),
    )


def _resolve_module_path(selected: Path, game: GameDefinition) -> Path | None:
    if not selected.is_dir():
        return None

    if (selected / game.config_file_name).is_file():
        return selected

    try:
        children = {child.name.casefold(): child for child in selected.iterdir() if child.is_dir()}
    except OSError:
        return None
    for directory_name in game.module_directory_names:
        child = children.get(directory_name.casefold())
        if child is not None and (child / game.config_file_name).is_file():
            return child
    return None


def _read_ini_entries(config_path: Path) -> dict[str, tuple[str, ...]]:
    values: dict[str, list[str]] = {}
    with config_path.open("r", encoding="utf-8-sig", errors="replace") as config_file:
        for raw_line in config_file:
            line = raw_line.split(";", 1)[0].strip()
            if not line or line.startswith("[") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values.setdefault(key.strip().casefold(), []).append(value.strip())
    return {key: tuple(items) for key, items in values.items()}
