# Paris trip project

Work from `/home/aether/work/paris-trip`. This is an independent local Git repository; `/home/aether/work/os-environment` is a separate project.

- The canonical itinerary is `data/plan.json`. Preserve accepted user choices and day numbering.
- Build current pages with `python build_daily.py`. Do not run `prepare_plan.py`: it can replace the edited itinerary with older source data.
- The stable entry is `web/current/index.html`; the companion table is `web/current/review-plan.html`.
- `web/current/paris-companion-plan.html` is the generated complete single-file edition. Its map library is embedded by `portable_bundle.py`; street tiles and external websites require a network connection.
- Keep local backups in `archive/` and shareable exports in `exports/`. These and generated pages are ignored by Git, not deleted.
- For GitHub Pages, run `python scripts/build_pages.py`; it builds and validates a separate `dist/` document root while preserving `web/current/`. Never publish the entire repository as the website.
- `.github/workflows/pages.yml` validates pull requests and deploys only pushes or manual runs on `master`. Run `python -m unittest discover -s tests -v` and `python scripts/validate_site.py dist --check-js` for publication changes.
- Early discussion drafts and the previous update log are kept in `docs/history/`; they are not the canonical itinerary.
- Keep this project local unless the user requests publishing or pushing to a remote.
