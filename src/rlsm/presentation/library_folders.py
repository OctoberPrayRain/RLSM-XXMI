from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QSettings

from rlsm.domain.mod import ModEntry


RESERVED_FOLDER_NAMES = {"全部 Mod", "未整理"}
RESERVED_FOLDER_NAMES_FOLDED = {name.casefold() for name in RESERVED_FOLDER_NAMES}


class LibraryFolderError(RuntimeError):
    pass


class LibraryFolders:
    def __init__(self, settings: QSettings) -> None:
        self._settings = settings
        self._importer_key = ""
        self._folders: list[str] = []
        self._assignments: dict[str, str] = {}

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._folders)

    def load(self, importer_key: str) -> None:
        self._importer_key = importer_key
        self._folders = []
        self._assignments = {}

        raw_value = str(self._settings.value(self._setting_key(), "") or "")
        if not raw_value:
            return
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            return
        if not isinstance(value, dict):
            return

        folder_values = value.get("folders", ())
        if isinstance(folder_values, list):
            for item in folder_values:
                name = self._normalize_name(str(item))
                if name and not self._contains_name(name) and not self._is_reserved(name):
                    self._folders.append(name)

        assignment_values = value.get("assignments", {})
        if isinstance(assignment_values, dict):
            for key, item in assignment_values.items():
                folder = self._matching_name(str(item))
                if folder is not None:
                    self._assignments[str(key)] = folder

    def create(self, value: str) -> str:
        name = self._validate_new_name(value)
        self._folders.append(name)
        self._save()
        return name

    def rename(self, current_name: str, value: str) -> str:
        current = self._matching_name(current_name)
        if current is None:
            raise LibraryFolderError("找不到需要重命名的文件夹")

        name = self._normalize_name(value)
        if not name:
            raise LibraryFolderError("文件夹名称不能为空")
        if self._is_reserved(name):
            raise LibraryFolderError("该名称由 RLSM 保留")
        duplicate = self._matching_name(name)
        if duplicate is not None and duplicate != current:
            raise LibraryFolderError("已经存在同名文件夹")

        index = self._folders.index(current)
        self._folders[index] = name
        self._assignments = {
            key: name if folder == current else folder
            for key, folder in self._assignments.items()
        }
        self._save()
        return name

    def delete(self, value: str) -> None:
        name = self._matching_name(value)
        if name is None:
            raise LibraryFolderError("找不到需要删除的文件夹")
        self._folders.remove(name)
        self._assignments = {
            key: folder for key, folder in self._assignments.items() if folder != name
        }
        self._save()

    def assign(self, entry: ModEntry, value: str) -> str:
        name = ""
        if value:
            matching = self._matching_name(value)
            if matching is None:
                raise LibraryFolderError("所选文件夹不存在")
            name = matching

        key = self.key_for(entry)
        if name:
            self._assignments[key] = name
        else:
            self._assignments.pop(key, None)
        self._save()
        return name

    def remove_key(self, key: str) -> None:
        if self._assignments.pop(key, None) is not None:
            self._save()

    def folder_for(self, entry: ModEntry) -> str:
        folder = self._assignments.get(self.key_for(entry), "")
        return folder if folder in self._folders else ""

    def folder_map(self, entries: tuple[ModEntry, ...]) -> dict[Path, str]:
        return {entry.path: self.folder_for(entry) for entry in entries}

    @staticmethod
    def key_for(entry: ModEntry) -> str:
        metadata_path = entry.path / ".rlsm.json"
        try:
            with metadata_path.open("r", encoding="utf-8-sig") as metadata_file:
                metadata = json.load(metadata_file)
            identifier = metadata.get("id") if isinstance(metadata, dict) else None
            if identifier:
                return f"id:{identifier}"
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
        return f"path:{entry.canonical_relative_path.as_posix()}"

    def _validate_new_name(self, value: str) -> str:
        name = self._normalize_name(value)
        if not name:
            raise LibraryFolderError("文件夹名称不能为空")
        if self._is_reserved(name):
            raise LibraryFolderError("该名称由 RLSM 保留")
        if self._contains_name(name):
            raise LibraryFolderError("已经存在同名文件夹")
        return name

    def _matching_name(self, value: str) -> str | None:
        folded = value.casefold()
        return next((name for name in self._folders if name.casefold() == folded), None)

    def _contains_name(self, value: str) -> bool:
        return self._matching_name(value) is not None

    @staticmethod
    def _is_reserved(value: str) -> bool:
        return value.casefold() in RESERVED_FOLDER_NAMES_FOLDED

    @staticmethod
    def _normalize_name(value: str) -> str:
        return " ".join(value.split())[:64]

    def _setting_key(self) -> str:
        return f"games/{self._importer_key}/libraryFolders"

    def _save(self) -> None:
        value = {
            "folders": self._folders,
            "assignments": self._assignments,
        }
        self._settings.setValue(
            self._setting_key(),
            json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        )
