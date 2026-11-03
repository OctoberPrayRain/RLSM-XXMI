from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Iterable

from rlsm.domain.mod import ModEntry, disabled_directory_name, enabled_directory_name


@dataclass(frozen=True, slots=True)
class RenameStep:
    source: Path
    target: Path


@dataclass(frozen=True, slots=True)
class ToggleResult:
    completed_steps: tuple[RenameStep, ...]

    @property
    def changed(self) -> bool:
        return bool(self.completed_steps)


class ToggleOperationError(RuntimeError):
    def __init__(self, message: str, rollback_errors: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.rollback_errors = rollback_errors


class ModToggleEngine:
    def __init__(self) -> None:
        self._operation_lock = RLock()

    def set_enabled(self, mod: ModEntry, enabled: bool) -> ToggleResult:
        step = self._state_change_step(mod, enabled)
        return self.execute(() if step is None else (step,))

    def enable_exclusively(self, target: ModEntry, siblings: Iterable[ModEntry]) -> ToggleResult:
        steps: list[RenameStep] = []
        for sibling in siblings:
            if sibling.path == target.path or not sibling.is_enabled:
                continue
            step = self._state_change_step(sibling, False)
            if step is not None:
                steps.append(step)

        target_step = self._state_change_step(target, True)
        if target_step is not None:
            steps.append(target_step)
        return self.execute(steps)

    def execute(self, steps: Iterable[RenameStep]) -> ToggleResult:
        planned_steps = tuple(steps)
        with self._operation_lock:
            self._validate(planned_steps)
            completed: list[RenameStep] = []
            try:
                for step in planned_steps:
                    step.source.rename(step.target)
                    completed.append(step)
            except OSError as error:
                rollback_errors = self._rollback(completed)
                message = f"目录切换失败：{error.filename or ''} {error.strerror or error}"
                raise ToggleOperationError(message.strip(), rollback_errors) from error

        return ToggleResult(tuple(completed))

    @staticmethod
    def _state_change_step(mod: ModEntry, enabled: bool) -> RenameStep | None:
        if mod.is_enabled is enabled:
            return None

        target_name = (
            enabled_directory_name(mod.directory_name)
            if enabled
            else disabled_directory_name(mod.directory_name)
        )
        if not target_name:
            raise ToggleOperationError(f"Mod 目录名称无效：{mod.path}")
        return RenameStep(mod.path, mod.path.with_name(target_name))

    @staticmethod
    def _validate(steps: tuple[RenameStep, ...]) -> None:
        targets: set[Path] = set()

        for step in steps:
            if step.source.parent != step.target.parent:
                raise ToggleOperationError(f"切换操作只能重命名同一目录中的 Mod：{step.source}")
            if not step.source.is_dir():
                raise ToggleOperationError(f"Mod 目录不存在：{step.source}")
            if step.target in targets:
                raise ToggleOperationError(f"多个 Mod 将使用同一目录名称：{step.target}")
            if step.target.exists():
                raise ToggleOperationError(f"目标目录已经存在：{step.target}")
            targets.add(step.target)

    @staticmethod
    def _rollback(completed: list[RenameStep]) -> tuple[str, ...]:
        errors: list[str] = []
        for step in reversed(completed):
            try:
                if step.target.exists() and not step.source.exists():
                    step.target.rename(step.source)
            except OSError as error:
                errors.append(f"恢复 {step.target} 失败：{error.strerror or error}")
        return tuple(errors)

