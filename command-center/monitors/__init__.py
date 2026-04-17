"""Service monitor registry for the DuberyMNL Command Center.

Each monitor module under this package exposes a `check() -> ServiceStatus`
function. The `SERVICES` list defines display order + cheap/expensive flag.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Callable, Literal, Optional

State = Literal["active", "degraded", "offline", "not_wired"]


@dataclass
class ServiceStatus:
    name: str
    state: State
    last_checked: str  # ISO 8601 UTC
    message: str = ""
    log_source: Optional[str] = None  # file path or callable reference

    @classmethod
    def now(
        cls,
        name: str,
        state: State,
        message: str = "",
        log_source: Optional[str] = None,
    ) -> "ServiceStatus":
        return cls(
            name=name,
            state=state,
            last_checked=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            message=message,
            log_source=log_source,
        )

    def to_dict(self) -> dict:
        return asdict(self)


# Registry populated by monitors/registry.py at app startup to avoid circular
# imports. Each entry: (service_name, check_callable, expensive_flag).
SERVICES: list[tuple[str, Callable[[], ServiceStatus], bool]] = []


def register(name: str, check_fn: Callable[[], ServiceStatus], expensive: bool = False) -> None:
    """Register a service check. Idempotent -- replaces existing entry by name.
    Mutates SERVICES in place so imports that aliased it still see updates.
    """
    for i, (n, _fn, _exp) in enumerate(SERVICES):
        if n == name:
            SERVICES[i] = (name, check_fn, expensive)
            return
    SERVICES.append((name, check_fn, expensive))


def service_names_in_order() -> list[str]:
    """Canonical display order, matches the Monitoring tab row order."""
    return [
        "chatbot",
        "tunnel",
        "worker_fallback",
        "meta_ads",
        "story_rotation",
        "rasclaw_tg",
        "chatbot_tg",
        "crm_sheet",
        "inventory",
    ]
