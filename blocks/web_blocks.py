from __future__ import annotations
import time
from typing import Any, Dict
from .base import Block, Param
from .registry import register


def _get_driver(context: Dict[str, Any]):
    driver = context.get('web_driver')
    if driver is None:
        raise RuntimeError(
            "No browser driver in context. Add an 'Open URL' block (with a browser, not 'requests') first."
        )
    return driver


@register
class OpenURLBlock(Block):
    CATEGORY = 'Web'
    NAME = 'Open URL'
    DESCRIPTION = 'Opens a URL. Use "requests" for simple scraping or a real browser for JavaScript pages.'
    ICON = '🌐'
    COLOR = '#ff79c6'
    PARAMS = [
        Param('url', 'URL', 'text', required=True, placeholder='https://example.com'),
        Param('browser', 'Backend', 'choice', default='chrome',
              options=['chrome', 'firefox', 'edge', 'requests']),
        Param('headless', 'Headless (no window)', 'bool', default=False),
        Param('wait_seconds', 'Wait after load (s)', 'float', default=2.0),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        url = self.params['url']
        browser = self.params.get('browser', 'chrome')
        headless = bool(self.params.get('headless'))
        wait = float(self.params.get('wait_seconds') or 2.0)

        if browser == 'requests':
            import requests
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            context['web_content'] = resp.text
            context['web_url'] = url
            self.output = f"Fetched {url} ({len(resp.text)} chars)"
        else:
            from selenium import webdriver
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.firefox import GeckoDriverManager
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.chrome.service import Service as CS
            from selenium.webdriver.firefox.service import Service as FS
            from selenium.webdriver.edge.service import Service as ES

            if browser == 'chrome':
                opts = webdriver.ChromeOptions()
                if headless:
                    opts.add_argument('--headless=new')
                opts.add_argument('--no-sandbox')
                opts.add_argument('--disable-dev-shm-usage')
                driver = webdriver.Chrome(service=CS(ChromeDriverManager().install()), options=opts)
            elif browser == 'firefox':
                opts = webdriver.FirefoxOptions()
                if headless:
                    opts.add_argument('--headless')
                driver = webdriver.Firefox(service=FS(GeckoDriverManager().install()), options=opts)
            else:
                opts = webdriver.EdgeOptions()
                if headless:
                    opts.add_argument('--headless')
                driver = webdriver.Edge(service=ES(EdgeChromiumDriverManager().install()), options=opts)

            driver.get(url)
            time.sleep(wait)
            context['web_driver'] = driver
            context['web_url'] = url
            self.output = f"Opened {url} in {browser}"

    def get_summary(self) -> str:
        url = self.params.get('url', '')
        br = self.params.get('browser', 'chrome')
        return f"{url}  [{br}]" if url else "Not configured"


@register
class ExtractTextBlock(Block):
    CATEGORY = 'Web'
    NAME = 'Extract Text'
    DESCRIPTION = 'Extracts text content from page elements using a CSS selector or XPath'
    ICON = '📤'
    COLOR = '#ff79c6'
    PARAMS = [
        Param('selector', 'CSS Selector or XPath', 'text', required=True,
              placeholder='.class-name  or  //div[@id="main"]'),
        Param('selector_type', 'Type', 'choice', default='css', options=['css', 'xpath']),
        Param('multiple', 'Extract all matches (returns list)', 'bool', default=False),
        Param('output_variable', 'Store result in variable', 'text', default='extracted_text'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        selector = self.params['selector']
        sel_type = self.params.get('selector_type', 'css')
        multiple = bool(self.params.get('multiple'))
        var = self.params.get('output_variable') or 'extracted_text'

        driver = context.get('web_driver')
        if driver:
            from selenium.webdriver.common.by import By
            by = By.CSS_SELECTOR if sel_type == 'css' else By.XPATH
            if multiple:
                result = [e.text for e in driver.find_elements(by, selector)]
            else:
                result = driver.find_element(by, selector).text
        elif 'web_content' in context:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context['web_content'], 'lxml')
            if sel_type == 'css':
                if multiple:
                    result = [e.get_text(strip=True) for e in soup.select(selector)]
                else:
                    el = soup.select_one(selector)
                    result = el.get_text(strip=True) if el else ''
            else:
                import lxml.etree as etree
                tree = etree.fromstring(context['web_content'].encode(), etree.HTMLParser())
                els = tree.xpath(selector)
                if multiple:
                    result = [e.text_content() for e in els]
                else:
                    result = els[0].text_content() if els else ''
        else:
            raise RuntimeError("No web driver or content available. Add an 'Open URL' block first.")

        context[var] = result
        self.output = f"Extracted: {str(result)[:120]}"


@register
class ExtractTableBlock(Block):
    CATEGORY = 'Web'
    NAME = 'Extract HTML Table'
    DESCRIPTION = 'Extracts an HTML table from the current page as a DataFrame'
    ICON = '📋'
    COLOR = '#ff79c6'
    PARAMS = [
        Param('table_index', 'Table index (0 = first)', 'int', default=0),
        Param('output_variable', 'Store result in variable', 'text', default='table_data'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pandas as pd
        driver = context.get('web_driver')
        content = driver.page_source if driver else context.get('web_content', '')
        if not content:
            raise RuntimeError("No web content available")
        tables = pd.read_html(content)
        idx = int(self.params.get('table_index') or 0)
        if idx >= len(tables):
            raise IndexError(f"Table index {idx} out of range (found {len(tables)})")
        var = self.params.get('output_variable') or 'table_data'
        context[var] = tables[idx]
        self.output = f"Extracted table {idx}: {len(tables[idx])} rows"


@register
class ClickWebElementBlock(Block):
    CATEGORY = 'Web'
    NAME = 'Click Web Element'
    DESCRIPTION = 'Clicks an element on the current browser page'
    ICON = '👆'
    COLOR = '#ff79c6'
    PARAMS = [
        Param('selector', 'CSS Selector or XPath', 'text', required=True),
        Param('selector_type', 'Type', 'choice', default='css', options=['css', 'xpath']),
        Param('wait_seconds', 'Wait before click (s)', 'float', default=0.5),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        from selenium.webdriver.common.by import By
        driver = _get_driver(context)
        time.sleep(float(self.params.get('wait_seconds') or 0.5))
        by = By.CSS_SELECTOR if self.params.get('selector_type') == 'css' else By.XPATH
        driver.find_element(by, self.params['selector']).click()
        self.output = f"Clicked: {self.params['selector']}"


@register
class FillWebFormBlock(Block):
    CATEGORY = 'Web'
    NAME = 'Fill Web Form Field'
    DESCRIPTION = 'Types text into a form input on the browser page'
    ICON = '✏️'
    COLOR = '#ff79c6'
    PARAMS = [
        Param('selector', 'CSS Selector or XPath', 'text', required=True),
        Param('selector_type', 'Type', 'choice', default='css', options=['css', 'xpath']),
        Param('value', 'Value to enter', 'text', required=True),
        Param('clear_first', 'Clear field first', 'bool', default=True),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        from selenium.webdriver.common.by import By
        driver = _get_driver(context)
        by = By.CSS_SELECTOR if self.params.get('selector_type') == 'css' else By.XPATH
        el = driver.find_element(by, self.params['selector'])
        if self.params.get('clear_first', True):
            el.clear()
        el.send_keys(self.params['value'])
        self.output = f"Filled '{self.params['selector']}'"


@register
class CloseBrowserBlock(Block):
    CATEGORY = 'Web'
    NAME = 'Close Browser'
    DESCRIPTION = 'Closes the Selenium browser window and releases resources'
    ICON = '❌'
    COLOR = '#ff79c6'
    PARAMS = []

    def execute(self, context: Dict[str, Any]) -> None:
        driver = context.pop('web_driver', None)
        if driver:
            driver.quit()
            self.output = "Browser closed"
        else:
            self.output = "No browser was open"
