from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Param:
    """Definition of a configurable block parameter."""
    name: str
    label: str
    # types: text, multiline, int, float, bool, choice, file, folder, file_save, password
    type: str = 'text'
    default: Any = None
    options: List[str] = field(default_factory=list)
    required: bool = False
    placeholder: str = ''
    tooltip: str = ''


class Block:
    """Base class for every automation block."""
    CATEGORY: str = 'General'
    NAME: str = 'Block'
    DESCRIPTION: str = ''
    ICON: str = '▶'
    COLOR: str = '#6272a4'
    PARAMS: List[Param] = []

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.id: str = str(uuid.uuid4())
        self.params: Dict[str, Any] = {p.name: p.default for p in self.PARAMS}
        if params:
            self.params.update(params)
        self.status: str = 'idle'   # idle | running | success | error
        self.error_message: str = ''
        self.output: Any = None

    # ------------------------------------------------------------------ #
    # Subclasses must override this
    # ------------------------------------------------------------------ #
    def execute(self, context: Dict[str, Any]) -> None:
        raise NotImplementedError(f"Block '{self.NAME}' has no execute() implementation")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def get_summary(self) -> str:
        parts = []
        for p in self.PARAMS[:3]:
            val = self.params.get(p.name)
            if val is not None and str(val).strip():
                parts.append(str(val)[:60])
        return '  ▸  '.join(parts) if parts else self.DESCRIPTION

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.__class__.__name__,
            'id': self.id,
            'params': dict(self.params),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        b = cls(data.get('params', {}))
        b.id = data.get('id', str(uuid.uuid4()))
        return b

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.params})'
