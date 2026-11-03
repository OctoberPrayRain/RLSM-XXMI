from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameDefinition:
    key: str
    display_name: str
    executable_names: tuple[str, ...]
    process_names: tuple[str, ...]
    directory_names: tuple[str, ...]
    directory_markers: tuple[str, ...]
    lutris_slugs: tuple[str, ...] = ()
    process_relative_paths: tuple[str, ...] = ()
    launcher_directory_names: tuple[str, ...] = ()
    launcher_file_names: tuple[str, ...] = ()
    reload_key: str = "F10"


@dataclass(frozen=True, slots=True)
class ImporterDefinition:
    key: str
    importer_name: str
    game: GameDefinition
    module_directory_names: tuple[str, ...]
    injection_mode: str
    d3d11_arguments: tuple[str, ...] = ()
    mods_directory_name: str = "Mods"
    config_file_name: str = "d3dx.ini"
    user_config_file_name: str = "d3dx_user.ini"

    @property
    def display_name(self) -> str:
        return self.game.display_name

    @property
    def process_names(self) -> tuple[str, ...]:
        return self.game.process_names

    @property
    def reload_key(self) -> str:
        return self.game.reload_key
