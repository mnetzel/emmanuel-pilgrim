"""One-off, reproducible Weebly to buildless HTML migration.
Run: python -m pip install beautifulsoup4; python scripts/mirror.py
"""
import concurrent.futures as futures
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.parse as U
import urllib.request as R
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
ORIGIN = 'https://emmanuel-pilgrim.weebly.com'
HOST = U.urlsplit(ORIGIN).netloc
pages, assets, failures, originals = {}, {}, [], {}
OUT.mkdir(exist_ok=True)

def fetch(url):
    for attempt in range(3):
        try:
            req = R.Request(url, headers={'User-Agent': 'Mozilla/5.0 (static archival migration)'})
            with R.urlopen(req, timeout=45) as response:
                return response.read()
        except Exception:
            if attempt == 2: raise
            time.sleep(attempt + 1)

def page_path(url):
    path = U.unquote(U.urlsplit(url).path).strip('/')
    if not path: return 'index.html'
    if path.endswith('.html'): return path
    return path + '/index.html'

def normalized(url):
    p = U.urlsplit(url)
    return U.urlunsplit(('https', p.netloc, p.path or '/', p.query, ''))

def relative(target, current):
    return os.path.relpath(target, Path(current).parent).replace('\\', '/')

def asset_path(url):
    p = U.urlsplit(url)
    name = U.unquote(p.path.rsplit('/', 1)[-1]) or 'asset'
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    return 'assets/' + hashlib.sha256(url.encode()).hexdigest()[:14] + '-' + name

def register_asset(url):
    url = normalized(url)
    if url not in assets: assets[url] = asset_path(url)
    return assets[url]

def css_urls(text, base, current):
    def replace(m):
        raw = m.group(1).strip(' \t\r\n\"\'')
        if not raw or raw.startswith(('data:', '#')): return m.group(0)
        url = normalized(U.urljoin(base, raw))
        return 'url("' + relative(register_asset(url), current) + '")'
    return re.sub(r'url\(([^)]+)\)', replace, text, flags=re.I)

def get_page(url):
    raw = fetch(url).decode('utf-8')
    # Strip the hosted runtime before saving; the static copy has its own tiny JS.
    raw = re.sub(r'<script\b[^>]*>.*?</script\s*>', '', raw, flags=re.I | re.S)
    return BeautifulSoup(raw, 'html.parser')

def discover(soup, url):
    found = set()
    for a in soup.select('a[href]'):
        p = U.urlsplit(U.urljoin(url, a['href']))
        if p.netloc == HOST and (p.path in ['/', '/index.html', '/blog.html', '/about.html', '/contact.html', '/faq.html'] or p.path.startswith('/blog/')):
            if not p.path.endswith(('.xml', '.php')):
                found.add(U.urlunsplit(('https', HOST, p.path or '/', '', '')))
    return found

def transform(soup, url):
    current = page_path(url)
    originals[current] = [x.get_text() for x in soup.select('#wsite-content .paragraph, .blog-title, .blog-date')]
    for node in soup.select('#weebly-footer-signup-container-v3, #customer-accounts-app, .blogCommentReplyWrapper, #commentReplyTitle, .fb-like, .fb-share-button'):
        node.decompose()
    for node in soup.select('iframe'):
        if 'weebly.com' in node.get('src', ''): node.decompose()
    for node in soup.select('[data-cfemail]'):
        value = bytes.fromhex(node['data-cfemail'])
        email = ''.join(chr(b ^ value[0]) for b in value[1:])
        node.string = email
        if node.parent.name == 'a': node.parent['href'] = 'mailto:' + email
        del node['data-cfemail']
    for node in soup.find_all(True):
        for attr in list(node.attrs):
            if attr.startswith('on'): del node[attr]
        for attr in ['src', 'href', 'poster', 'data-src']:
            raw = node.get(attr)
            if not raw or raw.startswith(('#', 'mailto:', 'tel:', 'data:', 'javascript:')): continue
            absolute = U.urljoin(url, raw)
            p = U.urlsplit(absolute)
            clean = normalized(absolute)
            if p.netloc == HOST and clean in pages:
                node[attr] = relative(page_path(clean), current) + ('#' + p.fragment if p.fragment else '')
            elif attr != 'href' or node.name == 'link' or p.path.startswith('/uploads/'):
                if p.scheme in ('http', 'https'):
                    node[attr] = relative(register_asset(clean), current)
            elif p.netloc == HOST and p.path in ('/', '/blog'):
                node[attr] = relative('blog.html' if p.path == '/blog' else 'index.html', current)
            elif raw.startswith('//'):
                node[attr] = 'https:' + raw
        if node.has_attr('style'):
            node['style'] = css_urls(node['style'], url, current)
        if node.name == 'style' and node.string:
            node.string = css_urls(node.string, url, current)
        if node.has_attr('srcset'):
            values = []
            for item in node['srcset'].split(','):
                parts = item.split()
                if parts:
                    parts[0] = relative(register_asset(U.urljoin(url, parts[0])), current)
                    values.append(' '.join(parts))
            node['srcset'] = ', '.join(values)
    for a in soup.select('.wsite-image > a:not([href])'):
        img = a.find('img')
        if img and img.get('src'): a['href'] = img['src']; a['data-lightbox'] = ''
    for a in soup.select('a[href]'):
        if re.search(r'\.(jpg|jpeg|png|webp)(?:\?|$)', a['href'], re.I): a['data-lightbox'] = ''
    extra = soup.new_tag('link', rel='stylesheet', href=relative('static.css', current))
    soup.head.append(extra)
    script = soup.new_tag('script', src=relative('static.js', current), defer='')
    soup.body.append(script)
    path = OUT / current
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(soup), encoding='utf-8')

def main():
    sitemap = ET.fromstring(fetch(ORIGIN + '/sitemap.xml'))
    pending = {ORIGIN + '/'} | {x.text for x in sitemap.iter() if x.tag.endswith('}loc')}
    with futures.ThreadPoolExecutor(max_workers=8) as pool:
        while pending:
            batch = {pool.submit(get_page, url): url for url in sorted(pending) if url not in pages}
            pending = set()
            for future in futures.as_completed(batch):
                url = batch[future]
                try:
                    soup = future.result()
                    pages[url] = soup
                    pending |= discover(soup, url) - pages.keys()
                except Exception as error: failures.append({'url': url, 'error': str(error)})
            print(f'Pages: {len(pages)}; next: {len(pending)}', flush=True)
        for url, soup in pages.items(): transform(soup, url)
        done = set()
        while set(assets) - done:
            batch = {pool.submit(fetch, url): url for url in set(assets) - done}
            for future in futures.as_completed(batch):
                url = batch[future]
                done.add(url)
                try:
                    data = future.result()
                    path = OUT / assets[url]
                    if U.urlsplit(url).path.endswith('.css'):
                        data = css_urls(data.decode('utf-8'), url, assets[url]).encode('utf-8')
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                except Exception as error: failures.append({'url': url, 'error': str(error)})
            print(f'Assets: {len(done)}/{len(assets)}', flush=True)
    report = {'source': ORIGIN, 'pages': {u: page_path(u) for u in pages}, 'assets': assets, 'failures': failures, 'source_content': originals}
    (ROOT / 'migration-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Finished: {len(pages)} URLs, {len(assets)} assets, {len(failures)} failures', flush=True)

if __name__ == '__main__': main()
