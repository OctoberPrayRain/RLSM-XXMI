from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GameInstallation:
    game_key: str
    root_path: Path
    executable_path: Path


@dataclass(frozen=True, slots=True)
class WineEnvironment:
    prefix_path: Path | None
    runner_name: str | None
    runner_path: Path | None
    architecture: str | None
    environment: tuple[tuple[str, str], ...]
    issues: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.prefix_path is not None and self.runner_name is not None and not self.issues


@dataclass(frozen=True, slots=True)
class LaunchProfile:
    provider: str
    profile_id: str
    name: str
    slug: str
    runner: str
    config_path: Path
    executable_path: Path | None
    working_directory: Path | None
    arguments: str
    importer_hint: str | None
    wine: WineEnvironment

    @property
    def launch_uri(self) -> str:
        return f"lutris:rungameid/{self.profile_id}"


@dataclass(frozen=True, slots=True)
class GameBinding:
    importer_key: str
    module_path: Path | None
    launch_profile_id: str | None
    wine_prefix_override: Path | None = None
