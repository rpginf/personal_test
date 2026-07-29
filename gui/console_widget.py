from __future__ import annotations
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt
from gui.theme import THEMES, FONT_SIZES, DEFAULT_THEME, DEFAULT_FONT_SIZE


class ConsoleWidget(QWidget):
    """Read-only log output panel shown at the bottom of the main window."""

    LEVEL_COLORS = {
        'info':    '#cdd6f4',
        'success': '#50fa7b',
        'error':   '#ff5555',
        'warning': '#ffb86c',
        'debug':   '#6c7086',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._c = THEMES[DEFAULT_THEME]
        self._fs = FONT_SIZES[DEFAULT_FONT_SIZE]
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── header ──────────────────────────────────────────────────────
        self._console_hdr = QWidget()
        h_layout = QHBoxLayout(self._console_hdr)
        h_layout.setContentsMargins(10, 4, 8, 4)
        self._console_title = QLabel("Output Console")
        self._console_title.setStyleSheet("font-weight:bold;")
        h_layout.addWidget(self._console_title)
        h_layout.addStretch()
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFlat(True)
        self._clear_btn.clicked.connect(self.clear)
        h_layout.addWidget(self._clear_btn)
        layout.addWidget(self._console_hdr)

        # ── text area ────────────────────────────────────────────────────
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

    # ── theme support ───────────────────────────────────────────────
    def refresh_theme(self, c: dict, fs: int) -> None:
        self._c = c
        self._fs = fs
        sm = max(fs - 2, 9)
        self._console_hdr.setStyleSheet(f"background:{c['surface2']};")
        self._console_title.setStyleSheet(
            f"color:{c['text']}; font-weight:bold; font-size:{sm}px;"
        )
        self._clear_btn.setStyleSheet(
            f"color:{c['muted']}; font-size:{sm}px; border:none;"
        )
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background:{c['bg']};
                color:{c['text']};
                font-family:'Consolas','Courier New',monospace;
                font-size:{sm}px;
                border:none;
                padding:8px;
            }}
        """)

    # ── public API ────────────────────────────────────────────────────────
    def log(self, message: str, level: str = 'info') -> None:
        ts = datetime.now().strftime('%H:%M:%S')
        color = self.LEVEL_COLORS.get(level, '#cdd6f4')
        html = (
            f'<span style="color:#45475a;">[{ts}]</span>'
            f'&nbsp;<span style="color:{color};">{message}</span>'
        )
        self.text_edit.append(html)
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def log_success(self, msg: str) -> None:
        self.log(msg, 'success')

    def log_error(self, msg: str) -> None:
        self.log(msg, 'error')

    def log_warning(self, msg: str) -> None:
        self.log(msg, 'warning')

    def clear(self) -> None:
        self.text_edit.clear()
