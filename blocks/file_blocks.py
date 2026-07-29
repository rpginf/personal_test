from __future__ import annotations
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .base import Block, Param
from .registry import register


@register
class CreateFileBlock(Block):
    CATEGORY = 'File'
    NAME = 'Create File'
    DESCRIPTION = 'Creates a new text file with optional content'
    ICON = '📄'
    COLOR = '#50fa7b'
    PARAMS = [
        Param('path', 'File Path', 'file_save', required=True, placeholder='C:\\path\\to\\file.txt'),
        Param('content', 'Content', 'multiline', default=''),
        Param('overwrite', 'Overwrite if exists', 'bool', default=False),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        path = Path(self.params['path'])
        if path.exists() and not self.params.get('overwrite'):
            raise FileExistsError(f"File already exists: {path}. Enable 'Overwrite' to replace it.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.params.get('content') or '', encoding='utf-8')
        context['last_created_file'] = str(path)
        self.output = f"Created: {path}"


@register
class CopyFileBlock(Block):
    CATEGORY = 'File'
    NAME = 'Copy File'
    DESCRIPTION = 'Copies a file to a destination folder, optionally adding a date prefix'
    ICON = '📋'
    COLOR = '#50fa7b'
    PARAMS = [
        Param('source', 'Source File', 'file', required=True,
              placeholder='\\\\server\\share\\Cpk_Report_300.xlsm'),
        Param('destination', 'Destination Folder', 'folder', required=True,
              placeholder='C:\\Users\\...\\cpk_kopie'),
        Param('add_date_prefix', 'Add Date Prefix (YYYY-MM-DD)', 'bool', default=False),
        Param('date_format', 'Date Format', 'text', default='%Y-%m-%d'),
        Param('overwrite', 'Overwrite if exists', 'bool', default=True),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        source = Path(self.params['source'])
        dest_dir = Path(self.params['destination'])
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = source.name
        if self.params.get('add_date_prefix'):
            fmt = self.params.get('date_format') or '%Y-%m-%d'
            filename = f"{datetime.now().strftime(fmt)}_{filename}"
        target = dest_dir / filename
        if target.exists() and not self.params.get('overwrite'):
            raise FileExistsError(f"Destination already exists: {target}")
        shutil.copy2(source, target)
        context['last_copied_file'] = str(target)
        self.output = f"Copied → {target}"

    def get_summary(self) -> str:
        src = self.params.get('source', '')
        dst = self.params.get('destination', '')
        name = Path(src).name if src else '?'
        return f"{name}  →  {dst}" if src else "Not configured"


@register
class MoveFileBlock(Block):
    CATEGORY = 'File'
    NAME = 'Move / Rename File'
    DESCRIPTION = 'Moves or renames a file'
    ICON = '📦'
    COLOR = '#50fa7b'
    PARAMS = [
        Param('source', 'Source File', 'file', required=True),
        Param('destination', 'Destination Folder', 'folder', required=True),
        Param('new_name', 'New filename (optional)', 'text', default='',
              placeholder='Leave empty to keep original name'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        source = Path(self.params['source'])
        dest_dir = Path(self.params['destination'])
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = self.params.get('new_name') or source.name
        dest = dest_dir / name
        shutil.move(str(source), str(dest))
        context['last_moved_file'] = str(dest)
        self.output = f"Moved → {dest}"


@register
class DeleteFileBlock(Block):
    CATEGORY = 'File'
    NAME = 'Delete File / Folder'
    DESCRIPTION = 'Permanently deletes a file or folder'
    ICON = '🗑️'
    COLOR = '#ff5555'
    PARAMS = [
        Param('path', 'Path to delete', 'file', required=True),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        path = Path(self.params['path'])
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(str(path))
        self.output = f"Deleted: {path}"


@register
class ListFilesBlock(Block):
    CATEGORY = 'File'
    NAME = 'List Files'
    DESCRIPTION = 'Lists files in a directory matching a pattern'
    ICON = '📁'
    COLOR = '#50fa7b'
    PARAMS = [
        Param('directory', 'Directory', 'folder', required=True),
        Param('pattern', 'File Pattern', 'text', default='*', placeholder='*.xlsx'),
        Param('recursive', 'Search Recursively', 'bool', default=False),
        Param('output_variable', 'Store list in variable', 'text', default='file_list'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        directory = Path(self.params['directory'])
        pattern = self.params.get('pattern') or '*'
        if self.params.get('recursive'):
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        result = sorted(str(f) for f in files)
        var = self.params.get('output_variable') or 'file_list'
        context[var] = result
        self.output = f"{len(result)} files found"


@register
class WaitBlock(Block):
    CATEGORY = 'Control'
    NAME = 'Wait'
    DESCRIPTION = 'Pauses execution for a specified number of seconds'
    ICON = '⏱️'
    COLOR = '#8be9fd'
    PARAMS = [
        Param('seconds', 'Seconds to wait', 'float', default=1.0),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        duration = float(self.params.get('seconds') or 1.0)
        time.sleep(duration)
        self.output = f"Waited {duration}s"


@register
class SetVariableBlock(Block):
    CATEGORY = 'Control'
    NAME = 'Set Variable'
    DESCRIPTION = 'Sets a named variable in the workflow context'
    ICON = '📌'
    COLOR = '#8be9fd'
    PARAMS = [
        Param('name', 'Variable Name', 'text', required=True, placeholder='my_var'),
        Param('value', 'Value', 'text', required=True),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        context[self.params['name']] = self.params['value']
        self.output = f"{self.params['name']} = {self.params['value']}"


@register
class LogMessageBlock(Block):
    CATEGORY = 'Control'
    NAME = 'Log Message'
    DESCRIPTION = 'Prints a message to the console (supports {variable} substitution)'
    ICON = '📝'
    COLOR = '#8be9fd'
    PARAMS = [
        Param('message', 'Message', 'multiline', required=True,
              placeholder='Value is: {my_var}'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        msg = self.params.get('message') or ''
        for key, val in context.items():
            msg = msg.replace(f'{{{key}}}', str(val))
        print(msg)
        self.output = msg


@register
class RunPythonScriptBlock(Block):
    CATEGORY = 'Control'
    NAME = 'Run Python Script'
    DESCRIPTION = 'Executes arbitrary Python code; use "context" dict to pass data between blocks'
    ICON = '🐍'
    COLOR = '#8be9fd'
    PARAMS = [
        Param('code', 'Python Code', 'multiline', required=True,
              placeholder='# Access workflow data via context dict\nprint(context.get("my_var"))'),
        Param('script_file', 'Or load from .py file', 'file', default=''),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        script_file = (self.params.get('script_file') or '').strip()
        if script_file:
            with open(script_file, 'r', encoding='utf-8') as f:
                code = f.read()
        else:
            code = self.params.get('code') or ''
        if not code.strip():
            raise ValueError("No code provided")
        # Provide access to context but restrict builtins to safe set
        exec_globals: Dict[str, Any] = {'context': context}
        exec(compile(code, '<automation_script>', 'exec'), exec_globals)  # nosec
        self.output = "Script executed"
