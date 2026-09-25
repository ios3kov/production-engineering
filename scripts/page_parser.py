"""Adapted from Production Auditor (MIT); see upstream license/provenance."""
from html.parser import HTMLParser

class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self.lang = ""
        self.description = ""
        self.canonical = ""
        self.viewport = ""
        self.robots = ""
        self.og_title = ""
        self.h1 = 0
        self.links: list[str] = []
        self.images_missing_alt = 0
        self.forms = 0
        self.third_party_scripts: list[str] = []
        self.insecure_resources: list[str] = []
        self.password_forms = 0

    def handle_starttag(self, tag: str, attrs_list):
        attrs = {str(k).lower(): (v or "") for k, v in attrs_list}
        tag = tag.lower()
        if tag == "html":
            self.lang = attrs.get("lang", "")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs.get("name", "").lower()
            prop = attrs.get("property", "").lower()
            if name == "description":
                self.description = attrs.get("content", "")
            elif name == "viewport":
                self.viewport = attrs.get("content", "")
            elif name == "robots":
                self.robots = attrs.get("content", "")
            elif prop == "og:title":
                self.og_title = attrs.get("content", "")
        elif tag == "link" and "canonical" in attrs.get("rel", "").lower():
            self.canonical = attrs.get("href", "")
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img" and "alt" not in attrs:
            self.images_missing_alt += 1
        elif tag == "form":
            self.forms += 1
        elif tag == "input" and attrs.get("type", "").lower() == "password":
            self.password_forms += 1
        elif tag == "script" and attrs.get("src"):
            src = attrs["src"]
            self.third_party_scripts.append(src)
            if src.startswith("http://"):
                self.insecure_resources.append(src)
        elif tag in {"img", "iframe", "link"}:
            src = attrs.get("src") or attrs.get("href") or ""
            if src.startswith("http://"):
                self.insecure_resources.append(src)

    def handle_endtag(self, tag: str):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str):
        if self._in_title:
            self.title += data.strip()
