from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ServiceEvent:
    message: str
    tag: str | None = None


@dataclass
class BackupRestoreResult:
    events: list[ServiceEvent] = field(default_factory=list)
    restored_count: int = 0
    had_errors: bool = False


@dataclass
class DlssUpdateResult:
    events: list[ServiceEvent] = field(default_factory=list)
    found_dlss_files: dict[str, list[Path]] = field(default_factory=dict)
    updated_count: int = 0
    had_errors: bool = False
