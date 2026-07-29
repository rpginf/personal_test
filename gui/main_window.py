from __future__ import annotations
import os
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QLabel, QPushButton, QMessageBox, QFileDialog,
    QInputDialog, QDialog, QDialogButtonBox, QTreeWidget, QTreeWidgetItem,
    QApplication,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence, QFont, QColor

from core.workflow import Workflow
from core.executor import ExecutionThread
from gui.workflow_view import WorkflowView
from gui.block_palette import BlockPalette
from gui.properties_panel import PropertiesPanel
from gui.console_widget import ConsoleWidget
from blocks.base import Block
from blocks.registry import load_all_blocks, get_all_categories, get_blocks_for_category, create_block_from_dict
from gui.theme import (
    THEMES, FONT_SIZES, DEFAULT_THEME, DEFAULT_FONT_SIZE,
    make_app_style, make_btn_run, make_btn_stop, make_btn_rec,
)


# ─────────────────────────────────────────────────────────────────────────────
# Add-block dialog (reusable)
# ─────────────────────────────────────────────────────────────────────────────
class AddBlockDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_class = None
        self.setWindowTitle("Add Block")
        self.setMinimumSize(360, 520)

        layout = QVBoxLayout(self)
        lbl = QLabel("Choose a block type (double-click or select + OK):")
        lbl.setStyleSheet("font-size:11px;")
        layout.addWidget(lbl)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        for cat in get_all_categories():
            cat_item = QTreeWidgetItem([f"  {cat}"])
            cat_item.setData(0, Qt.ItemDataRole.UserRole, None)
            cat_item.setForeground(0, QColor('#7c6af7'))
            f = QFont(); f.setBold(True); cat_item.setFont(0, f)
            for cls in sorted(get_blocks_for_category(cat), key=lambda c: c.NAME):
                child = QTreeWidgetItem([f"  {cls.ICON}  {cls.NAME}"])
                child.setData(0, Qt.ItemDataRole.UserRole, cls)
                child.setToolTip(0, cls.DESCRIPTION)
                cat_item.addChild(child)
            self.tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)
        self.tree.itemDoubleClicked.connect(self._double_click)
        layout.addWidget(self.tree)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _double_click(self, item, _col) -> None:
        cls = item.data(0, Qt.ItemDataRole.UserRole)
        if cls:
            self.selected_class = cls
            self.accept()

    def _accept(self) -> None:
        item = self.tree.currentItem()
        if item:
            cls = item.data(0, Qt.ItemDataRole.UserRole)
            if cls:
                self.selected_class = cls
                self.accept()
                return
        QMessageBox.information(self, "Select a block", "Please select a block type first.")


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        load_all_blocks()
        self.workflow = Workflow("New Workflow")
        self._executor: Optional[ExecutionThread] = None
        self._current_file: Optional[str] = None
        self._modified = False
        self._theme_name = DEFAULT_THEME
        self._font_size_name = DEFAULT_FONT_SIZE

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._connect_signals()

        self.setWindowTitle("Automation Studio")
        self.resize(1440, 860)
        self.setMinimumSize(920, 600)
        self._apply_appearance()
        self.statusBar().showMessage("Ready  —  double-click a block in the library to add it")

    # ── UI construction ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Central widget
        self.workflow_view = WorkflowView()
        self.setCentralWidget(self.workflow_view)

        # Left dock – block palette
        self.palette_dock = QDockWidget("Blocks", self)
        self.palette_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.palette = BlockPalette()
        self.palette_dock.setWidget(self.palette)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.palette_dock)
        self.palette_dock.setMinimumWidth(200)
        self.palette_dock.setMaximumWidth(300)

        # Right dock – properties
        self.props_dock = QDockWidget("Properties", self)
        self.props_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.props = PropertiesPanel()
        self.props_dock.setWidget(self.props)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.props_dock)
        self.props_dock.setMinimumWidth(260)
        self.props_dock.setMaximumWidth(420)

        # Bottom dock – console
        self.console_dock = QDockWidget("Output", self)
        self.console_dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )
        self.console = ConsoleWidget()
        self.console_dock.setWidget(self.console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)
        self.console_dock.setMinimumHeight(140)
        self.console_dock.setMaximumHeight(340)

    def _build_menu(self) -> None:
        mb = self.menuBar()

        # File
        fm = mb.addMenu("File")
        self._add_action(fm, "New Workflow",      QKeySequence.StandardKey.New,  self.new_workflow)
        self._add_action(fm, "Open Workflow…",    QKeySequence.StandardKey.Open, self.open_workflow)
        fm.addSeparator()
        self._add_action(fm, "Save",              QKeySequence.StandardKey.Save, self.save_workflow)
        self._add_action(fm, "Save As…",          QKeySequence("Ctrl+Shift+S"),  self.save_workflow_as)
        fm.addSeparator()
        self._add_action(fm, "Exit",              QKeySequence.StandardKey.Quit, self.close)

        # Edit
        em = mb.addMenu("Edit")
        self._add_action(em, "Rename Workflow…",  None, self.rename_workflow)
        em.addSeparator()
        self._add_action(em, "Clear All Blocks",  None, self.clear_workflow)

        # Run
        rm = mb.addMenu("Run")
        self._add_action(rm, "▶  Run Workflow",   QKeySequence("F5"),  self.run_workflow)
        self._add_action(rm, "⬛  Stop",           QKeySequence("F6"),  self.stop_workflow)
        rm.addSeparator()
        self._add_action(rm, "Reset Block Statuses", None, self._reset_statuses)

        # View
        vm = mb.addMenu("View")
        vm.addAction(self.palette_dock.toggleViewAction())
        vm.addAction(self.props_dock.toggleViewAction())
        vm.addAction(self.console_dock.toggleViewAction())
        vm.addSeparator()

        font_menu = vm.addMenu("Font Size")
        font_grp = QActionGroup(self)
        font_grp.setExclusive(True)
        for size_name in FONT_SIZES:
            act = QAction(size_name, self, checkable=True)
            act.setChecked(size_name == self._font_size_name)
            act.triggered.connect(lambda checked, s=size_name: self._set_font_size(s))
            font_grp.addAction(act)
            font_menu.addAction(act)

        theme_menu = vm.addMenu("Theme")
        theme_grp = QActionGroup(self)
        theme_grp.setExclusive(True)
        for theme_name in THEMES:
            act = QAction(theme_name, self, checkable=True)
            act.setChecked(theme_name == self._theme_name)
            act.triggered.connect(lambda checked, t=theme_name: self._set_theme(t))
            theme_grp.addAction(act)
            theme_menu.addAction(act)

        # Help
        hm = mb.addMenu("Help")
        self._add_action(hm, "About", None, self._show_about)

    def _add_action(self, menu, text, shortcut, slot) -> None:
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(shortcut)
        act.triggered.connect(slot)
        menu.addAction(act)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(14, 14))
        self.addToolBar(tb)

        for label, slot in [
            ("📄 New",   self.new_workflow),
            ("📂 Open",  self.open_workflow),
            ("💾 Save",  self.save_workflow),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            tb.addWidget(btn)

        tb.addSeparator()

        self.run_btn = QPushButton("▶  Run")
        self.run_btn.setToolTip("Run workflow (F5)")
        self.run_btn.clicked.connect(self.run_workflow)
        tb.addWidget(self.run_btn)

        self.stop_btn = QPushButton("⬛  Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_workflow)
        tb.addWidget(self.stop_btn)

        tb.addSeparator()

        self.rec_btn = QPushButton("⏺  Record")
        self.rec_btn.setToolTip("Record mouse & keyboard actions as blocks")
        self.rec_btn.clicked.connect(self._open_recorder)
        tb.addWidget(self.rec_btn)

        tb.addSeparator()

        self.wf_name_tb = QLabel("  New Workflow")
        tb.addWidget(self.wf_name_tb)

    def _connect_signals(self) -> None:
        self.palette.block_double_clicked.connect(self._add_block_class)
        self.workflow_view.block_selected.connect(self.props.show_block)
        self.workflow_view.workflow_changed.connect(self._mark_modified)
        self.workflow_view.add_btn.clicked.connect(self._show_add_dialog)
        self.props.block_updated.connect(self._on_block_updated)

    # ── workflow management ───────────────────────────────────────────────
    def new_workflow(self) -> None:
        if not self._confirm_discard():
            return
        self.workflow = Workflow("New Workflow")
        self._current_file = None
        self._modified = False
        self.workflow_view.clear()
        self._sync_name()
        self.props.show_block(None)
        self.console.log("New workflow created")
        self._update_title()

    def open_workflow(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Workflow", "",
            "Automation Workflow (*.json);;All Files (*)"
        )
        if not path:
            return
        try:
            self.workflow = Workflow.load(path)
            self._current_file = path
            self._modified = False
            self.workflow_view.clear()
            for block in self.workflow.blocks:
                self.workflow_view.add_card(block)
            self._sync_name()
            self.props.show_block(None)
            self.console.log_success(f"Opened: {path}")
            self._update_title()
        except Exception as exc:
            QMessageBox.critical(self, "Open Error", str(exc))
            self.console.log_error(f"Failed to open: {exc}")

    def save_workflow(self) -> bool:
        if not self._current_file:
            return self.save_workflow_as()
        return self._do_save(self._current_file)

    def save_workflow_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Workflow",
            (self.workflow.name or "workflow") + ".json",
            "Automation Workflow (*.json);;All Files (*)"
        )
        if not path:
            return False
        return self._do_save(path)

    def _do_save(self, path: str) -> bool:
        try:
            self.workflow.blocks = self.workflow_view.get_blocks_in_order()
            self.workflow.save(path)
            self._current_file = path
            self._modified = False
            self._update_title()
            self.console.log_success(f"Saved: {path}")
            self.statusBar().showMessage(f"Saved → {path}")
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            return False

    def rename_workflow(self) -> None:
        name, ok = QInputDialog.getText(
            self, "Rename", "Workflow name:", text=self.workflow.name
        )
        if ok and name.strip():
            self.workflow.name = name.strip()
            self._sync_name()
            self._mark_modified()
            self._update_title()

    def clear_workflow(self) -> None:
        if not self.workflow_view.cards:
            return
        if QMessageBox.question(
            self, "Clear", "Remove all blocks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.workflow_view.clear()
            self.workflow.blocks.clear()
            self.props.show_block(None)
            self._mark_modified()

    # ── block management ─────────────────────────────────────────────────
    def _add_block_class(self, cls) -> None:
        block = cls()
        self.workflow.blocks.append(block)
        self.workflow_view.add_card(block)
        self._mark_modified()
        self.statusBar().showMessage(f"Added: {block.NAME}")

    def _show_add_dialog(self) -> None:
        dlg = AddBlockDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_class:
            self._add_block_class(dlg.selected_class)

    def _on_block_updated(self, block: Block) -> None:
        self.workflow_view.update_card(block)
        self._mark_modified()

    # ── recording ────────────────────────────────────────────────────────
    def _open_recorder(self) -> None:
        from gui.recorder_dialog import RecorderDialog
        dlg = RecorderDialog(on_insert=self._insert_recorded_blocks, parent=self)
        dlg.exec()

    def _insert_recorded_blocks(self, block_dicts: List[Dict[str, Any]]) -> None:
        for bd in block_dicts:
            try:
                block = create_block_from_dict(bd)
                self.workflow.blocks.append(block)
                self.workflow_view.add_card(block)
            except Exception as exc:
                self.console.log_warning(f"Skipping recorded block: {exc}")
        self._mark_modified()
        self.console.log_success(f"Inserted {len(block_dicts)} recorded blocks")

    # ── execution ────────────────────────────────────────────────────────
    def run_workflow(self) -> None:
        if self._executor and self._executor.isRunning():
            return
        blocks = self.workflow_view.get_blocks_in_order()
        if not blocks:
            self.console.log_warning("No blocks to run. Add blocks to the workflow first.")
            return
        self.workflow.blocks = blocks
        self.workflow.reset_statuses()
        self.workflow_view.update_all_cards()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage("Running…")

        self._executor = ExecutionThread(self.workflow, parent=self)
        self._executor.block_started.connect(self._on_block_started)
        self._executor.block_finished.connect(self._on_block_finished)
        self._executor.block_failed.connect(self._on_block_failed)
        self._executor.workflow_finished.connect(self._on_wf_finished)
        self._executor.log_message.connect(self.console.log)
        self._executor.start()

    def stop_workflow(self) -> None:
        if self._executor and self._executor.isRunning():
            self._executor.stop()
            self.console.log_warning("Stop requested…")

    def _on_block_started(self, block_id: str) -> None:
        self.workflow_view.select_card(block_id)
        block = self.workflow.get_block(block_id)
        if block:
            self.workflow_view.update_card(block)

    def _on_block_finished(self, block_id: str, _output: str) -> None:
        block = self.workflow.get_block(block_id)
        if block:
            self.workflow_view.update_card(block)

    def _on_block_failed(self, block_id: str, error: str) -> None:
        block = self.workflow.get_block(block_id)
        if block:
            self.workflow_view.update_card(block)

    def _on_wf_finished(self, success: bool, msg: str) -> None:
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.workflow_view.update_all_cards()
        if success:
            self.statusBar().showMessage("Workflow completed ✓")
            self.console.log_success(msg)
        else:
            self.statusBar().showMessage("Workflow failed ✗")
            self.console.log_error(msg)

    def _reset_statuses(self) -> None:
        self.workflow.reset_statuses()
        self.workflow_view.update_all_cards()

    # ── helpers ──────────────────────────────────────────────────────────
    def _sync_name(self) -> None:
        self.workflow_view.set_workflow_name(self.workflow.name)
        self.wf_name_tb.setText(f"  {self.workflow.name}")

    def _mark_modified(self) -> None:
        self._modified = True
        self._update_title()

    def _update_title(self) -> None:
        fname = os.path.basename(self._current_file) if self._current_file else ""
        mod = " *" if self._modified else ""
        sep = "  —  " if fname else ""
        self.setWindowTitle(f"Automation Studio  —  {self.workflow.name}{sep}{fname}{mod}")

    def _confirm_discard(self) -> bool:
        if not self._modified:
            return True
        reply = QMessageBox.question(
            self, "Unsaved Changes", "Save the current workflow before continuing?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return False
        if reply == QMessageBox.StandardButton.Save:
            return self.save_workflow()
        return True

    def _apply_appearance(self) -> None:
        c = THEMES[self._theme_name]
        fs = FONT_SIZES[self._font_size_name]
        QApplication.instance().setStyleSheet(make_app_style(c, fs))
        self.run_btn.setStyleSheet(make_btn_run(c, fs))
        self.stop_btn.setStyleSheet(make_btn_stop(c, fs))
        self.rec_btn.setStyleSheet(make_btn_rec(c, fs))
        self.wf_name_tb.setStyleSheet(
            f"color:{c['text']}; font-size:{fs + 1}px; font-weight:bold;"
        )
        self.workflow_view.refresh_theme(c, fs)
        self.palette.refresh_theme(c, fs)
        self.props.refresh_theme(c, fs)
        self.console.refresh_theme(c, fs)

    def _set_font_size(self, size_name: str) -> None:
        self._font_size_name = size_name
        self._apply_appearance()
        self.statusBar().showMessage(f"Font size: {size_name}")

    def _set_theme(self, theme_name: str) -> None:
        self._theme_name = theme_name
        self._apply_appearance()
        self.statusBar().showMessage(f"Theme: {theme_name}")

    def _show_about(self) -> None:
        QMessageBox.about(
            self, "Automation Studio",
            "<h3>Automation Studio</h3>"
            "<p>A visual block-based automation workflow builder.</p>"
            "<b>Block categories:</b>"
            "<ul>"
            "<li>📁 <b>File</b> – copy, move, create, delete, list files</li>"
            "<li>📊 <b>Excel</b> – open, filter, find values, write cells, save</li>"
            "<li>🌐 <b>Web</b> – scrape pages, extract text/tables, fill forms</li>"
            "<li>🖥️ <b>App Automation</b> – keyboard, mouse, credentials, scroll</li>"
            "<li>🤖 <b>AI</b> – OpenAI text generation and data extraction</li>"
            "<li>📸 <b>Computer Vision</b> – screenshot, find/click images, OCR</li>"
            "<li>🐍 <b>Control</b> – wait, set variable, log, Python script</li>"
            "</ul>"
            "<p>Workflows are saved as <code>.json</code> files.</p>"
            "<p>By Pineda Gomez.</p>"
        )

    def closeEvent(self, event) -> None:
        if self._modified and not self._confirm_discard():
            event.ignore()
            return
        if self._executor and self._executor.isRunning():
            self._executor.stop()
            self._executor.wait(2000)
        event.accept()
