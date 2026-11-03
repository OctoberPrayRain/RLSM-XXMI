from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from rlsm.domain.game import GameDefinition, ImporterDefinition


GENSHIN_IMPACT = GameDefinition(
    key="genshin-impact",
    display_name="原神",
    executable_names=("GenshinImpact.exe", "YuanShen.exe"),
    process_names=("GenshinImpact.exe", "YuanShen.exe"),
    directory_names=("Genshin Impact Game",),
    directory_markers=("GenshinImpact_Data",),
    lutris_slugs=("genshin-impact",),
)

HONKAI_STAR_RAIL = GameDefinition(
    key="honkai-star-rail",
    display_name="崩坏：星穹铁道",
    executable_names=("StarRail.exe",),
    process_names=("StarRail.exe",),
    directory_names=("Star Rail Games",),
    directory_markers=("StarRail_Data",),
    lutris_slugs=("honkai-star-rail",),
)

WUTHERING_WAVES = GameDefinition(
    key="wuthering-waves",
    display_name="鸣潮",
    executable_names=("Wuthering Waves.exe",),
    process_names=("Client-Win64-Shipping.exe",),
    process_relative_paths=("Client/Binaries/Win64",),
    directory_names=("Wuthering Waves Game",),
    directory_markers=("Client", "Data"),
    lutris_slugs=("wuthering-waves",),
)

ZENLESS_ZONE_ZERO = GameDefinition(
    key="zenless-zone-zero",
    display_name="绝区零",
    executable_names=("ZenlessZoneZero.exe", "ZenlessZoneZeroBeta.exe"),
    process_names=("ZenlessZoneZero.exe", "ZenlessZoneZeroBeta.exe"),
    directory_names=("ZenlessZoneZero Game",),
    directory_markers=("ZenlessZoneZero_Data",),
    lutris_slugs=("zenless-zone-zero", "zenless-zone-zero-xxmi"),
)

HONKAI_IMPACT = GameDefinition(
    key="honkai-impact",
    display_name="崩坏3",
    executable_names=("BH3.exe",),
    process_names=("BH3.exe",),
    directory_names=("Honkai Impact 3rd game",),
    directory_markers=("BH3_Data",),
    lutris_slugs=("honkai-impact-3rd",),
)

ARKNIGHTS_ENDFIELD = GameDefinition(
    key="arknights-endfield",
    display_name="明日方舟：终末地",
    executable_names=("Endfield.exe",),
    process_names=("Endfield.exe",),
    directory_names=("EndField Game",),
    directory_markers=("Endfield_Data",),
    lutris_slugs=("arknightsendfield", "arknights-endfield"),
    launcher_directory_names=("GRYPHLINK", "Hypergryph Launcher"),
    launcher_file_names=("Launcher.exe",),
)

GIMI = ImporterDefinition(
    key="gimi",
    importer_name="GIMI",
    game=GENSHIN_IMPACT,
    module_directory_names=("GIMI",),
    injection_mode="HOOK",
)

SRMI = ImporterDefinition(
    key="srmi",
    importer_name="SRMI",
    game=HONKAI_STAR_RAIL,
    module_directory_names=("SRMI",),
    injection_mode="HOOK",
)

WWMI = ImporterDefinition(
    key="wwmi",
    importer_name="WWMI",
    game=WUTHERING_WAVES,
    module_directory_names=("WWMI",),
    injection_mode="DIRECT",
    d3d11_arguments=("-dx11",),
)

ZZMI = ImporterDefinition(
    key="zzmi",
    importer_name="ZZMI",
    game=ZENLESS_ZONE_ZERO,
    module_directory_names=("ZZMI",),
    injection_mode="HOOK",
)

HIMI = ImporterDefinition(
    key="himi",
    importer_name="HIMI",
    game=HONKAI_IMPACT,
    module_directory_names=("HIMI",),
    injection_mode="HOOK",
)

EFMI = ImporterDefinition(
    key="efmi",
    importer_name="EFMI",
    game=ARKNIGHTS_ENDFIELD,
    module_directory_names=("EFMI",),
    injection_mode="DIRECT",
    d3d11_arguments=("-force-d3d11",),
)

IMPORTER_DEFINITIONS: tuple[ImporterDefinition, ...] = (ZZMI, EFMI, WWMI, GIMI, SRMI, HIMI)
IMPORTERS_BY_KEY = {definition.key: definition for definition in IMPORTER_DEFINITIONS}
IMPORTERS_BY_NAME = {definition.importer_name.casefold(): definition for definition in IMPORTER_DEFINITIONS}
GAME_DEFINITIONS: tuple[GameDefinition, ...] = tuple(
    definition.game for definition in IMPORTER_DEFINITIONS
)


@dataclass(frozen=True, slots=True)
class XXMIInstallation:
    root_path: Path
    config_path: Path | None
    configured_importers: tuple[str, ...]
    enabled_importers: tuple[str, ...]
    installed_importers: tuple[str, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EnvironmentInspection:
    importer: ImporterDefinition
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


def get_importer_definition(key_or_name: str) -> ImporterDefinition | None:
    lookup = key_or_name.casefold()
    return IMPORTERS_BY_KEY.get(lookup) or IMPORTERS_BY_NAME.get(lookup)


def discover_xxmi_installations(
    search_roots: tuple[Path, ...] | None = None,
) -> tuple[XXMIInstallation, ...]:
    roots = search_roots or (Path.home() / "Games",)
    candidates: set[Path] = set()

    for search_root in roots:
        root = search_root.expanduser().resolve(strict=False)
        if not root.is_dir():
            continue
        if _looks_like_xxmi_root(root):
            candidates.add(root)
        try:
            children = tuple(child for child in root.iterdir() if child.is_dir())
        except OSError:
            continue
        candidates.update(child for child in children if _looks_like_xxmi_root(child))

    installations = (inspect_xxmi_installation(path) for path in candidates)
    return tuple(sorted(installations, key=lambda item: str(item.root_path).casefold()))


def inspect_xxmi_installation(selected_path: Path) -> XXMIInstallation:
    selected = selected_path.expanduser().resolve(strict=False)
    root = _resolve_xxmi_root(selected) or selected
    config_path = root / "XXMI Launcher Config.json"
    issues: list[str] = []
    configured_importers: tuple[str, ...] = ()
    enabled_importers: tuple[str, ...] = ()

    if config_path.is_file():
        try:
            with config_path.open("r", encoding="utf-8-sig") as config_file:
                config = json.load(config_file)
            importer_config = config.get("Importers", {})
            configured_importers = _known_importer_names(importer_config.keys())
            launcher_config = config.get("Launcher", {})
            enabled_importers = _known_importer_names(launcher_config.get("enabled_importers", ()))
        except (OSError, UnicodeError, json.JSONDecodeError, AttributeError) as error:
            issues.append(f"无法读取 XXMI Launcher Config.json：{error}")
    else:
        config_path = None
        issues.append("没有找到 XXMI Launcher Config.json")

    installed_importers = tuple(
        definition.importer_name
        for definition in IMPORTER_DEFINITIONS
        if _resolve_module_path(root, definition) is not None
    )
    return XXMIInstallation(
        root_path=root,
        config_path=config_path,
        configured_importers=configured_importers,
        enabled_importers=enabled_importers,
        installed_importers=installed_importers,
        issues=tuple(issues),
    )


def discover_module_path(
    importer: ImporterDefinition = ZZMI,
    search_roots: tuple[Path, ...] | None = None,
) -> Path | None:
    roots = search_roots or (Path.home() / "Games",)
    for installation in discover_xxmi_installations(roots):
        module_path = _resolve_module_path(installation.root_path, importer)
        if module_path is not None:
            return module_path

    for root in roots:
        selected = root.expanduser().resolve(strict=False)
        module_path = _resolve_module_path(selected, importer)
        if module_path is not None:
            return module_path
        if not selected.is_dir():
            continue
        try:
            candidates = sorted(
                (child for child in selected.iterdir() if child.is_dir()),
                key=lambda path: path.name.casefold(),
            )
        except OSError:
            continue
        for candidate in candidates:
            module_path = _resolve_module_path(candidate, importer)
            if module_path is not None:
                return module_path
    return None


def inspect_environment(
    selected_path: Path,
    importer: ImporterDefinition = ZZMI,
) -> EnvironmentInspection:
    selected = selected_path.expanduser().resolve(strict=False)
    issues: list[str] = []
    module_path = _resolve_module_path(selected, importer)

    if module_path is None:
        issues.append(f"没有找到 {importer.importer_name} 模块目录")
        return EnvironmentInspection(importer, selected, None, None, None, None, False, False, tuple(issues))

    mods_path = module_path / importer.mods_directory_name
    config_path = module_path / importer.config_file_name
    user_config_path = module_path / importer.user_config_file_name

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
            value.strip().strip('"').casefold() == importer.mods_directory_name.casefold()
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
        importer=importer,
        selected_path=selected,
        module_path=module_path,
        mods_path=mods_path,
        config_path=config_path,
        user_config_path=user_config_path,
        has_recursive_mods=has_recursive_mods,
        excludes_disabled=excludes_disabled,
        issues=tuple(issues),
    )


def _resolve_xxmi_root(selected: Path) -> Path | None:
    if _looks_like_xxmi_root(selected):
        return selected
    if selected.parent != selected and _looks_like_xxmi_root(selected.parent):
        return selected.parent
    return None


def _looks_like_xxmi_root(path: Path) -> bool:
    return (
        (path / "XXMI Launcher Config.json").is_file()
        or (path / "Resources" / "Bin" / "XXMI Launcher.exe").is_file()
    )


def _resolve_module_path(selected: Path, importer: ImporterDefinition) -> Path | None:
    if not selected.is_dir():
        return None

    if (selected / importer.config_file_name).is_file():
        return selected

    try:
        children = {child.name.casefold(): child for child in selected.iterdir() if child.is_dir()}
    except OSError:
        return None
    for directory_name in importer.module_directory_names:
        child = children.get(directory_name.casefold())
        if child is not None and (child / importer.config_file_name).is_file():
            return child
    return None


def _known_importer_names(values: object) -> tuple[str, ...]:
    if not hasattr(values, "__iter__") or isinstance(values, (str, bytes)):
        return ()
    names: list[str] = []
    for value in values:
        definition = get_importer_definition(str(value))
        if definition is not None and definition.importer_name not in names:
            names.append(definition.importer_name)
    return tuple(names)


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
