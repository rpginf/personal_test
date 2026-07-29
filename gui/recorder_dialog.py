from __future__ import annotations
from typing import Callable, List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSpinBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from core.recorder import ActionRecorder


class RecorderDialog(QDialog):
    """
    Modal dialog for macro recording.
    Press Start → perform actions → press Stop → preview → Insert into workflow.
    """

    def __init__(self, on_insert: Callable[[List[Dict[str, Any]]], None], parent=None):
        super().__init__(parent)
        self.on_insert = on_insert
        self._recorder = ActionRecorder(on_action=self._on_live_action)
        self._block_dicts: List[Dict[str, Any]] = []
        self._countdown_remaining = 0
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._tick_countdown)
        self.setWindowTitle("Action Recorder")
        self.setMinimumSize(480, 420)
        self.setStyleSheet("""
            QDialog { background:#1e1e2e; color:#cdd6f4; }
            QLabel { color:#cdd6f4; }
            QPushButton {
                background:#313244; color:#cdd6f4;
                border:1px solid #45475a; border-radius:4px;
                padding:6px 16px; font-size:12px;
            }
            QPushButton:hover { background:#45475a; }
            QPushButton:disabled { background:#1e1e2e; color:#6c7086; }
            QListWidget {
                background:#11111b; color:#cdd6f4;
                border:1px solid #313244; font-size:11px;
                font-family: Consolas, monospace;
            }
            QSpinBox { background:#11111b; color:#cdd6f4; border:1px solid #45475a; border-radius:4px; padding:3px; }
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── instructions ─────────────────────────────────────────────────
        info = QLabel(
            "1. Set a countdown delay, then click <b>Start Recording</b>.<br>"
            "2. Perform the actions you want to automate.<br>"
            "3. Click <b>Stop</b> to finish. Preview the captured blocks and click <b>Insert into Workflow</b>."
        )
        info.setStyleSheet("color:#a6adc8; font-size:11px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # ── countdown ────────────────────────────────────────────────────
        cd_row = QHBoxLayout()
        cd_row.addWidget(QLabel("Start delay (s):"))
        self.cd_spin = QSpinBox()
        self.cd_spin.setRange(0, 10)
        self.cd_spin.setValue(3)
        cd_row.addWidget(self.cd_spin)
        cd_row.addStretch()
        layout.addLayout(cd_row)

        # ── status label ──────────────────────────────────────────────────
        self.status_lbl = QLabel("Ready")
        f = QFont()
        f.setBold(True)
        f.setPointSize(11)
        self.status_lbl.setFont(f)
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet(
            "color:#50fa7b; background:#11111b; border-radius:4px; padding:6px;"
        )
        layout.addWidget(self.status_lbl)

        # ── action log ───────────────────────────────────────────────────
        layout.addWidget(QLabel("Captured actions:"))
        self.action_list = QListWidget()
        layout.addWidget(self.action_list, 1)

        # ── buttons ──────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("⏺  Start Recording")
        self.start_btn.setStyleSheet(
            "background:#50fa7b; color:#1e1e2e; font-weight:bold;"
            "border:none; border-radius:4px; padding:6px 16px;"
        )
        self.start_btn.clicked.connect(self._start)

        self.stop_btn = QPushButton("⬛  Stop")
        self.stop_btn.setStyleSheet(
            "background:#ff5555; color:#fff; font-weight:bold;"
            "border:none; border-radius:4px; padding:6px 16px;"
        )
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)

        self.insert_btn = QPushButton("➕  Insert into Workflow")
        self.insert_btn.setEnabled(False)
        self.insert_btn.clicked.connect(self._insert)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.insert_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    # ── recording flow ────────────────────────────────────────────────────
    def _start(self) -> None:
        self.action_list.clear()
        self._block_dicts.clear()
        self.insert_btn.setEnabled(False)
        delay = self.cd_spin.value()
        if delay > 0:
            self._countdown_remaining = delay
            self.start_btn.setEnabled(False)
            self._countdown_timer.start(1000)
            self.status_lbl.setText(f"Starting in {delay}…")
            self.status_lbl.setStyleSheet(
                "color:#ffb86c; background:#11111b; border-radius:4px; padding:6px;"
            )
        else:
            self._begin_recording()

    def _tick_countdown(self) -> None:
        self._countdown_remaining -= 1
        if self._countdown_remaining <= 0:
            self._countdown_timer.stop()
            self._begin_recording()
        else:
            self.status_lbl.setText(f"Starting in {self._countdown_remaining}…")

    def _begin_recording(self) -> None:
        self._recorder.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_lbl.setText("🔴  Recording…")
        self.status_lbl.setStyleSheet(
            "color:#ff5555; background:#11111b; border-radius:4px; padding:6px;"
        )

    def _stop(self) -> None:
        actions = self._recorder.stop()
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self._block_dicts = self._recorder.actions_to_block_dicts()

        self.action_list.clear()
        for bd in self._block_dicts:
            params_preview = ', '.join(f"{k}={v}" for k, v in list(bd.get('params', {}).items())[:3])
            self.action_list.addItem(f"{bd['type']}  ({params_preview})")

        n = len(self._block_dicts)
        self.status_lbl.setText(f"Stopped — {n} block{'s' if n != 1 else ''} captured")
        self.status_lbl.setStyleSheet(
            "color:#50fa7b; background:#11111b; border-radius:4px; padding:6px;"
        )
        self.insert_btn.setEnabled(n > 0)

    def _on_live_action(self, action: dict) -> None:
        label = (
            f"🖱 Click ({action['x']},{action['y']})"
            if action['type'] == 'mouse_click'
            else f"⌨ Key: {action['key']}"
        )
        self.action_list.addItem(label)
        self.action_list.scrollToBottom()

    def _insert(self) -> None:
        if self._block_dicts:
            self.on_insert(self._block_dicts)
            self.accept()
