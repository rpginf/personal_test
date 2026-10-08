from __future__ import annotations
from typing import Dict

# ─────────────────────────────────────────────────────────────────────────────
# Theme definitions
# ─────────────────────────────────────────────────────────────────────────────
THEMES: Dict[str, Dict[str, str]] = {
    "Catppuccin Mocha": {
        "bg": "#11111b", "surface": "#1e1e2e", "surface2": "#2a2a3e",
        "overlay": "#313244", "overlay2": "#45475a", "muted": "#6c7086",
        "text": "#cdd6f4", "subtext": "#a6adc8", "accent": "#7c6af7",
        "green": "#50fa7b", "green_h": "#69ff94", "green_p": "#3dd668",
        "red": "#ff5555", "red_h": "#ff6e6e",
        "purple": "#bd93f9", "purple_h": "#caa8ff",
        "toolbar_bg": "#181825", "btn_text": "#1e1e2e",
    },
    "Dracula": {
        "bg": "#1e1f29", "surface": "#282a36", "surface2": "#343746",
        "overlay": "#44475a", "overlay2": "#6272a4", "muted": "#6272a4",
        "text": "#f8f8f2", "subtext": "#bfc9d4", "accent": "#bd93f9",
        "green": "#50fa7b", "green_h": "#69ff94", "green_p": "#3dd668",
        "red": "#ff5555", "red_h": "#ff7070",
        "purple": "#bd93f9", "purple_h": "#d0a8ff",
        "toolbar_bg": "#21222c", "btn_text": "#282a36",
    },
    "One Dark": {
        "bg": "#1a1d23", "surface": "#21252b", "surface2": "#2c313a",
        "overlay": "#3e4451", "overlay2": "#4b5263", "muted": "#5c6370",
        "text": "#abb2bf", "subtext": "#828997", "accent": "#61afef",
        "green": "#98c379", "green_h": "#afd492", "green_p": "#7db360",
        "red": "#e06c75", "red_h": "#e88890",
        "purple": "#c678dd", "purple_h": "#d49ae8",
        "toolbar_bg": "#191d22", "btn_text": "#1a1d23",
    },
    "Catppuccin Latte": {
        "bg": "#eff1f5", "surface": "#e6e9ef", "surface2": "#dce0e8",
        "overlay": "#ccd0da", "overlay2": "#bcc0cc", "muted": "#9ca0b0",
        "text": "#4c4f69", "subtext": "#5c5f77", "accent": "#7287fd",
        "green": "#40a02b", "green_h": "#5ab53e", "green_p": "#2e8a1e",
        "red": "#d20f39", "red_h": "#e63050",
        "purple": "#8839ef", "purple_h": "#9e50f5",
        "toolbar_bg": "#dce0e8", "btn_text": "#eff1f5",
    },
}

FONT_SIZES: Dict[str, int] = {"Small": 11, "Medium": 13, "Large": 16, "X-Large": 19}
DEFAULT_THEME = "Catppuccin Mocha"
DEFAULT_FONT_SIZE = "Medium"


# ─────────────────────────────────────────────────────────────────────────────
# Style builders
# ─────────────────────────────────────────────────────────────────────────────
def make_app_style(c: Dict[str, str], fs: int) -> str:
    sm = max(fs - 2, 9)
    return f"""
QMainWindow, QWidget {{ background:{c['bg']}; color:{c['text']}; font-size:{fs}px; }}
QDockWidget {{ background:{c['surface']}; color:{c['text']}; font-weight:bold; }}
QDockWidget::title {{ background:{c['surface2']}; padding:6px; color:{c['text']}; }}
QMenuBar {{ background:{c['surface']}; color:{c['text']}; font-size:{fs}px;
            border-bottom:1px solid {c['overlay']}; }}
QMenuBar::item:selected {{ background:{c['overlay']}; }}
QMenu {{ background:{c['surface']}; color:{c['text']}; border:1px solid {c['overlay']};
         font-size:{fs}px; }}
QMenu::item:selected {{ background:{c['overlay2']}; }}
QMenu::item:disabled {{ color:{c['muted']}; }}
QToolBar {{ background:{c['toolbar_bg']}; border-bottom:1px solid {c['overlay']};
            spacing:4px; padding:2px 4px; }}
QToolBar QPushButton {{
    background:transparent; color:{c['text']};
    border:none; border-radius:4px;
    padding:4px 10px; font-size:{fs}px;
}}
QToolBar QPushButton:hover {{ background:{c['overlay']}; }}
QStatusBar {{ background:{c['surface']}; color:{c['muted']}; font-size:{sm}px;
              border-top:1px solid {c['overlay']}; }}
QSplitter::handle {{ background:{c['overlay']}; }}
QScrollBar:vertical {{ background:{c['surface']}; width:8px; border-radius:4px; margin:0; }}
QScrollBar::handle:vertical {{ background:{c['overlay2']}; border-radius:4px; min-height:20px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{ background:{c['surface']}; height:8px; border-radius:4px; margin:0; }}
QScrollBar::handle:horizontal {{ background:{c['overlay2']}; border-radius:4px; min-width:20px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background:{c['bg']}; color:{c['text']};
    border:1px solid {c['overlay2']}; border-radius:4px;
    padding:3px 6px; font-size:{fs}px;
}}
QSpinBox, QDoubleSpinBox {{ padding-right:18px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin:border; subcontrol-position:top right;
    width:16px; border-left:1px solid {c['overlay2']};
    background:{c['surface2']}; border-top-right-radius:3px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin:border; subcontrol-position:bottom right;
    width:16px; border-left:1px solid {c['overlay2']};
    background:{c['surface2']}; border-bottom-right-radius:3px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background:{c['overlay']};
}}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background:{c['overlay2']};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ width:6px; height:6px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ width:6px; height:6px; }}
QLineEdit:focus, QTextEdit:focus {{ border-color:{c['accent']}; }}
QComboBox::drop-down {{ border:none; }}
QComboBox QAbstractItemView {{
    background:{c['surface']}; color:{c['text']};
    selection-background-color:{c['overlay2']};
}}
QCheckBox {{ color:{c['text']}; font-size:{fs}px; }}
QCheckBox::indicator {{
    width:14px; height:14px;
    border:1px solid {c['overlay2']}; border-radius:3px; background:{c['bg']};
}}
QCheckBox::indicator:checked {{ background:{c['accent']}; border-color:{c['accent']}; }}
QTreeWidget {{ background:{c['bg']}; color:{c['text']}; border:none; font-size:{fs}px; }}
QTreeWidget::item {{ padding:3px 4px; border-radius:3px; }}
QTreeWidget::item:hover {{ background:{c['surface2']}; }}
QTreeWidget::item:selected {{ background:{c['overlay2']}; color:{c['text']}; }}
QHeaderView::section {{ background:{c['surface']}; color:{c['text']}; border:none; padding:4px; }}
QDialog {{ background:{c['surface']}; color:{c['text']}; font-size:{fs}px; }}
QDialogButtonBox QPushButton {{
    background:{c['overlay']}; color:{c['text']};
    border:1px solid {c['overlay2']}; border-radius:4px;
    padding:6px 16px; font-size:{fs}px;
}}
QDialogButtonBox QPushButton:hover {{ background:{c['overlay2']}; }}
"""


def make_btn_run(c: Dict[str, str], fs: int) -> str:
    return f"""
    QPushButton {{ background:{c['green']}; color:{c['btn_text']}; border:none; border-radius:4px;
                  padding:5px 18px; font-size:{fs}px; font-weight:bold; }}
    QPushButton:hover  {{ background:{c['green_h']}; }}
    QPushButton:pressed{{ background:{c['green_p']}; }}
    QPushButton:disabled{{ background:{c['surface']}; color:{c['muted']};
                           border:1px solid {c['overlay']}; }}
"""


def make_btn_stop(c: Dict[str, str], fs: int) -> str:
    return f"""
    QPushButton {{ background:{c['red']}; color:#fff; border:none; border-radius:4px;
                  padding:5px 18px; font-size:{fs}px; font-weight:bold; }}
    QPushButton:hover  {{ background:{c['red_h']}; }}
    QPushButton:disabled{{ background:{c['surface']}; color:{c['muted']};
                           border:1px solid {c['overlay']}; }}
"""


def make_btn_rec(c: Dict[str, str], fs: int) -> str:
    return f"""
    QPushButton {{ background:{c['purple']}; color:{c['btn_text']}; border:none; border-radius:4px;
                  padding:5px 14px; font-size:{fs}px; font-weight:bold; }}
    QPushButton:hover {{ background:{c['purple_h']}; }}
"""
