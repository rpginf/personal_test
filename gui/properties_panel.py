from __future__ import annotations
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QScrollArea, QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from blocks.base import Block, Param
from gui.theme import THEMES, FONT_SIZES, DEFAULT_THEME, DEFAULT_FONT_SIZE


# Subclasses that guarantee keyboard Up/Down always steps the value,
# working around a PyQt6/Windows quirk where Key_Up can be dropped.
class _SpinBox(QSpinBox):
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Up:
            self.setValue(self.value() + self.singleStep())
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            self.setValue(self.value() - self.singleStep())
            event.accept()
        else:
            super().keyPressEvent(event)


class _DoubleSpinBox(QDoubleSpinBox):
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Up:
            self.setValue(self.value() + self.singleStep())
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            self.setValue(self.value() - self.singleStep())
            event.accept()
        else:
            super().keyPressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# Single-parameter widget
# ─────────────────────────────────────────────────────────────────────────────
class ParamWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param: Param, value, parent=None):
        super().__init__(parent)
        self.param = param
        self._build(value)

    def _build(self, value) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        t = self.param.type

        if t == 'text':
            self.widget = QLineEdit()
            self.widget.setText(str(value) if value is not None else '')
            self.widget.setPlaceholderText(self.param.placeholder)
            if self.param.tooltip:
                self.widget.setToolTip(self.param.tooltip)
            self.widget.textChanged.connect(self.value_changed)
            layout.addWidget(self.widget)

        elif t == 'password':
            self.widget = QLineEdit()
            self.widget.setEchoMode(QLineEdit.EchoMode.Password)
            self.widget.setText(str(value) if value is not None else '')
            self.widget.textChanged.connect(self.value_changed)
            layout.addWidget(self.widget)

        elif t == 'multiline':
            self.widget = QTextEdit()
            self.widget.setPlainText(str(value) if value is not None else '')
            self.widget.setPlaceholderText(self.param.placeholder)
            self.widget.setMinimumHeight(72)
            self.widget.setMaximumHeight(160)
            self.widget.textChanged.connect(self.value_changed)
            layout.addWidget(self.widget)

        elif t == 'int':
            self.widget = _SpinBox()
            self.widget.setRange(-9_999_999, 9_999_999)
            self.widget.setValue(int(value) if value is not None else 0)
            self.widget.valueChanged.connect(self.value_changed)
            layout.addWidget(self.widget)

        elif t == 'float':
            self.widget = _DoubleSpinBox()
            self.widget.setRange(-9_999_999.0, 9_999_999.0)
            self.widget.setDecimals(3)
            self.widget.setValue(float(value) if value is not None else 0.0)
            self.widget.valueChanged.connect(self.value_changed)
            layout.addWidget(self.widget)

        elif t == 'bool':
            self.widget = QCheckBox()
            self.widget.setChecked(bool(value) if value is not None else False)
            self.widget.stateChanged.connect(self.value_changed)
            layout.addWidget(self.widget)

        elif t == 'choice':
            self.widget = QComboBox()
            self.widget.addItems(self.param.options)
            if str(value) in self.param.options:
                self.widget.setCurrentText(str(value))
            self.widget.currentTextChanged.connect(self.value_changed)
            layout.addWidget(self.widget)

        elif t == 'keyseq':
            self.widget = QLineEdit()
            self.widget.setText(str(value) if value is not None else '')
            self.widget.setPlaceholderText(self.param.placeholder)
            if self.param.tooltip:
                self.widget.setToolTip(self.param.tooltip)
            self.widget.textChanged.connect(self.value_changed)
            layout.addWidget(self.widget)
            btn = QPushButton('⌨')
            btn.setFixedWidth(28)
            btn.setToolTip('Open Key Picker — press keys to capture their names')
            btn.setStyleSheet('padding:0;')
            btn.clicked.connect(self._open_key_picker)
            layout.addWidget(btn)

        elif t in ('file', 'folder', 'file_save'):
            self.widget = QLineEdit()
            self.widget.setText(str(value) if value is not None else '')
            self.widget.setPlaceholderText(self.param.placeholder or 'Path...')
            self.widget.textChanged.connect(self.value_changed)
            layout.addWidget(self.widget)
            btn = QPushButton('…')
            btn.setFixedWidth(28)
            btn.setStyleSheet("padding:0;")
            btn.clicked.connect(self._browse)
            layout.addWidget(btn)

        else:
            self.widget = QLineEdit()
            self.widget.setText(str(value) if value is not None else '')
            self.widget.textChanged.connect(self.value_changed)
            layout.addWidget(self.widget)

    def _open_key_picker(self) -> None:
        from gui.key_picker import KeyPickerDialog
        dlg = KeyPickerDialog(self)
        if dlg.exec():
            seq = dlg.get_sequence()
            if seq:
                existing = self.widget.text().strip().rstrip(',')
                self.widget.setText((existing + ', ' + seq) if existing else seq)

    def _browse(self) -> None:
        t = self.param.type
        if t == 'folder':
            path = QFileDialog.getExistingDirectory(self, f'Select {self.param.label}')
        elif t == 'file_save':
            path, _ = QFileDialog.getSaveFileName(self, f'Save {self.param.label}')
        else:
            path, _ = QFileDialog.getOpenFileName(self, f'Open {self.param.label}')
        if path:
            self.widget.setText(path)

    def get_value(self):
        t = self.param.type
        if t == 'bool':
            return self.widget.isChecked()
        if t == 'int':
            return self.widget.value()
        if t == 'float':
            return self.widget.value()
        if t == 'multiline':
            return self.widget.toPlainText()
        if t == 'choice':
            return self.widget.currentText()
        return self.widget.text()

    def set_value(self, value) -> None:
        t = self.param.type
        if t == 'bool':
            self.widget.setChecked(bool(value))
        elif t == 'int':
            self.widget.setValue(int(value) if value else 0)
        elif t == 'float':
            self.widget.setValue(float(value) if value else 0.0)
        elif t == 'multiline':
            self.widget.setPlainText(str(value) if value else '')
        elif t == 'choice':
            if str(value) in self.param.options:
                self.widget.setCurrentText(str(value))
        else:
            self.widget.setText(str(value) if value else '')


# ─────────────────────────────────────────────────────────────────────────────
# Properties panel
# ─────────────────────────────────────────────────────────────────────────────


class PropertiesPanel(QWidget):
    """Right-hand panel that shows editable fields for the selected block."""
    block_updated = pyqtSignal(object)   # emits the Block instance after any change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._block: Optional[Block] = None
        self._widgets: dict = {}
        self._c = THEMES[DEFAULT_THEME]
        self._fs = FONT_SIZES[DEFAULT_FONT_SIZE]
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── header ──────────────────────────────────────────────────────
        self.header = QWidget()
        h = QVBoxLayout(self.header)
        h.setContentsMargins(10, 10, 10, 6)
        self.title_lbl = QLabel("Select a block to configure")
        self.title_lbl.setStyleSheet("font-weight:bold;")
        self.sub_lbl = QLabel("")
        h.addWidget(self.title_lbl)
        h.addWidget(self.sub_lbl)
        layout.addWidget(self.header)

        # ── scrollable form ───────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._scroll.viewport().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        self.form_layout.setContentsMargins(12, 12, 12, 12)
        self.form_layout.setSpacing(10)
        self.form_layout.addStretch()
        self._scroll.setWidget(self.form_widget)
        layout.addWidget(self._scroll, 1)

    # ── theme support ──────────────────────────────────────────────────────
    def refresh_theme(self, c: dict, fs: int) -> None:
        self._c = c
        self._fs = fs
        sm = max(fs - 2, 9)
        self.header.setStyleSheet(f"background:{c['surface2']}; padding:8px;")
        self.title_lbl.setStyleSheet(
            f"color:{c['text']}; font-weight:bold; font-size:{fs}px;"
        )
        self.sub_lbl.setStyleSheet(f"color:{c['muted']}; font-size:{sm}px;")
        self._scroll.setStyleSheet(
            f"QScrollArea{{border:none; background:{c['surface']};}}"
        )
        self.form_widget.setStyleSheet(f"background:{c['surface']};") 

    # ── public API ────────────────────────────────────────────────────────
    def show_block(self, block: Optional[Block]) -> None:
        self._block = block
        self._widgets.clear()

        # clear layout
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if block is None:
            self.title_lbl.setText("Select a block to configure")
            self.sub_lbl.setText("")
            self.form_layout.addStretch()
            return

        self.title_lbl.setText(f"{block.ICON}  {block.NAME}")
        self.sub_lbl.setText(f"Category: {block.CATEGORY}")

        if not block.PARAMS:
            lbl = QLabel("This block has no configurable parameters.")
            lbl.setStyleSheet(
                f"color:{self._c['muted']}; font-style:italic; font-size:{self._fs}px;"
            )
            self.form_layout.addWidget(lbl)
            self.form_layout.addStretch()
            return

        for param in block.PARAMS:
            value = block.params.get(param.name, param.default)

            # label
            lbl_text = param.label + ('  *' if param.required else '')
            lbl = QLabel(lbl_text)
            req_color = self._c['text'] if param.required else self._c['subtext']
            lbl.setStyleSheet(
                f"color:{req_color}; font-size:{self._fs}px; "
                f"font-weight:{'bold' if param.required else 'normal'};"
            )
            if param.tooltip:
                lbl.setToolTip(param.tooltip)

            pw = ParamWidget(param, value)
            pw.value_changed.connect(self._on_changed)
            self._widgets[param.name] = pw

            container = QWidget()
            cl = QVBoxLayout(container)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(2)
            cl.addWidget(lbl)
            cl.addWidget(pw)
            self.form_layout.addWidget(container)

        self.form_layout.addStretch()

    # ── internal ─────────────────────────────────────────────────────────
    def _on_changed(self) -> None:
        if self._block:
            for name, pw in self._widgets.items():
                self._block.params[name] = pw.get_value()
            self.block_updated.emit(self._block)
