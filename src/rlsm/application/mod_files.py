from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

from rlsm.domain.mod import ModEntry


MANAGED_PREVIEW_STEM = ".rlsm-preview"
PREVIEW_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


class ModFileError(RuntimeError):
    pass


class ModFileManager:
    def __init__(self, trash_command: str | None = None) -> None:
        self._trash_command = trash_command or shutil.which("gio")

    def set_preview(self, entry: ModEntry, source: Path) -> Path:
        mod_path = entry.path.resolve(strict=False)
        source_path = source.expanduser().resolve(strict=False)
        if not mod_path.is_dir():
            raise ModFileError(f"Mod 目录不存在：{mod_path}")
        if not source_path.is_file() or source_path.suffix.casefold() not in PREVIEW_EXTENSIONS:
            raise ModFileError("请选择 PNG、JPEG、WebP、BMP 或 GIF 图片")

        suffix = source_path.suffix.casefold()
        target = mod_path / f"{MANAGED_PREVIEW_STEM}{suffix}"
        temporary = mod_path / f"{MANAGED_PREVIEW_STEM}-{uuid.uuid4().hex}{suffix}"
        try:
            if source_path != target:
                shutil.copyfile(source_path, temporary)
                os.replace(temporary, target)
            for previous in mod_path.glob(f"{MANAGED_PREVIEW_STEM}.*"):
                if previous != target:
                    previous.unlink()
        except OSError as error:
            temporary.unlink(missing_ok=True)
            raise ModFileError(f"保存预览图失败：{error}") from error
        return target

    def move_to_trash(self, entry: ModEntry, mods_root: Path) -> None:
        root = mods_root.expanduser().resolve(strict=False)
        target = entry.path.expanduser().resolve(strict=False)
        if not target.is_dir():
            raise ModFileError(f"Mod 目录不存在：{target}")
        if target == root or root not in target.parents:
            raise ModFileError("无法删除 Mods 目录以外的内容")
        if self._trash_command is None:
            raise ModFileError("系统未安装 gio，无法使用回收站")

        result = subprocess.run(
            (self._trash_command, "trash", str(target)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stdout.strip() or f"退出状态 {result.returncode}"
            raise ModFileError(f"移入回收站失败：{detail}")
