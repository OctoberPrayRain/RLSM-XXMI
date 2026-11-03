from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from rlsm.domain.game import ImporterDefinition
from rlsm.domain.runtime import LaunchProfile, WineEnvironment
from rlsm.infrastructure.xxmi import get_importer_definition


_XXMI_ARGUMENT = re.compile(r"(?:^|\s)--xxmi(?:\s+|=)([A-Za-z0-9_-]+)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class LutrisSnapshot:
    profiles: tuple[LaunchProfile, ...]
    issues: tuple[str, ...]


class LutrisIntegration:
    def __init__(self, data_root: Path | None = None, command: str | None = None) -> None:
        xdg_data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        self.data_root = (data_root or xdg_data_home / "lutris").expanduser().resolve(strict=False)
        self.command = command or shutil.which("lutris") or "/usr/bin/lutris"

    def discover_profiles(self) -> LutrisSnapshot:
        database_path = self.data_root / "pga.db"
        if not database_path.is_file():
            return LutrisSnapshot((), (f"没有找到 Lutris 数据库：{database_path}",))

        issues: list[str] = []
        profiles: list[LaunchProfile] = []
        try:
            database_uri = f"{database_path.as_uri()}?mode=ro"
            with sqlite3.connect(database_uri, uri=True) as connection:
                connection.row_factory = sqlite3.Row
                rows = connection.execute(
                    """
                    SELECT id, name, slug, runner, configpath
                    FROM games
                    WHERE installed = 1
                    ORDER BY name COLLATE NOCASE, id
                    """
                ).fetchall()
        except sqlite3.Error as error:
            return LutrisSnapshot((), (f"读取 Lutris 数据库失败：{error}",))

        for row in rows:
            try:
                profiles.append(self._load_profile(row))
            except (OSError, UnicodeError, yaml.YAMLError, ValueError, TypeError) as error:
                issues.append(f"无法读取 Lutris 启动项 {row['name']}：{error}")

        return LutrisSnapshot(tuple(profiles), tuple(issues))

    def profiles_for_importer(
        self,
        importer: ImporterDefinition,
        profiles: tuple[LaunchProfile, ...],
    ) -> tuple[LaunchProfile, ...]:
        ranked = (
            (self.match_score(importer, profile), profile)
            for profile in profiles
        )
        matches = (item for item in ranked if item[0] > 0)
        return tuple(
            profile
            for _, profile in sorted(
                matches,
                key=lambda item: (-item[0], item[1].name.casefold(), item[1].profile_id),
            )
        )

    @staticmethod
    def match_score(importer: ImporterDefinition, profile: LaunchProfile) -> int:
        if profile.importer_hint == importer.key:
            return 1000

        score = 0
        if profile.slug.casefold() in {slug.casefold() for slug in importer.game.lutris_slugs}:
            score += 200

        if profile.executable_path is not None:
            executable_name = profile.executable_path.name.casefold()
            known_names = {
                name.casefold()
                for name in importer.game.executable_names + importer.game.launcher_file_names
            }
            if executable_name in known_names:
                score += 100
        return score

    def launch(self, profile: LaunchProfile) -> None:
        subprocess.Popen(
            (self.command, profile.launch_uri),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _load_profile(self, row: sqlite3.Row) -> LaunchProfile:
        runner = str(row["runner"] or "")
        config_path = self._config_path(str(row["configpath"] or ""))
        config = self._read_yaml(config_path)
        game_config = _mapping(config.get("game"))
        system_config = _mapping(config.get("system"))
        local_runner_config = _mapping(config.get(runner))
        global_runner_config = self._global_runner_config(runner)

        executable_path = _optional_path(game_config.get("exe"))
        working_directory = _optional_path(game_config.get("working_dir"))
        arguments = str(game_config.get("args") or "")
        architecture = _optional_string(game_config.get("arch"))
        prefix_path = _optional_path(game_config.get("prefix"))
        runner_name = _optional_string(local_runner_config.get("version"))
        if runner_name is None:
            runner_name = _optional_string(global_runner_config.get("version"))

        environment_values = _mapping(system_config.get("env"))
        environment = tuple(
            sorted((str(key), str(value)) for key, value in environment_values.items())
        )
        wine_issues: list[str] = []
        if runner == "wine":
            if prefix_path is None:
                wine_issues.append("Lutris 启动项没有指定 Wine 前缀")
            elif not prefix_path.is_dir():
                wine_issues.append(f"Wine 前缀当前不可访问：{prefix_path}")
            if runner_name is None:
                wine_issues.append("Lutris 启动项没有指定 Wine 运行器")

        wine = WineEnvironment(
            prefix_path=prefix_path,
            runner_name=runner_name,
            runner_path=self._resolve_runner_path(runner, runner_name),
            architecture=architecture,
            environment=environment,
            issues=tuple(wine_issues),
        )
        return LaunchProfile(
            provider="lutris",
            profile_id=str(row["id"]),
            name=str(row["name"] or row["slug"] or row["id"]),
            slug=str(row["slug"] or ""),
            runner=runner,
            config_path=config_path,
            executable_path=executable_path,
            working_directory=working_directory,
            arguments=arguments,
            importer_hint=_importer_hint(arguments),
            wine=wine,
        )

    def _config_path(self, config_name: str) -> Path:
        if not config_name:
            raise ValueError("启动项没有配置文件名称")
        relative_path = Path(config_name)
        if relative_path.suffix.casefold() not in {".yml", ".yaml"}:
            relative_path = relative_path.with_suffix(".yml")
        return self.data_root / "games" / relative_path

    def _global_runner_config(self, runner: str) -> Mapping[str, Any]:
        if not runner:
            return {}
        config_path = self.data_root / "runners" / f"{runner}.yml"
        try:
            config = self._read_yaml(config_path)
        except (OSError, UnicodeError, yaml.YAMLError, TypeError):
            return {}
        return _mapping(config.get(runner))

    def _resolve_runner_path(self, runner: str, runner_name: str | None) -> Path | None:
        if runner != "wine" or not runner_name:
            return None
        candidates = (
            self.data_root / "runners" / "wine" / runner_name,
            Path.home() / ".local" / "share" / "Steam" / "compatibilitytools.d" / runner_name,
            Path.home() / ".steam" / "root" / "compatibilitytools.d" / runner_name,
            Path.home() / ".steam" / "steam" / "compatibilitytools.d" / runner_name,
        )
        return next((path for path in candidates if path.is_dir()), None)

    @staticmethod
    def _read_yaml(path: Path) -> Mapping[str, Any]:
        with path.open("r", encoding="utf-8") as config_file:
            return _mapping(yaml.safe_load(config_file) or {})


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _optional_path(value: object) -> Path | None:
    text = _optional_string(value)
    return Path(text).expanduser().resolve(strict=False) if text is not None else None


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _importer_hint(arguments: str) -> str | None:
    match = _XXMI_ARGUMENT.search(arguments)
    if match is None:
        return None
    definition = get_importer_definition(match.group(1))
    return definition.key if definition is not None else None
