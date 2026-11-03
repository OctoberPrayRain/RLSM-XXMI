from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameDefinition:
    key: str
    display_name: str
    importer_name: str
    module_directory_names: tuple[str, ...]
    process_names: tuple[str, ...]
    mods_directory_name: str = "Mods"
    config_file_name: str = "d3dx.ini"
    user_config_file_name: str = "d3dx_user.ini"
    reload_key: str = "F10"

