from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from blocks.registry import get_all_categories, get_blocks_for_category
from gui.theme import THEMES, FONT_SIZES, DEFAULT_THEME, DEFAULT_FONT_SIZE


CATEGORY_COLORS = {
    'File':             '#50fa7b',
    'Excel':            '#1d9e5e',
    'Web':              '#ff79c6',
    'App Automation':   '#bd93f9',
    'AI':               '#f1fa8c',
    'Computer Vision':  '#ffb86c',
    'Control':          '#8be9fd',
}


class BlockPalette(QWidget):
    """Left-hand panel listing all available block types by category."""
    block_double_clicked = pyqtSignal(type)   # emits the block class

    def __init__(self, parent=None):
        super().__init__(parent)
        self._c = THEMES[DEFAULT_THEME]
        self._fs = FONT_SIZES[DEFAULT_FONT_SIZE]
        self._setup_ui()
        self._populate()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── header ──────────────────────────────────────────────────────
        self._hdr = QWidget()
        hl = QVBoxLayout(self._hdr)
        hl.setContentsMargins(10, 10, 10, 6)
        self._title_lbl = QLabel("Block Library")
        self._title_lbl.setStyleSheet("font-weight:bold;")
        hl.addWidget(self._title_lbl)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search blocks…")
        self.search.textChanged.connect(self._filter)
        hl.addWidget(self.search)
        layout.addWidget(self._hdr)

        # ── tree ────────────────────────────────────────────────────────
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree)

        self._hint_lbl = QLabel("Double-click a block to add it")
        layout.addWidget(self._hint_lbl)

    def refresh_theme(self, c: dict, fs: int) -> None:
        self._c = c
        self._fs = fs
        sm = max(fs - 2, 9)
        self._hdr.setStyleSheet(f"background:{c['surface2']};")
        self._title_lbl.setStyleSheet(
            f"color:{c['text']}; font-weight:bold; font-size:{fs}px;"
        )
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background:{c['bg']}; color:{c['text']};
                border:none; font-size:{fs}px;
            }}
            QTreeWidget::item {{ padding:3px 4px; border-radius:3px; }}
            QTreeWidget::item:hover {{ background:{c['surface2']}; }}
            QTreeWidget::item:selected {{ background:{c['overlay2']}; }}
        """)
        self._hint_lbl.setStyleSheet(
            f"color:{c['overlay2']}; font-size:{sm}px; padding:4px 10px;"
        )

    def _populate(self) -> None:
        self.tree.clear()
        for category in get_all_categories():
            color = CATEGORY_COLORS.get(category, '#6272a4')
            cat_item = QTreeWidgetItem([f"  {category}"])
            cat_item.setData(0, Qt.ItemDataRole.UserRole, None)
            cat_item.setForeground(0, QColor(color))
            f = QFont()
            f.setBold(True)
            f.setPointSize(10)
            cat_item.setFont(0, f)
            for cls in sorted(get_blocks_for_category(category), key=lambda c: c.NAME):
                child = QTreeWidgetItem([f"  {cls.ICON}  {cls.NAME}"])
                child.setData(0, Qt.ItemDataRole.UserRole, cls)
                child.setToolTip(0, cls.DESCRIPTION)
                cat_item.addChild(child)
            self.tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)

    def _on_double_click(self, item: QTreeWidgetItem, _col: int) -> None:
        cls = item.data(0, Qt.ItemDataRole.UserRole)
        if cls is not None:
            self.block_double_clicked.emit(cls)

    def _filter(self, text: str) -> None:
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            cat = self.tree.topLevelItem(i)
            any_visible = False
            for j in range(cat.childCount()):
                child = cat.child(j)
                cls = child.data(0, Qt.ItemDataRole.UserRole)
                visible = (
                    not text
                    or text in child.text(0).lower()
                    or (cls and text in cls.DESCRIPTION.lower())
                )
                child.setHidden(not visible)
                if visible:
                    any_visible = True
            cat.setHidden(not any_visible)
