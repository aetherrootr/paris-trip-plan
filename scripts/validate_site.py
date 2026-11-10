"""Validate Pages subpath links, assets and inline JavaScript."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
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
    if "paris-companion-plan.html" in names:
        raise SiteError("The retired single-file edition must not be published.")
    sources = {name: path.read_text(encoding="utf-8") for name, path in names.items()}
    documents = {name: Document(text) for name, text in sources.items()}
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

    scripts = _check_scripts(list(documents.values()), check_js)
    return {
        "html_pages": len(names), "local_links": checked,
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
