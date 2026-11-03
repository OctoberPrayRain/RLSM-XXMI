from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


DISABLED_PREFIX = "DISABLED_"
ALTERNATE_DISABLED_PREFIX = "DISABLED"


class ModState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


def is_disabled_name(name: str) -> bool:
    return name.casefold().startswith(ALTERNATE_DISABLED_PREFIX.casefold())


def enabled_directory_name(name: str) -> str:
    folded = name.casefold()
    if folded.startswith(DISABLED_PREFIX.casefold()):
        return name[len(DISABLED_PREFIX) :]
    if folded.startswith(ALTERNATE_DISABLED_PREFIX.casefold()):
        return name[len(ALTERNATE_DISABLED_PREFIX) :].lstrip("_")
    return name


def disabled_directory_name(name: str) -> str:
    enabled_name = enabled_directory_name(name)
    return f"{DISABLED_PREFIX}{enabled_name}"


@dataclass(frozen=True, slots=True)
class ModEntry:
    path: Path
    relative_path: Path
    group_path: Path
    directory_name: str
    display_name: str
    state: ModState
    preview_path: Path | None = None

    @property
    def is_enabled(self) -> bool:
        return self.state is ModState.ENABLED

    @property
    def canonical_relative_path(self) -> Path:
        return self.group_path / enabled_directory_name(self.directory_name)

