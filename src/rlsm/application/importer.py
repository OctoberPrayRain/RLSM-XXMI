from __future__ import annotations

import json
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from rlsm.domain.mod import disabled_directory_name, enabled_directory_name


_METADATA_NAMES = {".rlsm.json", ".jasm_modconfig.json"}
_MOD_FILE_EXTENSIONS = {".buf", ".dds", ".ib"}
_ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar"}
_COMPONENT_MARKERS = (
    "texcoord",
    "position",
    "lightmap",
    "diffuse",
    "normalmap",
    "normal",
    "texture",
    "blend",
    "stocking",
    "jacket",
    "dress",
    "weapon",
    "body",
    "head",
    "hair",
    "face",
    "hand",
    "torso",
    "shoes",
    "legs",
)
_GENERIC_PREFIXES = {
    "body",
    "buffer",
    "default",
    "diffuse",
    "head",
    "mesh",
    "mod",
    "normal",
    "object",
    "texture",
}
_UI_WORDS = ("interface", "menu", "portrait", "reticle", "splash", "ui", "hud")
_WEAPON_WORDS = ("weapon", "weapons", "w-engine", "wengine")
_FOLDER_SUFFIX_WORDS = ("costume", "mod", "outfit", "skin")
_SAFE_NAME = re.compile(r"[^\w .()+\-\[\]]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class ModClassification:
    category: str
    reason: str


@dataclass(frozen=True, slots=True)
class ImportedMod:
    source_path: Path
    target_path: Path
    category: str


@dataclass(frozen=True, slots=True)
class ImportResult:
    imported: tuple[ImportedMod, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OrganizeResult:
    moved: int
    unchanged: int
    warnings: tuple[str, ...] = ()


class ModImportError(RuntimeError):
    pass


class ModClassifier:
    def classify(self, mod_root: Path) -> ModClassification:
        metadata_category = self._metadata_category(mod_root)
        if metadata_category:
            return ModClassification(_safe_component(metadata_category), "Mod 元数据")

        searchable_names: list[str] = [mod_root.name]
        mod_file_stems: list[str] = []
        try:
            for path in mod_root.rglob("*"):
                if not path.is_file():
                    continue
                searchable_names.append(path.name)
                if path.suffix.casefold() in _MOD_FILE_EXTENSIONS:
                    mod_file_stems.append(path.stem)
        except OSError:
            pass

        folded_names = " ".join(searchable_names).casefold()
        if _contains_word(folded_names, _WEAPON_WORDS):
            return ModClassification("武器", "文件名称包含武器标记")
        if _contains_word(folded_names, _UI_WORDS):
            return ModClassification("界面", "文件名称包含界面标记")

        candidates = [_mod_file_prefix(stem) for stem in mod_file_stems]
        usable = [candidate for candidate in candidates if candidate]
        if usable:
            counts = Counter(candidate.casefold() for candidate in usable)
            winner = max(
                counts,
                key=lambda value: (counts[value], len(value)),
            )
            display_value = next(candidate for candidate in usable if candidate.casefold() == winner)
            return ModClassification(_safe_component(display_value), "模型文件名称前缀")

        folder_category = _folder_name_category(mod_root.name)
        if folder_category:
            return ModClassification(_safe_component(folder_category), "Mod 目录名称")
        return ModClassification("未分类", "没有足够的分类依据")

    @staticmethod
    def _metadata_category(mod_root: Path) -> str | None:
        try:
            metadata_paths = (
                path for path in mod_root.iterdir()
                if path.is_file() and path.name.casefold() in _METADATA_NAMES
            )
            for metadata_path in metadata_paths:
                try:
                    with metadata_path.open("r", encoding="utf-8-sig") as metadata_file:
                        value = json.load(metadata_file)
                except (OSError, UnicodeError, json.JSONDecodeError):
                    continue
                category = _find_metadata_category(value)
                if category:
                    return category
        except OSError:
            return None
        return None


class ModImporter:
    def __init__(self, classifier: ModClassifier | None = None) -> None:
        self.classifier = classifier or ModClassifier()

    def import_source(self, source: Path, mods_root: Path) -> ImportResult:
        source_path = source.expanduser().resolve(strict=False)
        destination_root = mods_root.expanduser().resolve(strict=False)
        if not source_path.exists():
            raise ModImportError(f"导入来源不存在：{source_path}")
        if not destination_root.is_dir():
            raise ModImportError(f"Mods 目录不存在：{destination_root}")
        if source_path == destination_root or destination_root in source_path.parents:
            raise ModImportError("不能从当前 Mods 目录内部重复导入")

        with tempfile.TemporaryDirectory(prefix="rlsm-import-") as temporary_name:
            temporary_path = Path(temporary_name)
            scan_root = self._prepare_source(source_path, temporary_path)
            roots = _find_mod_roots(scan_root)
            if not roots:
                raise ModImportError("没有找到包含 INI 配置的 Mod 目录")

            imported: list[ImportedMod] = []
            warnings: list[str] = []
            for root in roots:
                classification = self.classifier.classify(root)
                category_path = destination_root / classification.category
                category_path.mkdir(parents=True, exist_ok=True)
                source_name = enabled_directory_name(root.name) or source_path.stem or "Imported Mod"
                directory_name = disabled_directory_name(_safe_component(source_name))
                target_path = _unique_path(category_path / directory_name)
                try:
                    shutil.copytree(root, target_path)
                    _write_metadata(target_path, classification, source_path.name)
                except OSError as error:
                    if target_path.exists():
                        shutil.rmtree(target_path, ignore_errors=True)
                    warnings.append(f"导入 {root.name} 失败：{error}")
                    continue
                imported.append(ImportedMod(root, target_path, classification.category))

        if not imported:
            detail = "\n".join(warnings) or "没有 Mod 被导入"
            raise ModImportError(detail)
        return ImportResult(tuple(imported), tuple(warnings))

    def organize_existing(self, mods_root: Path, mod_paths: tuple[Path, ...]) -> OrganizeResult:
        destination_root = mods_root.expanduser().resolve(strict=False)
        moved = 0
        unchanged = 0
        warnings: list[str] = []

        for path in mod_paths:
            mod_path = path.expanduser().resolve(strict=False)
            try:
                relative = mod_path.relative_to(destination_root)
            except ValueError:
                warnings.append(f"跳过 Mods 目录以外的路径：{mod_path}")
                continue

            if len(relative.parts) > 1 and relative.parts[0] != "未分类":
                unchanged += 1
                continue

            classification = self.classifier.classify(mod_path)
            if classification.category == "未分类":
                unchanged += 1
                continue

            category_path = destination_root / classification.category
            category_path.mkdir(parents=True, exist_ok=True)
            target_path = _unique_path(category_path / mod_path.name)
            try:
                mod_path.rename(target_path)
                _write_metadata(target_path, classification, "现有 Mod")
            except OSError as error:
                warnings.append(f"分类 {mod_path.name} 失败：{error}")
                continue

            _remove_empty_parents(mod_path.parent, destination_root)
            moved += 1

        return OrganizeResult(moved, unchanged, tuple(warnings))

    @staticmethod
    def _prepare_source(source_path: Path, temporary_path: Path) -> Path:
        if source_path.is_dir():
            _reject_symlinks(source_path)
            return source_path
        if source_path.suffix.casefold() not in _ARCHIVE_EXTENSIONS:
            raise ModImportError("支持目录、ZIP、7z 和 RAR 导入")

        extracted_path = temporary_path / "extracted"
        extracted_path.mkdir()
        if source_path.suffix.casefold() == ".zip":
            _extract_zip(source_path, extracted_path)
        else:
            _extract_with_bsdtar(source_path, extracted_path)
        _reject_symlinks(extracted_path)
        return extracted_path


def _extract_zip(archive_path: Path, destination: Path) -> None:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                member_path = PurePosixPath(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ModImportError(f"压缩包包含无效路径：{member.filename}")
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ModImportError(f"压缩包包含符号链接：{member.filename}")
            archive.extractall(destination)
    except (OSError, zipfile.BadZipFile) as error:
        raise ModImportError(f"无法解压 ZIP：{error}") from error


def _extract_with_bsdtar(archive_path: Path, destination: Path) -> None:
    command = shutil.which("bsdtar")
    if command is None:
        raise ModImportError("系统没有安装 bsdtar，无法解压 7z 或 RAR")
    result = subprocess.run(
        (command, "-xf", str(archive_path), "-C", str(destination)),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stdout.strip() or f"退出状态 {result.returncode}"
        raise ModImportError(f"无法解压 {archive_path.suffix}：{detail}")


def _find_mod_roots(search_root: Path) -> tuple[Path, ...]:
    candidates: list[Path] = []
    directories = [search_root]
    try:
        directories.extend(path for path in search_root.rglob("*") if path.is_dir())
    except OSError as error:
        raise ModImportError(f"无法读取导入内容：{error}") from error

    for directory in sorted(directories, key=lambda path: len(path.parts)):
        if any(parent in candidates for parent in directory.parents):
            continue
        try:
            files = tuple(path for path in directory.iterdir() if path.is_file())
        except OSError:
            continue
        names = {path.name.casefold() for path in files}
        if names & _METADATA_NAMES or any(path.suffix.casefold() == ".ini" for path in files):
            candidates.append(directory)
    return tuple(candidates)


def _reject_symlinks(root: Path) -> None:
    if root.is_symlink():
        raise ModImportError(f"导入来源不能是符号链接：{root}")
    try:
        link = next((path for path in root.rglob("*") if path.is_symlink()), None)
    except OSError as error:
        raise ModImportError(f"无法检查导入来源：{error}") from error
    if link is not None:
        raise ModImportError(f"导入内容包含符号链接：{link}")


def _write_metadata(
    target_path: Path,
    classification: ModClassification,
    source_name: str,
) -> None:
    metadata_path = target_path / ".rlsm.json"
    if metadata_path.exists():
        return
    metadata = {
        "id": str(uuid.uuid4()),
        "displayName": enabled_directory_name(target_path.name),
        "category": classification.category,
        "classificationReason": classification.reason,
        "sourceName": source_name,
        "importedAt": datetime.now(UTC).isoformat(),
    }
    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, ensure_ascii=False, indent=2)
        metadata_file.write("\n")


def _find_metadata_category(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    folded = {str(key).casefold(): item for key, item in value.items()}
    for key in ("category", "character", "charactername", "moddableobject", "group"):
        item = folded.get(key)
        if isinstance(item, str) and item.strip():
            return item.strip()
        if isinstance(item, dict):
            for name_key in ("displayname", "internalname", "name"):
                nested = {str(name).casefold(): child for name, child in item.items()}
                name_value = nested.get(name_key)
                if isinstance(name_value, str) and name_value.strip():
                    return name_value.strip()
    return None


def _mod_file_prefix(stem: str) -> str | None:
    cleaned = re.sub(r"^(?:disabled[_ -]*)+", "", stem, flags=re.IGNORECASE).strip(" _-.[]()")
    folded = cleaned.casefold()
    for marker in _COMPONENT_MARKERS:
        index = folded.find(marker)
        if index < 2:
            continue
        candidate = cleaned[:index].strip(" _-.[]()")
        if _usable_prefix(candidate):
            return candidate
    return None


def _folder_name_category(name: str) -> str | None:
    cleaned = enabled_directory_name(name).strip(" _-.[]()")
    match = re.match(
        rf"^(.+?)[ _\-.]+(?:{'|'.join(_FOLDER_SUFFIX_WORDS)})(?:[ _\-.].*)?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    candidate = match.group(1).strip(" _-.[]()")
    return candidate if _usable_prefix(candidate) else None


def _usable_prefix(value: str) -> bool:
    compact = re.sub(r"[^\w]+", "", value, flags=re.UNICODE)
    if len(compact) < 3 or compact.casefold() in _GENERIC_PREFIXES:
        return False
    if re.fullmatch(r"[0-9a-fA-F]{8,}", compact):
        return False
    return any(character.isalpha() for character in compact)


def _contains_word(text: str, words: tuple[str, ...]) -> bool:
    return any(re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", text) for word in words)


def _safe_component(value: str) -> str:
    cleaned = _SAFE_NAME.sub("_", value).strip(" ._")
    if cleaned in {"", ".", ".."}:
        return "未分类"
    return cleaned[:120]


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    enabled_name = enabled_directory_name(path.name)
    disabled = path.name.casefold().startswith("disabled")
    for index in range(2, 10_000):
        name = f"{enabled_name} ({index})"
        candidate = path.with_name(disabled_directory_name(name) if disabled else name)
        if not candidate.exists():
            return candidate
    raise ModImportError(f"无法为同名 Mod 分配目录：{path.name}")


def _remove_empty_parents(path: Path, stop: Path) -> None:
    current = path
    while current != stop and stop in current.parents:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent
