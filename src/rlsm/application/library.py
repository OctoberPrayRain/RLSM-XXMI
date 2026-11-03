from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rlsm.domain.mod import ModEntry, ModState, enabled_directory_name, is_disabled_name


_METADATA_NAMES = {".rlsm.json", ".jasm_modconfig.json"}
_PREVIEW_PREFIXES = (".rlsm-preview", "preview", "cover", "thumbnail")
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


@dataclass(frozen=True, slots=True)
class LibrarySnapshot:
    root: Path
    entries: tuple[ModEntry, ...]
    warnings: tuple[str, ...]
    scanned_at: datetime

    @property
    def enabled_count(self) -> int:
        return sum(entry.is_enabled for entry in self.entries)


class ModLibrary:
    def scan(self, mods_root: Path) -> LibrarySnapshot:
        root = mods_root.expanduser().resolve(strict=False)
        warnings: list[str] = []
        entries: list[ModEntry] = []

        if not root.is_dir():
            warnings.append(f"Mods 目录不存在：{root}")
            return LibrarySnapshot(root, (), tuple(warnings), datetime.now(UTC))

        def on_error(error: OSError) -> None:
            warnings.append(f"无法读取目录：{error.filename or root}（{error.strerror}）")

        for current, directory_names, file_names in os.walk(root, topdown=True, onerror=on_error):
            directory_names.sort(key=str.casefold)
            current_path = Path(current)

            if current_path == root:
                continue

            if not self._looks_like_mod_root(file_names):
                continue

            directory_names.clear()
            relative_path = current_path.relative_to(root)
            directory_name = current_path.name
            state = ModState.DISABLED if is_disabled_name(directory_name) else ModState.ENABLED
            preview_path = self._find_preview(current_path, file_names)

            entries.append(
                ModEntry(
                    path=current_path,
                    relative_path=relative_path,
                    group_path=relative_path.parent,
                    directory_name=directory_name,
                    display_name=self._display_name(current_path, directory_name, warnings),
                    state=state,
                    preview_path=preview_path,
                )
            )

        entries.sort(key=lambda entry: (entry.group_path.as_posix().casefold(), entry.display_name.casefold()))
        return LibrarySnapshot(root, tuple(entries), tuple(warnings), datetime.now(UTC))

    @staticmethod
    def _display_name(directory: Path, directory_name: str, warnings: list[str]) -> str:
        fallback = enabled_directory_name(directory_name)
        metadata_path = directory / ".rlsm.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError:
            return fallback
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            warnings.append(f"读取 Mod 名称失败：{metadata_path}（{error}）")
            return fallback
        if isinstance(metadata, dict):
            name = metadata.get("displayName")
            if isinstance(name, str) and name.strip():
                return name.strip()
        return fallback

    @staticmethod
    def _looks_like_mod_root(file_names: list[str]) -> bool:
        folded_names = {name.casefold() for name in file_names}
        if folded_names & _METADATA_NAMES:
            return True
        return any(Path(name).suffix.casefold() == ".ini" for name in file_names)

    @staticmethod
    def _find_preview(directory: Path, file_names: list[str]) -> Path | None:
        images = [
            directory / name
            for name in file_names
            if Path(name).suffix.casefold() in _IMAGE_EXTENSIONS
        ]
        if not images:
            return None

        images.sort(
            key=lambda path: (
                not path.stem.casefold().startswith(_PREVIEW_PREFIXES),
                path.name.casefold(),
            )
        )
        return images[0]

