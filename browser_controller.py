from typing import List, Dict, Any, Tuple
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
from config import MAX_PAGE_TEXT_CHARS, MAX_ELEMENTS, MAX_INPUT_ELEMENTS


class BrowserController:
    def __init__(self, user_data_dir: str = "user_data"):
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            locale="ru-RU",
        )
        self.page: Page = self.context.pages[0] if self.context.pages else self.context.new_page()

        self.context.set_default_timeout(15000)
        self.context.set_default_navigation_timeout(20000)

        self.current_elements = []
        self.current_inputs = []
        
    def _sync_to_latest_page(self) -> None:
        try:
            pages = [p for p in self.context.pages if not p.is_closed()]
        except Exception:
            return

        if not pages:
            return

        latest = pages[-1]
        if latest is not self.page:
            self.page = latest

    
    def goto(self, url: str):
        self.page.goto(url, wait_until="networkidle", timeout=10000)

    def click_by_element_index(self, index: int):
        if index < 0 or index >= len(self.current_elements):
            raise IndexError(f"Element index {index} is out of range")

        element = self.current_elements[index]
        locator = self.page.locator(element["selector"]).nth(element["nth"])

        locator.click(timeout=10000)
        self.page.wait_for_timeout(5000)

    
    def type_text(self, selector: str, text: str, press_enter: bool = False):
        loc = self.page.locator(selector).first
        loc.click()
        loc.fill("")
        loc.type(text)
        if press_enter:
            loc.press("Enter")

    def press_key(self, key: str):
        self.page.keyboard.press(key)

    def type_into_input_index(self, index: int, text: str, press_enter: bool = False):
        if index < 0 or index >= len(self.current_inputs):
            raise IndexError(f"Input index {index} is out of range")

        meta = self.current_inputs[index]
        locator = self.page.locator("input, textarea").nth(meta["index"])

        locator.click()
        locator.fill(text)

        if press_enter:
            locator.press("Enter")
            self.page.wait_for_timeout(1500)
        self.page.wait_for_timeout(300)


    def get_observation(self) -> Dict[str, Any]:
        self._sync_to_latest_page()
        try:
            url = self.page.url
        except Exception:
            url = "about:blank"
        try:
            title = self.page.title()
        except Exception:
            title = ""
        try:
            html = self.page.content()
        except Exception:
            html = ""

        soup = BeautifulSoup(html or "", "html.parser")

        body_text = " ".join(soup.stripped_strings)
        if len(body_text) > MAX_PAGE_TEXT_CHARS:
            body_text = body_text[:MAX_PAGE_TEXT_CHARS] + "…"

        elements: List[Dict[str, Any]] = []

        def add_clickables(root_locator):
            nonlocal elements

            try:
                clickable_loc = root_locator.locator(
                    "a, button, [role=button], input[type=submit], input[type=button]"
                )
                raw_count = clickable_loc.count()
            except Exception:
                return
            for i in range(raw_count):
                if len(elements) >= MAX_ELEMENTS:
                    break
                el = clickable_loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                except Exception:
                    continue

                try:
                    text = el.inner_text().strip()
                except Exception:
                    text = ""

                if not text:
                    label = el.get_attribute("aria-label") or el.get_attribute("title")
                    if label:
                        text = label.strip()

                href = el.get_attribute("href")
                try:
                    tag = el.evaluate("el => el.tagName.toLowerCase()")
                except Exception:
                    tag = "unknown"

                selector = (
                    "a, button, [role=button], input[type=submit], input[type=button]"
                )

                elements.append(
                    {
                        "index": len(elements),
                        "tag": tag,
                        "text": text[:120],
                        "href": href,
                        "selector": selector,
                        "nth": i,
                    }
                )

        try:
            overlay_loc = self.page.locator("[role=dialog], [aria-modal='true']")
            if overlay_loc.count() > 0:
                add_clickables(overlay_loc.nth(0))
        except Exception:
            pass
        if len(elements) < MAX_ELEMENTS:
            add_clickables(self.page)

        for idx, el in enumerate(elements):
            el["index"] = idx
        elements = elements[:MAX_ELEMENTS]

        self.current_elements = elements

        input_elements: List[Dict[str, Any]] = []
        try:
            input_loc = self.page.locator("input, textarea")
            input_count = min(input_loc.count(), MAX_INPUT_ELEMENTS)

            for i in range(input_count):
                el = input_loc.nth(i)
                input_type = (el.get_attribute("type") or "").lower()
                if input_type in ("hidden", "submit", "button", "image"):
                    continue
                try:
                    if not el.is_visible():
                        continue
                except Exception:
                    pass

                placeholder = el.get_attribute("placeholder") or ""
                name = el.get_attribute("name") or ""
                try:
                    label_text = el.evaluate(
                        """el => {
                            if (el.labels && el.labels.length > 0) {
                                return el.labels[0].innerText;
                            }
                            return "";
                        }"""
                    ) or ""
                except Exception:
                    label_text = ""

                input_elements.append(
                    {
                        "index": len(input_elements),
                        "type": input_type,
                        "placeholder": placeholder[:120],
                        "name": name[:120],
                        "label": label_text.strip()[:120],
                    }
                )
        except Exception:
            input_elements = []

        self.current_inputs = input_elements

        return {
            "url": url,
            "title": title,
            "body_text": body_text,
            "clickable_elements": elements,
            "input_elements": input_elements,
        }