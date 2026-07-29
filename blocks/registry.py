from __future__ import annotations
from typing import Dict, List, Type
from .base import Block

_REGISTRY: Dict[str, Type[Block]] = {}


def register(block_class: Type[Block]) -> Type[Block]:
    """Decorator: register a block class by its class name."""
    _REGISTRY[block_class.__name__] = block_class
    return block_class


def get_block_class(name: str) -> Type[Block]:
    return _REGISTRY[name]


def all_block_classes() -> List[Type[Block]]:
    return list(_REGISTRY.values())


def get_all_categories() -> List[str]:
    seen: List[str] = []
    for cls in _REGISTRY.values():
        if cls.CATEGORY not in seen:
            seen.append(cls.CATEGORY)
    return sorted(seen)


def get_blocks_for_category(category: str) -> List[Type[Block]]:
    return [cls for cls in _REGISTRY.values() if cls.CATEGORY == category]


def create_block_from_dict(data: Dict) -> Block:
    cls = _REGISTRY.get(data['type'])
    if cls is None:
        raise ValueError(f"Unknown block type: {data['type']!r}")
    return cls.from_dict(data)


def load_all_blocks() -> None:
    """Import all block modules so @register decorators run."""
    from . import file_blocks, excel_blocks, web_blocks, app_blocks, ai_blocks, cv_blocks  # noqa: F401
