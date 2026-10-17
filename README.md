# Emmanuel, French Pilgrim

Static archive of https://emmanuel-pilgrim.weebly.com/, migrated on 17 October 2026.

The published website is in `docs/`: plain HTML, the original CSS and fonts,
original photographs, and one small JavaScript file for the mobile menu and
image viewer. No build step, framework, database, analytics or Weebly runtime.
All internal links are relative, including archive and pagination links, so the
site works under the GitHub Pages repository path.

## Preview

```sh
python -m http.server 8000 --directory docs
```

Open http://localhost:8000/. Edit the HTML/CSS directly.

## GitHub Pages

Publish the `main` branch, `/docs` folder from repository Settings → Pages.
The public address is https://mnetzel.github.io/emmanuel-pilgrim/.

## Migration

`scripts/mirror.py` follows the source sitemap, internal blog links, archives and
pagination; downloads original media and CSS/font dependencies; rewrites links;
decodes the public contact email; and replaces the hosted JavaScript.
It requires Python and `beautifulsoup4`. `migration-report.json` records every
source URL, local asset, failed download and source text used for verification.
Run `python scripts/check.py` to check content preservation and local references.

Existing comment text, when present in source HTML, is retained. Adding comments
requires a backend and is intentionally absent from this static archive.
External social links still lead to their original services.

The experimental AI photo edits in the top-level `assets/` folder are excluded
from the published site. The website uses the original photographs exclusively.
