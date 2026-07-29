from __future__ import annotations
import time
from threading import Thread, Event
from typing import Callable, Dict, List, Any, Optional


class ActionRecorder:
    """
    Records mouse clicks and keyboard presses via pynput.
    Call start() / stop() from the GUI.  stop() returns the raw action list.
    Use actions_to_block_dicts() to convert them into block data for a Workflow.
    """

    def __init__(self, on_action: Optional[Callable[[Dict], None]] = None):
        self._on_action = on_action          # optional real-time callback
        self._stop_event = Event()
        self._actions: List[Dict[str, Any]] = []
        self._start_time: float = 0.0
        self._thread: Optional[Thread] = None
        self.is_recording: bool = False

    def start(self) -> None:
        if self.is_recording:
            return
        self._actions.clear()
        self._stop_event.clear()
        self._start_time = time.time()
        self.is_recording = True
        self._thread = Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop(self) -> List[Dict[str, Any]]:
        self.is_recording = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        return list(self._actions)

    # ------------------------------------------------------------------ #
    # Internal recording loop (runs in daemon thread)
    # ------------------------------------------------------------------ #
    def _record_loop(self) -> None:
        try:
            from pynput import mouse, keyboard

            t0 = self._start_time

            def _ts() -> float:
                return round(time.time() - t0, 3)

            def on_click(x: int, y: int, button, pressed: bool):
                if not self.is_recording:
                    return False
                if pressed:
                    action = {'type': 'mouse_click', 'x': x, 'y': y,
                              'button': button.name, 'time': _ts()}
                    self._actions.append(action)
                    if self._on_action:
                        self._on_action(action)

            def on_press(key):
                if not self.is_recording:
                    return False
                try:
                    char = key.char
                    k = char if char else str(key)
                except AttributeError:
                    k = str(key).replace('Key.', '')
                action = {'type': 'key_press', 'key': k, 'time': _ts()}
                self._actions.append(action)
                if self._on_action:
                    self._on_action(action)

            m_listener = mouse.Listener(on_click=on_click)
            k_listener = keyboard.Listener(on_press=on_press)
            m_listener.start()
            k_listener.start()
            self._stop_event.wait()
            m_listener.stop()
            k_listener.stop()

        except ImportError:
            # pynput not available – silently return
            self._stop_event.wait()

    # ------------------------------------------------------------------ #
    # Convert raw actions → block dicts
    # ------------------------------------------------------------------ #
    def actions_to_block_dicts(self) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        last_time = 0.0
        actions = self._actions
        i = 0

        while i < len(actions):
            action = actions[i]
            delay = action['time'] - last_time

            # Insert a Wait block for gaps > 0.5 s
            if delay > 0.5 and blocks:
                blocks.append({'type': 'WaitBlock',
                                'params': {'seconds': round(delay, 1)}})

            if action['type'] == 'mouse_click':
                blocks.append({
                    'type': 'MouseClickBlock',
                    'params': {
                        'x': action['x'], 'y': action['y'],
                        'button': action['button'], 'clicks': 1,
                    },
                })

            elif action['type'] == 'key_press':
                # Try to group consecutive single-character keys into a TypeText block
                chars: List[str] = []
                j = i
                while j < len(actions) and actions[j]['type'] == 'key_press':
                    k = actions[j]['key']
                    if len(k) == 1:
                        chars.append(k)
                        j += 1
                    else:
                        break

                if len(chars) > 1:
                    blocks.append({'type': 'TypeTextBlock',
                                   'params': {'text': ''.join(chars)}})
                    i = j - 1          # skip consumed actions
                else:
                    blocks.append({'type': 'KeyPressBlock',
                                   'params': {'keys': action['key'], 'times': 1}})

            last_time = action['time']
            i += 1

        return blocks
