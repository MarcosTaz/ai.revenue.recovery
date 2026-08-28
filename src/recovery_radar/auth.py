from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal["ADMIN", "ANALYST", "REVIEWER"]


@dataclass(frozen=True, slots=True)
class Principal:
    """Identity already authenticated by an external boundary.

    Recovery Radar does not accept caller-selected workspace IDs on business
    methods; workspace scope is taken from this principal.
    """

    workspace_id: str
    actor_id: str
    role: Role
