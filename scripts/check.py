"""Check archived content, navigation and all locally referenced assets."""
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parents[1]
site = root / 'docs'
report = json.loads((root / 'migration-report.json').read_text(encoding='utf-8'))
errors = []
for path in site.rglob('*.html'):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    key = path.relative_to(site).as_posix()
    text = [x.get_text() for x in soup.select('#wsite-content .paragraph, .blog-title, .blog-date')]
    expected = report['source_content'].get(key)
    if expected is not None:
        # Contact address was obscured by Cloudflare in the source HTML.
        if key != 'contact.html' and text != expected: errors.append(f'Content changed: {key}')
    for tag in soup.find_all(True):
        for attr in ['href', 'src', 'poster', 'data-src']:
            value = tag.get(attr, '')
            p = urlsplit(value)
            if not value or not p.path or p.scheme or p.netloc: continue
            target = (path.parent / unquote(p.path)).resolve()
            if target.is_dir(): target /= 'index.html'
            if not target.exists(): errors.append(f'{key}: missing {value}')
        if tag.name == 'script' and not tag.get('src', '').endswith('static.js'):
            errors.append(f'Hosted runtime remains: {key}')
    if soup.select('[src*="weebly.com"], [src*="editmysite.com"]'):
        errors.append(f'External hosted asset: {key}')
for path in list(site.rglob('*.css')) + list(site.rglob('*.html')):
    for value in re.findall(r'url\([\"\']?([^\)\"\']+)', path.read_text(encoding='utf-8')):
        p = urlsplit(value)
        if p.scheme or p.netloc or not p.path: continue
        if not (path.parent / unquote(p.path)).exists(): errors.append(f'{path.name}: missing CSS asset {value}')
print(f"Checked {len(list(site.rglob('*.html')))} HTML files, {len(report['assets'])} assets")
print(f"Download failures: {len(report['failures'])}")
for error in sorted(set(errors)): print(error)
print(f'Errors: {len(set(errors))}')
raise SystemExit(bool(errors or report['failures']))
