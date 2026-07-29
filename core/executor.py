from __future__ import annotations
from typing import Any, Dict
from PyQt6.QtCore import QThread, pyqtSignal
from core.workflow import Workflow


class ExecutionThread(QThread):
    """Runs a Workflow in a background thread, emitting signals for the GUI."""

    block_started = pyqtSignal(str)           # block_id
    block_finished = pyqtSignal(str, str)     # block_id, output_text
    block_failed = pyqtSignal(str, str)       # block_id, error_message
    workflow_finished = pyqtSignal(bool, str) # success, summary_message
    log_message = pyqtSignal(str, str)        # message, level (info/success/error/warning)

    def __init__(self, workflow: Workflow, start_index: int = 0, parent=None):
        super().__init__(parent)
        self.workflow = workflow
        self.start_index = start_index
        self._stop_requested = False
        self.context: Dict[str, Any] = {}

    def stop(self) -> None:
        self._stop_requested = True

    # ------------------------------------------------------------------ #
    # Main run loop
    # ------------------------------------------------------------------ #
    def run(self) -> None:
        self.context = {}
        blocks = self.workflow.blocks[self.start_index:]
        total = len(blocks)

        if not blocks:
            self.workflow_finished.emit(True, "No blocks to run")
            return

        self.log_message.emit(f"▶  Starting '{self.workflow.name}'  ({total} blocks)", 'info')

        for idx, block in enumerate(blocks, 1):
            if self._stop_requested:
                self.log_message.emit("⬛  Workflow stopped by user", 'warning')
                self.workflow_finished.emit(False, "Stopped by user")
                return

            block.status = 'running'
            block.error_message = ''
            self.block_started.emit(block.id)
            self.log_message.emit(
                f"[{idx}/{total}]  {block.ICON} {block.NAME}", 'info'
            )

            try:
                block.execute(self.context)
                block.status = 'success'
                out = str(block.output) if block.output is not None else 'Done'
                self.block_finished.emit(block.id, out)
                self.log_message.emit(f"       ✓  {out}", 'success')
            except Exception as exc:
                block.status = 'error'
                block.error_message = str(exc)
                self.block_failed.emit(block.id, str(exc))
                self.log_message.emit(f"       ✗  {exc}", 'error')
                self.workflow_finished.emit(
                    False, f"Failed at '{block.NAME}': {exc}"
                )
                return

        self.workflow_finished.emit(True, f"All {total} blocks completed successfully ✓")
