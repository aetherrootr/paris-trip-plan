"""Publication regressions: broken links must fail before deployment."""
from pathlib import Path
import tempfile
import unittest

from scripts.validate_site import SiteError, validate_site


class PublicationChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_relative_links_work_under_a_repository_subpath(self):
        self.write("index.html", '<a href="day-02.html#stop">Day 2</a>')
        self.write("day-02.html", '<h1 id="stop">Visit</h1><img src="assets/map.svg">')
        self.write("assets/map.svg", "<svg/>")
        self.assertEqual(validate_site(self.root)["local_links"], 2)

    def test_missing_day_page_fails(self):
        self.write("index.html", '<a href="day-02.html">Day 2</a>')
        with self.assertRaisesRegex(SiteError, "Broken link"):
            validate_site(self.root)

    def test_missing_stop_anchor_fails(self):
        self.write("index.html", '<a href="day-02.html#missing">Visit</a>')
        self.write("day-02.html", '<h1 id="stop">Visit</h1>')
        with self.assertRaisesRegex(SiteError, "Missing anchor"):
            validate_site(self.root)

    def test_root_relative_assets_are_not_safe_for_project_pages(self):
        self.write("index.html", '<img src="/assets/map.svg">')
        with self.assertRaisesRegex(SiteError, "Root-relative"):
            validate_site(self.root)

    def test_machine_local_links_are_rejected(self):
        self.write("index.html", '<a href="file:///home/aether/work/paris-trip/day-02.html">Day 2</a>')
        with self.assertRaisesRegex(SiteError, "Machine-local"):
            validate_site(self.root)

    def test_symbolic_assets_are_not_published(self):
        self.write("index.html", "<h1>Trip</h1>")
        (self.root / "linked.html").symlink_to(self.root / "index.html")
        with self.assertRaisesRegex(SiteError, "symbolic"):
            validate_site(self.root)


if __name__ == "__main__":
    unittest.main()
