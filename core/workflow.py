from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from blocks.base import Block
from blocks.registry import create_block_from_dict


class Workflow:
    """An ordered sequence of automation blocks that can be saved/loaded as JSON."""

    def __init__(self, name: str = 'New Workflow'):
        self.name: str = name
        self.description: str = ''
        self.blocks: List[Block] = []
        self.metadata: Dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # Block operations
    # ------------------------------------------------------------------ #
    def add_block(self, block: Block, index: Optional[int] = None) -> None:
        if index is not None:
            self.blocks.insert(index, block)
        else:
            self.blocks.append(block)

    def remove_block(self, block_id: str) -> bool:
        for i, b in enumerate(self.blocks):
            if b.id == block_id:
                self.blocks.pop(i)
                return True
        return False

    def move_block(self, block_id: str, new_index: int) -> bool:
        for i, b in enumerate(self.blocks):
            if b.id == block_id:
                self.blocks.pop(i)
                self.blocks.insert(new_index, b)
                return True
        return False

    def get_block(self, block_id: str) -> Optional[Block]:
        return next((b for b in self.blocks if b.id == block_id), None)

    def reset_statuses(self) -> None:
        for b in self.blocks:
            b.status = 'idle'
            b.error_message = ''
            b.output = None

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'blocks': [b.to_dict() for b in self.blocks],
            'metadata': self.metadata,
        }

    def save(self, filepath: str) -> None:
        Path(filepath).write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding='utf-8'
        )

    @classmethod
    def load(cls, filepath: str) -> 'Workflow':
        data = json.loads(Path(filepath).read_text(encoding='utf-8'))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        wf = cls(data.get('name', 'Workflow'))
        wf.description = data.get('description', '')
        wf.metadata = data.get('metadata', {})
        for bd in data.get('blocks', []):
            try:
                wf.blocks.append(create_block_from_dict(bd))
            except Exception as exc:
                print(f"[Workflow.load] Skipping block {bd.get('type')!r}: {exc}")
        return wf

    def __len__(self) -> int:
        return len(self.blocks)

    def __repr__(self) -> str:
        return f"Workflow({self.name!r}, {len(self.blocks)} blocks)"
