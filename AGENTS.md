# Paris trip project

Work from `/home/aether/work/paris-trip`. This is an independent local Git repository; `/home/aether/work/os-environment` is a separate project.

- The canonical itinerary is `data/plan.json`. Preserve accepted user choices and day numbering.
- Build current pages with `python build_daily.py`. Do not run `prepare_plan.py`: it can replace the edited itinerary with older source data.
- The stable entry is `web/current/index.html`; the companion table is `web/current/review-plan.html`.
- Maintain only GitHub Pages and the local multi-page preview. Do not generate, publish or add download links for the retired single-file edition.
- Keep local backups in `archive/` and historical exports in `exports/`. The retired single-file generator and its bundled library are archived in `archive/retired-single-file-20261111/`. These and generated pages are ignored by Git, not deleted.
- For GitHub Pages, run `python scripts/build_pages.py`; it builds and validates a separate `dist/` document root while preserving `web/current/`. Never publish the entire repository as the website.
- The user has made `https://github.com/aetherrootr/paris-trip-plan.git` public and authorized a public website using native GitHub Pages. Private credentials, tickets and QR codes must be managed elsewhere and never committed or added to published data or assets.
- `.github/workflows/pages.yml` validates pull requests and builds `master`. Deployment is gated by the repository variable `PAGES_DEPLOY_ENABLED=true`; enable it after Pages is configured. Updates to `master` then automatically rebuild and publish the site.
- The user explicitly requires DNS and Cloudflare changes to be performed by them. Provide instructions, but do not change DNS records, Cloudflare settings or custom-domain bindings on their behalf.
- For publication changes, run the Python tests, `node --test tests/site-ui.test.cjs`, and `python scripts/validate_site.py dist --check-js`. Preserve the phone navigation, readable companion cards and touch controls.
- Early discussion drafts and the previous update log are kept in `docs/history/`; they are not the canonical itinerary.
- Keep this project local unless the user requests publishing or pushing to a remote.
