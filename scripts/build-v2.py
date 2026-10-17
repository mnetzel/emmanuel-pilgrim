"""Create the alternative visual edition, sharing the original media files."""
from pathlib import Path
import os
import re
from bs4 import BeautifulSoup

site = Path(__file__).resolve().parents[1] / 'docs'
pages = [p for p in site.rglob('*.html') if 'v2' not in p.relative_to(site).parts]
for source in pages:
    target = site / 'v2' / source.relative_to(site)
    target.parent.mkdir(parents=True, exist_ok=True)
    html = source.read_text(encoding='utf-8')
    # Old headings contain long runs of non-breaking spaces for manual alignment.
    html = re.sub(r'(<h2\b[^>]*class="blog-title"[^>]*>)(.*?)(</h2>)',
                  lambda m: m[1] + re.sub(r'(?:\s|&nbsp;|\u00a0){2,}', ' ', m[2]) + m[3], html, flags=re.S)
    # Media and runtime are shared; navigation stays within the alternative edition.
    html = re.sub(r'(?<=["\'(])((?:\.\./)*assets/)', r'../\1', html)
    html = re.sub(r'((?:href|src)=")((?:\.\./)*static\.(?:css|js))', r'\1../\2', html)
    theme = os.path.relpath(site / 'v2' / 'theme.css', target.parent).replace('\\', '/')
    original = os.path.relpath(source, target.parent).replace('\\', '/')
    html = html.replace('</head>', f'<link rel="stylesheet" href="{theme}"></head>')
    html = html.replace('</body>', f'<a class="edition-link" href="{original}">Original version <span aria-hidden="true">↗</span></a></body>')
    target.write_text(html, encoding='utf-8')
    before = BeautifulSoup(source.read_text(encoding='utf-8'), 'html.parser')
    after = BeautifulSoup(html, 'html.parser')
    assert ' '.join(before.select_one('#wsite-content').get_text().split()) == ' '.join(after.select_one('#wsite-content').get_text().split())
print(f'Built {len(pages)} V2 pages with unchanged content and shared images.')
