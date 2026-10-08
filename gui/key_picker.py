from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

# ── Qt.Key → keyboard-library name ────────────────────────────────────────
_SPECIAL: dict[Qt.Key, str] = {
    Qt.Key.Key_Up: 'up',           Qt.Key.Key_Down: 'down',
    Qt.Key.Key_Left: 'left',       Qt.Key.Key_Right: 'right',
    Qt.Key.Key_Return: 'enter',    Qt.Key.Key_Enter: 'enter',
    Qt.Key.Key_Space: 'space',     Qt.Key.Key_Tab: 'tab',
    Qt.Key.Key_Escape: 'esc',      Qt.Key.Key_Backspace: 'backspace',
    Qt.Key.Key_Delete: 'delete',   Qt.Key.Key_Insert: 'insert',
    Qt.Key.Key_Home: 'home',       Qt.Key.Key_End: 'end',
    Qt.Key.Key_PageUp: 'page up',  Qt.Key.Key_PageDown: 'page down',
    Qt.Key.Key_F1:  'f1',  Qt.Key.Key_F2:  'f2',  Qt.Key.Key_F3:  'f3',
    Qt.Key.Key_F4:  'f4',  Qt.Key.Key_F5:  'f5',  Qt.Key.Key_F6:  'f6',
    Qt.Key.Key_F7:  'f7',  Qt.Key.Key_F8:  'f8',  Qt.Key.Key_F9:  'f9',
    Qt.Key.Key_F10: 'f10', Qt.Key.Key_F11: 'f11', Qt.Key.Key_F12: 'f12',
    Qt.Key.Key_Control: 'ctrl',       Qt.Key.Key_Shift: 'shift',
    Qt.Key.Key_Alt: 'alt',            Qt.Key.Key_Meta: 'win',
    Qt.Key.Key_AltGr: 'alt gr',
    Qt.Key.Key_CapsLock:   'caps lock',
    Qt.Key.Key_NumLock:    'num lock',
    Qt.Key.Key_ScrollLock: 'scroll lock',
    Qt.Key.Key_Pause:      'pause',
    Qt.Key.Key_Print:      'print screen',
    Qt.Key.Key_SysReq:     'print screen',
}

# Numpad keys share Qt key codes with normal keys when KeypadModifier is set
_NUMPAD: dict[Qt.Key, str] = {
    Qt.Key.Key_0: 'numpad 0', Qt.Key.Key_1: 'numpad 1',
    Qt.Key.Key_2: 'numpad 2', Qt.Key.Key_3: 'numpad 3',
    Qt.Key.Key_4: 'numpad 4', Qt.Key.Key_5: 'numpad 5',
    Qt.Key.Key_6: 'numpad 6', Qt.Key.Key_7: 'numpad 7',
    Qt.Key.Key_8: 'numpad 8', Qt.Key.Key_9: 'numpad 9',
    Qt.Key.Key_Asterisk: 'numpad *', Qt.Key.Key_Plus:   'numpad +',
    Qt.Key.Key_Minus:    'numpad -', Qt.Key.Key_Period:  'numpad .',
    Qt.Key.Key_Slash:    'numpad /', Qt.Key.Key_Return:  'numpad enter',
    Qt.Key.Key_Delete:   'numpad .', Qt.Key.Key_Insert:  'numpad 0',
}

_MODIFIERS = frozenset({
    Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
    Qt.Key.Key_Meta, Qt.Key.Key_AltGr,
})


def event_to_key_name(event: QKeyEvent) -> str:
    """Return the keyboard-library key name for a QKeyEvent, or '' if unknown."""
    key = event.key()
    mods = event.modifiers()
    is_numpad = bool(mods & Qt.KeyboardModifier.KeypadModifier)

    # Determine base name
    if is_numpad and key in _NUMPAD:
        base = _NUMPAD[key]
    elif key in _SPECIAL:
        base = _SPECIAL[key]
    else:
        text = event.text()
        if text and text.isprintable() and not text.isspace():
            base = text.lower()
        else:
            return ''

    # Modifier key pressed alone → return its name without prefix
    if key in _MODIFIERS:
        return base

    prefixes: list[str] = []
    if mods & Qt.KeyboardModifier.ControlModifier:
        prefixes.append('ctrl')
    if mods & Qt.KeyboardModifier.AltModifier:
        prefixes.append('alt')
    # For printable characters the shifted form is embedded in event.text();
    # only add 'shift' explicitly for non-printable (special) keys.
    text = event.text()
    has_printable = bool(text and text.isprintable() and not text.isspace())
    if (mods & Qt.KeyboardModifier.ShiftModifier) and not has_printable:
        prefixes.append('shift')

    return '+'.join(prefixes + [base]) if prefixes else base


# ── Dialog ─────────────────────────────────────────────────────────────────
class KeyPickerDialog(QDialog):
    """
    Modal dialog: press keys one at a time to build a sequence string
    compatible with keyboard.send() (e.g. "ctrl+c, down, enter").
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Key Picker')
        self.setMinimumWidth(360)
        self.setFixedHeight(210)
        self._captured: list[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(14, 12, 14, 12)

        instr = QLabel(
            'Press keys one at a time — each is added to the sequence.\n'
            'Combos like Ctrl+C or Alt+F4 are captured as a single entry.'
        )
        instr.setWordWrap(True)
        lay.addWidget(instr)

        self.preview = QLabel('—')
        self.preview.setWordWrap(True)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet(
            'font-weight:bold; padding:8px; border-radius:4px;'
            'border:1px solid rgba(128,128,128,0.4);'
        )
        self.preview.setMinimumHeight(36)
        lay.addWidget(self.preview)

        row = QHBoxLayout()
        clear = QPushButton('Clear')
        clear.clicked.connect(self._clear)
        row.addWidget(clear)

        cancel = QPushButton('Cancel')
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)

        insert = QPushButton('Insert into field')
        insert.setDefault(True)
        insert.clicked.connect(self.accept)
        row.addWidget(insert)

        lay.addLayout(row)

    # ------------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent) -> None:
        name = event_to_key_name(event)
        if name:
            self._captured.append(name)
            self.preview.setText(', '.join(self._captured))
        event.accept()  # prevent dialog shortcuts (Enter/Esc) from interfering

    def _clear(self) -> None:
        self._captured.clear()
        self.preview.setText('—')

    def get_sequence(self) -> str:
        return ', '.join(self._captured)
