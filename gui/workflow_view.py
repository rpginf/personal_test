from __future__ import annotations
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QToolButton,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from blocks.base import Block
from gui.theme import THEMES, FONT_SIZES, DEFAULT_THEME, DEFAULT_FONT_SIZE


# ─────────────────────────────────────────────────────────────────────────────
# BlockCard widget
# ─────────────────────────────────────────────────────────────────────────────
class BlockCard(QFrame):
    """Visual card representing one block in the workflow sequence."""
    clicked = pyqtSignal(object)             # block
    delete_requested = pyqtSignal(object)    # block
    move_up_requested = pyqtSignal(object)   # block
    move_down_requested = pyqtSignal(object) # block

    _STATUS_COLORS = {
        'idle':    '#45475a',
        'running': '#ffb86c',
        'success': '#50fa7b',
        'error':   '#ff5555',
    }
    _STATUS_ICONS = {
        'idle':    '●',
        'running': '⟳',
        'success': '✓',
        'error':   '✗',
    }

    def __init__(self, block: Block, c: dict = None, fs: int = 13, parent=None):
        super().__init__(parent)
        self.block = block
        self._c = c if c is not None else THEMES[DEFAULT_THEME]
        self._fs = fs
        self._selected = False
        self._build()
        self._refresh()

    def _build(self) -> None:
        self.setMinimumHeight(62)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName('BlockCard')

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 3, 8, 3)
        outer.setSpacing(0)

        # ── card body ────────────────────────────────────────────────────
        self.card = QFrame()
        self.card.setObjectName('CardBody')
        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 6, 0)
        card_layout.setSpacing(0)

        # colour stripe
        self.stripe = QFrame()
        self.stripe.setFixedWidth(5)
        self.stripe.setStyleSheet(
            f"background:{self.block.COLOR}; border-radius:3px 0 0 3px;"
        )
        card_layout.addWidget(self.stripe)
        card_layout.addSpacing(8)

        # icon
        self.icon_lbl = QLabel(self.block.ICON)
        self.icon_lbl.setFixedWidth(26)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.icon_lbl)
        card_layout.addSpacing(6)

        # text area
        text_w = QWidget()
        text_l = QVBoxLayout(text_w)
        text_l.setContentsMargins(0, 6, 0, 6)
        text_l.setSpacing(1)
        self.name_lbl = QLabel(self.block.NAME)
        self.summary_lbl = QLabel()
        self.summary_lbl.setWordWrap(True)
        text_l.addWidget(self.name_lbl)
        text_l.addWidget(self.summary_lbl)
        card_layout.addWidget(text_w, 1)

        # right buttons
        btn_w = QWidget()
        btn_l = QVBoxLayout(btn_w)
        btn_l.setContentsMargins(0, 2, 0, 2)
        btn_l.setSpacing(0)
        btn_l.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.status_lbl = QLabel('●')
        self.status_lbl.setFixedWidth(18)
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._up_btn = QToolButton()
        self._up_btn.setText('▲')
        self._up_btn.setFixedSize(18, 14)
        self._up_btn.clicked.connect(lambda: self.move_up_requested.emit(self.block))

        self._dn_btn = QToolButton()
        self._dn_btn.setText('▼')
        self._dn_btn.setFixedSize(18, 14)
        self._dn_btn.clicked.connect(lambda: self.move_down_requested.emit(self.block))

        self._del_btn = QToolButton()
        self._del_btn.setText('✕')
        self._del_btn.setFixedSize(18, 18)
        self._del_btn.clicked.connect(lambda: self.delete_requested.emit(self.block))

        btn_l.addWidget(self.status_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        btn_l.addStretch()
        btn_l.addWidget(self._up_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        btn_l.addWidget(self._dn_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        btn_l.addStretch()
        btn_l.addWidget(self._del_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        card_layout.addWidget(btn_w)

        outer.addWidget(self.card)
        self.refresh_theme(self._c, self._fs)

    def refresh_theme(self, c: dict, fs: int) -> None:
        self._c = c
        self._fs = fs
        sm = max(fs - 2, 9)
        xs = max(fs - 4, 7)
        self.icon_lbl.setStyleSheet(f"font-size:{fs + 5}px; color:{self.block.COLOR};")
        self.name_lbl.setStyleSheet(
            f"font-size:{fs}px; font-weight:bold; color:{c['text']};"
        )
        self.summary_lbl.setStyleSheet(f"font-size:{sm}px; color:{c['muted']};")
        self._up_btn.setStyleSheet(f"border:none; color:{c['muted']}; font-size:{xs}px;")
        self._dn_btn.setStyleSheet(f"border:none; color:{c['muted']}; font-size:{xs}px;")
        self._del_btn.setStyleSheet(
            f"border:none; color:{c['muted']}; font-weight:bold; font-size:{sm}px;"
        )
        self._update_card_style()
        self._refresh()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._update_card_style()

    def _update_card_style(self) -> None:
        c = self._c
        if self._selected:
            self.card.setStyleSheet(f"""
                QFrame#CardBody {{
                    background:{c['surface2']};
                    border:2px solid {c['accent']};
                    border-radius:6px;
                }}
            """)
        else:
            self.card.setStyleSheet(f"""
                QFrame#CardBody {{
                    background:{c['toolbar_bg']};
                    border:1px solid {c['overlay']};
                    border-radius:6px;
                }}
                QFrame#CardBody:hover {{ background:{c['surface']}; border-color:{c['overlay2']}; }}
            """)

    def _refresh(self) -> None:
        summary = self.block.get_summary() or self.block.DESCRIPTION
        self.summary_lbl.setText(summary)
        color = self._STATUS_COLORS.get(self.block.status, '#45475a')
        icon = self._STATUS_ICONS.get(self.block.status, '●')
        self.status_lbl.setText(icon)
        self.status_lbl.setStyleSheet(
            f"color:{color}; font-size:{max(self._fs - 2, 9)}px; font-weight:bold;"
        )

    def update_display(self) -> None:
        self._refresh()
        self._update_card_style()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.block)
        super().mousePressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# WorkflowView
# ─────────────────────────────────────────────────────────────────────────────
class WorkflowView(QWidget):
    """Central panel showing the workflow as an ordered list of BlockCards."""
    block_selected = pyqtSignal(object)   # Block | None
    workflow_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: List[BlockCard] = []
        self._selected_id: Optional[str] = None
        self._c = THEMES[DEFAULT_THEME]
        self._fs = FONT_SIZES[DEFAULT_FONT_SIZE]
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── header ──────────────────────────────────────────────────────
        self._hdr = QWidget()
        hdr_layout = QHBoxLayout(self._hdr)
        hdr_layout.setContentsMargins(12, 8, 12, 8)
        self.wf_name_lbl = QLabel("Workflow")
        self.count_lbl = QLabel("0 blocks")
        hdr_layout.addWidget(self.wf_name_lbl)
        hdr_layout.addSpacing(10)
        hdr_layout.addWidget(self.count_lbl)
        hdr_layout.addStretch()
        layout.addWidget(self._hdr)

        # ── scroll area ──────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self.canvas = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas)
        self.canvas_layout.setContentsMargins(0, 8, 0, 8)
        self.canvas_layout.setSpacing(2)

        # add-block button (always at bottom)
        self.add_btn = QPushButton("＋  Add Block")
        self.canvas_layout.addStretch()
        self.canvas_layout.addWidget(self.add_btn)
        self._scroll.setWidget(self.canvas)
        layout.addWidget(self._scroll)

    def refresh_theme(self, c: dict, fs: int) -> None:
        self._c = c
        self._fs = fs
        sm = max(fs - 2, 9)
        self._hdr.setStyleSheet(f"background:{c['surface2']};")
        self.wf_name_lbl.setStyleSheet(
            f"color:{c['text']}; font-weight:bold; font-size:{fs + 1}px;"
        )
        self.count_lbl.setStyleSheet(f"color:{c['muted']}; font-size:{sm}px;")
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background:{c['bg']}; border:none; }}"
        )
        self.canvas.setStyleSheet(f"background:{c['bg']};")
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background:{c['surface']}; color:{c['accent']};
                border:2px dashed {c['overlay2']}; border-radius:8px;
                padding:12px; font-size:{fs}px; font-weight:bold;
                margin:8px 20px;
            }}
            QPushButton:hover {{ background:{c['surface2']}; border-color:{c['accent']}; }}
        """)
        for card in self.cards:
            card.refresh_theme(c, fs)

    # ── public API ────────────────────────────────────────────────────────
    def set_workflow_name(self, name: str) -> None:
        self.wf_name_lbl.setText(name)

    def add_card(self, block: Block) -> None:
        card = BlockCard(block, self._c, self._fs)
        card.clicked.connect(self._on_click)
        card.delete_requested.connect(self._on_delete)
        card.move_up_requested.connect(self._on_move_up)
        card.move_down_requested.connect(self._on_move_down)
        self.cards.append(card)
        # insert before stretch + add_btn
        pos = self.canvas_layout.count() - 2
        self.canvas_layout.insertWidget(pos, card)
        self._update_count()

    def remove_card_by_id(self, block_id: str) -> None:
        for card in self.cards[:]:
            if card.block.id == block_id:
                self.cards.remove(card)
                self.canvas_layout.removeWidget(card)
                card.deleteLater()
                break
        if self._selected_id == block_id:
            self._selected_id = None
            self.block_selected.emit(None)
        self._update_count()
        self.workflow_changed.emit()

    def clear(self) -> None:
        for card in self.cards[:]:
            self.canvas_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        self._selected_id = None
        self._update_count()

    def update_card(self, block: Block) -> None:
        for card in self.cards:
            if card.block.id == block.id:
                card.update_display()
                break

    def update_all_cards(self) -> None:
        for card in self.cards:
            card.update_display()

    def select_card(self, block_id: str) -> None:
        self._selected_id = block_id
        for card in self.cards:
            card.set_selected(card.block.id == block_id)

    def get_blocks_in_order(self) -> List[Block]:
        return [c.block for c in self.cards]

    # ── internal slots ───────────────────────────────────────────────────
    def _on_click(self, block: Block) -> None:
        self.select_card(block.id)
        self.block_selected.emit(block)

    def _on_delete(self, block: Block) -> None:
        self.remove_card_by_id(block.id)

    def _on_move_up(self, block: Block) -> None:
        idx = next((i for i, c in enumerate(self.cards) if c.block.id == block.id), -1)
        if idx > 0:
            self.cards.insert(idx - 1, self.cards.pop(idx))
            self._rebuild()
            self.workflow_changed.emit()

    def _on_move_down(self, block: Block) -> None:
        idx = next((i for i, c in enumerate(self.cards) if c.block.id == block.id), -1)
        if 0 <= idx < len(self.cards) - 1:
            self.cards.insert(idx + 1, self.cards.pop(idx))
            self._rebuild()
            self.workflow_changed.emit()

    def _rebuild(self) -> None:
        for card in self.cards:
            self.canvas_layout.removeWidget(card)
        for i, card in enumerate(self.cards):
            self.canvas_layout.insertWidget(i, card)

    def _update_count(self) -> None:
        n = len(self.cards)
        self.count_lbl.setText(f"{n} block{'s' if n != 1 else ''}")
