"""Validate Pages subpath links, assets, portable navigation and inline JavaScript."""
from __future__ import annotations

import argparse
import base64
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit


class SiteError(ValueError):
    """The generated site cannot be published as a self-contained artifact."""


class Document(HTMLParser):
    def __init__(self, source: str):
        super().__init__()
        self.ids: set[str] = set()
        self.references: list[str] = []
        self.scripts: list[tuple[dict, str]] = []
        self._script: dict | None = None
        self._text: list[str] = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            if values["id"] in self.ids:
                raise SiteError(f"Duplicate HTML id: {values['id']}")
            self.ids.add(values["id"])
        for attr in ("href", "src"):
            if values.get(attr):
                self.references.append(values[attr])
        if tag == "script":
            self._script = values
            self._text = []

    def handle_data(self, data):
        if self._script is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            self.scripts.append((self._script, "".join(self._text)))
            self._script = None


def _local_target(reference: str, current: str) -> tuple[str, str] | None:
    url = urlsplit(reference)
    if url.scheme == "file":
        raise SiteError(f"Machine-local URL cannot be published: {reference}")
    if url.scheme or url.netloc:
        return None
    if url.path.startswith("/"):
        raise SiteError(f"Root-relative URL breaks a Pages repository subpath: {reference}")
    target = (Path(current).parent / unquote(url.path)).as_posix() if url.path else current
    return target, unquote(url.fragment)


def _check_scripts(documents: list[Document], check_js: bool) -> int:
    scripts = []
    for document in documents:
        for attrs, text in document.scripts:
            kind = attrs.get("type", "")
            if kind == "application/json":
                json.loads(text)
            elif "src" not in attrs and kind in {"", "text/javascript", "application/javascript"}:
                scripts.append(text)
    if check_js:
        node = shutil.which("node")
        if not node:
            raise SiteError("Node.js is required when --check-js is selected.")
        with tempfile.TemporaryDirectory(prefix="paris-site-js-") as tmp:
            for index, script in enumerate(scripts):
                path = Path(tmp) / f"script-{index}.js"
                path.write_text(script, encoding="utf-8")
                result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
                if result.returncode:
                    raise SiteError(f"Inline JavaScript syntax error:\n{result.stderr}")
    return len(scripts)


def validate_site(directory: Path, check_js: bool = False) -> dict:
    root = Path(directory).resolve()
    if not (root / "index.html").is_file():
        raise SiteError("The site must contain index.html at its document root.")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SiteError(f"Pages artifacts must not contain symbolic links: {path}")
    names = {p.relative_to(root).as_posix(): p for p in root.rglob("*.html")}
    portable_name = "paris-companion-plan.html"
    sources = {name: path.read_text(encoding="utf-8") for name, path in names.items()}
    documents = {name: Document(text) for name, text in sources.items() if name != portable_name}
    checked = 0
    for name, doc in documents.items():
        for reference in doc.references:
            target = _local_target(reference, name)
            if target is None:
                continue
            file, anchor = target
            path = (root / file).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise SiteError(f"Broken link in {name}: {reference}")
            if anchor and file in documents and anchor not in documents[file].ids:
                raise SiteError(f"Missing anchor in {name}: {reference}")
            checked += 1

    bundled_pages = bundled_assets = 0
    script_documents = list(documents.values())
    if portable_name in sources:
        outer = Document(sources[portable_name])
        payloads = [text for attrs, text in outer.scripts if attrs.get("id") == "portable-data"]
        if len(payloads) != 1:
            raise SiteError("The portable HTML must contain exactly one embedded site payload.")
        bundle = json.loads(payloads[0])
        embedded = {name: Document(source) for name, source in bundle["pages"].items()}
        if set(embedded) != set(documents):
            raise SiteError("The portable HTML does not contain all published pages.")
        for name, doc in embedded.items():
            for reference in doc.references:
                if reference.startswith("portable-resource:"):
                    if reference.split(":", 1)[1] not in bundle["assets"]:
                        raise SiteError(f"Missing portable resource: {reference}")
                    continue
                target = _local_target(reference, name)
                if target is None:
                    continue
                file, anchor = target
                if file == portable_name:
                    continue
                if file not in embedded or (anchor and anchor not in embedded[file].ids):
                    raise SiteError(f"Broken portable navigation in {name}: {reference}")
        for asset in bundle["assets"].values():
            if not base64.b64decode(asset["data"], validate=True):
                raise SiteError("An embedded portable asset is empty.")
        library = bundle["leaflet"]
        if "url(images/" in library["css"]:
            raise SiteError("The portable map stylesheet still references external local images.")
        for name, source in bundle["pages"].items():
            if "<!--portable-map-library-->" in source:
                if "unpkg.com/leaflet" in source or "createElement('script')" in source:
                    raise SiteError(f"The portable map script is not inline: {name}")
                source = source.replace(
                    "<!--portable-map-library-->",
                    "<style>" + library["css"] + "</style><script>" + library["js"] + "</script>",
                )
            script_documents.append(Document(source))
        script_documents.extend([outer, Document("<script>" + bundle["bridge"].replace("__PAGE__", '"index.html"') + "</script>")])
        bundled_pages, bundled_assets = len(embedded), len(bundle["assets"])

    scripts = _check_scripts(script_documents, check_js)
    return {
        "html_pages": len(names), "local_links": checked,
        "portable_pages": bundled_pages, "portable_assets": bundled_assets,
        "inline_scripts": scripts, "javascript_checked": check_js,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path("dist"))
    parser.add_argument("--check-js", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(validate_site(args.directory, args.check_js), ensure_ascii=False))
    except (SiteError, ValueError) as error:
        parser.exit(1, f"Site validation failed: {error}\n")
