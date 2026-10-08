from __future__ import annotations
import time
from typing import Any, Dict
from .base import Block, Param
from .registry import register


@register
class OpenApplicationBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Open Application'
    DESCRIPTION = 'Launches an installed application by name or full path'
    ICON = '🖥️'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('app_path', 'Application path or name', 'text', required=True,
              placeholder='notepad.exe  or  C:\\Program Files\\...\\app.exe'),
        Param('arguments', 'Arguments (optional)', 'text', default=''),
        Param('wait_seconds', 'Wait after launch (s)', 'float', default=3.0),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import subprocess
        app = self.params['app_path']
        args = (self.params.get('arguments') or '').split()
        proc = subprocess.Popen([app] + args, shell=True)
        context['last_process'] = proc
        time.sleep(float(self.params.get('wait_seconds') or 3.0))
        self.output = f"Launched: {app}"


@register
class TypeTextBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Type Text'
    DESCRIPTION = 'Types text using the keyboard into the focused window'
    ICON = '⌨️'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('text', 'Text to type', 'multiline', required=True,
              placeholder='Hello World\n{my_variable}'),
        Param('interval', 'Delay between characters (s)', 'float', default=0.03),
        Param('wait_before', 'Wait before typing (s)', 'float', default=0.3),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        text = self.params.get('text') or ''
        for key, val in context.items():
            text = text.replace(f'{{{key}}}', str(val))
        time.sleep(float(self.params.get('wait_before') or 0.3))
        pyautogui.typewrite(text, interval=float(self.params.get('interval') or 0.03))
        self.output = f"Typed: {text[:60]}"


@register
class KeyPressBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Press Key(s)'
    DESCRIPTION = (
        'Presses keyboard keys or combos. '
        'Separate multiple combos with commas: "ctrl+c, enter, alt+f4"'
    )
    ICON = '🔑'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('keys', 'Keys to press', 'keyseq', required=True,
              placeholder='enter  or  ctrl+c  or  alt+f, down, down, enter'),
        Param('times', 'Repeat count', 'int', default=1),
        Param('delay_between', 'Delay between presses (s)', 'float', default=0.1),
        Param('wait_before', 'Wait before first press (s)', 'float', default=0.2),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import keyboard
        keys_str = self.params.get('keys') or ''
        times = int(self.params.get('times') or 1)
        delay = float(self.params.get('delay_between') or 0.1)
        time.sleep(float(self.params.get('wait_before') or 0.2))
        combos = [k.strip() for k in keys_str.split(',') if k.strip()]
        for _ in range(times):
            for combo in combos:
                keyboard.send(combo)
                time.sleep(delay)
        self.output = f"Pressed: {keys_str} ×{times}"

    def get_summary(self) -> str:
        keys = self.params.get('keys', '')
        times = self.params.get('times', 1)
        return f"{keys}  ×{times}" if keys else "Not configured"


@register
class MouseClickBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Mouse Click'
    DESCRIPTION = 'Clicks at an absolute screen coordinate'
    ICON = '🖱️'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('x', 'X coordinate', 'int', default=0),
        Param('y', 'Y coordinate', 'int', default=0),
        Param('button', 'Button', 'choice', default='left', options=['left', 'right', 'middle']),
        Param('clicks', 'Number of clicks', 'int', default=1),
        Param('wait_before', 'Wait before click (s)', 'float', default=0.2),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        x, y = int(self.params.get('x') or 0), int(self.params.get('y') or 0)
        time.sleep(float(self.params.get('wait_before') or 0.2))
        pyautogui.click(x, y, button=self.params.get('button', 'left'),
                        clicks=int(self.params.get('clicks') or 1))
        self.output = f"Clicked ({x},{y}) ×{self.params.get('clicks',1)}"


@register
class MouseMoveBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Mouse Move'
    DESCRIPTION = 'Moves the mouse cursor to a position'
    ICON = '➡️'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('x', 'X coordinate', 'int', default=0),
        Param('y', 'Y coordinate', 'int', default=0),
        Param('duration', 'Move duration (s)', 'float', default=0.4),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        pyautogui.moveTo(int(self.params['x']), int(self.params['y']),
                         duration=float(self.params.get('duration') or 0.4))
        self.output = f"Moved to ({self.params['x']}, {self.params['y']})"


@register
class MouseDragBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Mouse Drag'
    DESCRIPTION = 'Drags from one screen coordinate to another'
    ICON = '↔️'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('x1', 'From X', 'int', default=0),
        Param('y1', 'From Y', 'int', default=0),
        Param('x2', 'To X', 'int', default=100),
        Param('y2', 'To Y', 'int', default=100),
        Param('duration', 'Duration (s)', 'float', default=0.5),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        pyautogui.moveTo(int(self.params['x1']), int(self.params['y1']))
        pyautogui.dragTo(int(self.params['x2']), int(self.params['y2']),
                         duration=float(self.params.get('duration') or 0.5), button='left')
        self.output = f"Dragged ({self.params['x1']},{self.params['y1']}) → ({self.params['x2']},{self.params['y2']})"


@register
class InputCredentialsBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Input Credentials'
    DESCRIPTION = 'Types a username, presses a separator key, then types the password'
    ICON = '🔐'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('username', 'Username', 'text', required=True),
        Param('password', 'Password', 'password', required=True),
        Param('username_key', 'Key after username', 'text', default='tab',
              placeholder='tab or enter'),
        Param('password_key', 'Key after password', 'text', default='enter'),
        Param('wait_before', 'Wait before typing (s)', 'float', default=0.5),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        time.sleep(float(self.params.get('wait_before') or 0.5))
        pyautogui.typewrite(self.params['username'], interval=0.04)
        u_key = (self.params.get('username_key') or 'tab').strip()
        if u_key:
            pyautogui.press(u_key)
        time.sleep(0.2)
        pyautogui.typewrite(self.params['password'], interval=0.04)
        p_key = (self.params.get('password_key') or 'enter').strip()
        if p_key:
            pyautogui.press(p_key)
        self.output = f"Credentials entered for: {self.params['username']}"


@register
class ScrollBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Scroll'
    DESCRIPTION = 'Scrolls up or down at the current or specified position'
    ICON = '🔄'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('direction', 'Direction', 'choice', default='down',
              options=['up', 'down', 'left', 'right']),
        Param('amount', 'Scroll amount (clicks)', 'int', default=3),
        Param('x', 'X position (0 = use current)', 'int', default=0),
        Param('y', 'Y position (0 = use current)', 'int', default=0),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        direction = self.params.get('direction', 'down')
        amount = int(self.params.get('amount') or 3)
        x = int(self.params.get('x') or 0) or None
        y = int(self.params.get('y') or 0) or None
        if direction == 'down':
            pyautogui.scroll(-amount, x=x, y=y)
        elif direction == 'up':
            pyautogui.scroll(amount, x=x, y=y)
        elif direction == 'right':
            pyautogui.hscroll(amount, x=x, y=y)
        else:
            pyautogui.hscroll(-amount, x=x, y=y)
        self.output = f"Scrolled {direction} ×{amount}"


@register
class WindowFocusBlock(Block):
    CATEGORY = 'App Automation'
    NAME = 'Focus Window'
    DESCRIPTION = 'Brings a window with a given title to the foreground (Windows only)'
    ICON = '🪟'
    COLOR = '#bd93f9'
    PARAMS = [
        Param('title', 'Window title (partial match)', 'text', required=True,
              placeholder='Notepad'),
        Param('wait_seconds', 'Wait after focus (s)', 'float', default=0.5),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(self.params['title'])
            if not windows:
                raise RuntimeError(f"No window found matching '{self.params['title']}'")
            windows[0].activate()
            time.sleep(float(self.params.get('wait_seconds') or 0.5))
            self.output = f"Focused: {windows[0].title}"
        except ImportError:
            raise ImportError("pygetwindow not installed. Run: pip install pygetwindow")
