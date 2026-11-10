"""Build a standalone static document root for GitHub Pages, without network access."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from build_daily import build
from scripts.validate_site import validate_site


def build_pages(output: Path = ROOT / "dist") -> dict:
    output = output.resolve()
    relative = output.relative_to(ROOT)
    if len(relative.parts) != 1 or relative.name in {
        "assets", "data", "templates", "vendor", "archive", "exports", "web",
        "scripts", "tests", "docs", "review",
    } or relative.name.startswith("."):
        raise ValueError("Choose a dedicated top-level output directory, such as dist.")
    if output.is_symlink():
        raise ValueError("The publication directory must not be a symbolic link.")

    manifest = build()
    source = ROOT / "web/current"
    with tempfile.TemporaryDirectory(prefix=".pages-build-", dir=ROOT) as tmp:
        staging = Path(tmp) / "site"
        staging.mkdir()
        # Publish rendered content and its assets, rather than the repository.
        for item in sorted(source.iterdir()):
            if item.is_symlink():
                raise ValueError(f"Cannot publish a symbolic link: {item}")
            if item.name == "assets":
                for asset in item.rglob("*"):
                    if asset.is_symlink():
                        raise ValueError(f"Cannot publish a symbolic link: {asset}")
                shutil.copytree(item, staging / item.name)
            elif item.is_file() and item.suffix in {".html", ".txt"}:
                shutil.copy2(item, staging / item.name)
        public_revision = {
            **manifest,
            "output_mode": "github-pages",
            "entry": "index.html",
            "days": [Path(day).name for day in manifest["days"]],
        }
        if os.environ.get("GITHUB_SHA"):
            public_revision["source_commit"] = os.environ["GITHUB_SHA"]
        (staging / "revision.json").write_text(
            json.dumps(public_revision, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (staging / ".nojekyll").touch()
        report = validate_site(staging)
        previous = Path(tmp) / "previous"
        if output.exists():
            output.rename(previous)
        try:
            staging.rename(output)
        except Exception:
            if previous.exists():
                previous.rename(output)
            raise
    print(json.dumps({"output": str(output), **report}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    destination = args.output if args.output.is_absolute() else ROOT / args.output
    build_pages(destination)
