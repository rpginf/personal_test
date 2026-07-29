from __future__ import annotations
from typing import Any, Dict
from .base import Block, Param
from .registry import register


@register
class TakeScreenshotBlock(Block):
    CATEGORY = 'Computer Vision'
    NAME = 'Take Screenshot'
    DESCRIPTION = 'Captures the screen (or a region) and stores it as a PIL image'
    ICON = '📸'
    COLOR = '#ffb86c'
    PARAMS = [
        Param('save_path', 'Save to file (optional)', 'file_save', default=''),
        Param('region', 'Region x,y,w,h (empty = full screen)', 'text', default='',
              placeholder='0,0,1920,1080'),
        Param('output_variable', 'Store image in variable', 'text', default='screenshot'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        region_str = (self.params.get('region') or '').strip()
        region = None
        if region_str:
            parts = [int(v.strip()) for v in region_str.split(',')]
            if len(parts) == 4:
                region = tuple(parts)
        img = pyautogui.screenshot(region=region)
        save_path = (self.params.get('save_path') or '').strip()
        if save_path:
            img.save(save_path)
        var = self.params.get('output_variable') or 'screenshot'
        context[var] = img
        self.output = f"Screenshot {img.size[0]}×{img.size[1]}" + (f" → {save_path}" if save_path else "")


@register
class FindImageOnScreenBlock(Block):
    CATEGORY = 'Computer Vision'
    NAME = 'Find Image on Screen'
    DESCRIPTION = 'Locates a template image on the current screen using template matching'
    ICON = '🔍'
    COLOR = '#ffb86c'
    PARAMS = [
        Param('template_image', 'Template image file', 'file', required=True),
        Param('confidence', 'Confidence (0–1)', 'float', default=0.8),
        Param('grayscale', 'Grayscale matching (faster)', 'bool', default=False),
        Param('output_variable', 'Store location in variable', 'text', default='found_location'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        template = self.params['template_image']
        confidence = float(self.params.get('confidence') or 0.8)
        grayscale = bool(self.params.get('grayscale'))
        location = pyautogui.locateOnScreen(template, confidence=confidence, grayscale=grayscale)
        if location is None:
            raise RuntimeError(f"Template image not found on screen: {template}")
        center = pyautogui.center(location)
        var = self.params.get('output_variable') or 'found_location'
        context[var] = {'box': location, 'center': center, 'x': center.x, 'y': center.y}
        self.output = f"Found at ({center.x}, {center.y})"


@register
class ClickImageOnScreenBlock(Block):
    CATEGORY = 'Computer Vision'
    NAME = 'Find & Click Image'
    DESCRIPTION = 'Finds a template image on screen and clicks its centre'
    ICON = '👆'
    COLOR = '#ffb86c'
    PARAMS = [
        Param('template_image', 'Template image file', 'file', required=True),
        Param('confidence', 'Confidence (0–1)', 'float', default=0.8),
        Param('button', 'Mouse button', 'choice', default='left',
              options=['left', 'right', 'double']),
        Param('offset_x', 'X offset from centre', 'int', default=0),
        Param('offset_y', 'Y offset from centre', 'int', default=0),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pyautogui
        template = self.params['template_image']
        confidence = float(self.params.get('confidence') or 0.8)
        location = pyautogui.locateOnScreen(template, confidence=confidence)
        if location is None:
            raise RuntimeError(f"Image not found: {template}")
        center = pyautogui.center(location)
        x = center.x + int(self.params.get('offset_x') or 0)
        y = center.y + int(self.params.get('offset_y') or 0)
        btn = self.params.get('button', 'left')
        if btn == 'double':
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.click(x, y, button=btn)
        self.output = f"Clicked image at ({x}, {y})"


@register
class OCRTextBlock(Block):
    CATEGORY = 'Computer Vision'
    NAME = 'OCR Extract Text'
    DESCRIPTION = 'Extracts text from a screenshot or image file using Tesseract OCR'
    ICON = '🔤'
    COLOR = '#ffb86c'
    PARAMS = [
        Param('image_variable', 'Screenshot variable (or leave empty for new screenshot)', 'text',
              default='screenshot'),
        Param('image_path', 'Or image file path', 'file', default=''),
        Param('language', 'Language code', 'text', default='eng',
              placeholder='eng, deu, fra, ...'),
        Param('output_variable', 'Store text in variable', 'text', default='ocr_text'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        try:
            import pytesseract
        except ImportError:
            raise ImportError("pytesseract not installed. Run: pip install pytesseract")
        from PIL import Image
        image_path = (self.params.get('image_path') or '').strip()
        if image_path:
            img = Image.open(image_path)
        else:
            var = self.params.get('image_variable') or 'screenshot'
            img = context.get(var)
            if img is None:
                import pyautogui
                img = pyautogui.screenshot()
        lang = self.params.get('language') or 'eng'
        text = pytesseract.image_to_string(img, lang=lang)
        var_out = self.params.get('output_variable') or 'ocr_text'
        context[var_out] = text
        self.output = f"Extracted {len(text)} characters"


@register
class WaitForImageBlock(Block):
    CATEGORY = 'Computer Vision'
    NAME = 'Wait for Image to Appear'
    DESCRIPTION = 'Polls the screen until a template image is found (up to a timeout)'
    ICON = '⏳'
    COLOR = '#ffb86c'
    PARAMS = [
        Param('template_image', 'Template image file', 'file', required=True),
        Param('confidence', 'Confidence (0–1)', 'float', default=0.8),
        Param('timeout', 'Timeout (s)', 'float', default=30.0),
        Param('poll_interval', 'Poll interval (s)', 'float', default=1.0),
        Param('output_variable', 'Store location in variable', 'text', default='found_location'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import time
        import pyautogui
        template = self.params['template_image']
        confidence = float(self.params.get('confidence') or 0.8)
        timeout = float(self.params.get('timeout') or 30.0)
        poll = float(self.params.get('poll_interval') or 1.0)
        start = time.time()
        while time.time() - start < timeout:
            location = pyautogui.locateOnScreen(template, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                var = self.params.get('output_variable') or 'found_location'
                context[var] = {'box': location, 'center': center, 'x': center.x, 'y': center.y}
                self.output = f"Found after {time.time()-start:.1f}s at ({center.x},{center.y})"
                return
            time.sleep(poll)
        raise TimeoutError(f"Image not found within {timeout}s: {template}")
