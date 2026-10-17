"""Contracts captured before the refactor, independent of the build templates."""
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def normalize(text):
    # Ignore layout whitespace while preserving every word and punctuation mark.
    return ' '.join(re.findall(r'\w+|[^\w\s]', text.replace('\u200b', ''), flags=re.UNICODE))


def text_hash(node):
    return sha256(normalize(node.get_text(' ', strip=True)).encode()).hexdigest()


@lru_cache(maxsize=None)
def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads((ROOT / 'tests/fixtures/content-baseline.json').read_text(encoding='utf-8'))
        cls.images = json.loads((ROOT / 'tests/fixtures/image-checksums.json').read_text(encoding='utf-8'))
        cls.pages = {p.relative_to(DOCS).as_posix(): BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser') for p in DOCS.rglob('*.html')}

    def test_all_original_addresses_and_post_order(self):
        self.assertTrue(set(self.baseline['routes']).issubset(self.pages))
        for path, expected in self.baseline['routes'].items():
            if path == 'blog.html' or '/previous/' in path: continue
            with self.subTest(path=path):
                actual = [a['id'].removeprefix('post-title-') for a in self.pages[path].select('.post-title')]
                actual = [x for x in actual if x in self.baseline['posts']]
                self.assertEqual(actual, expected['posts'])
        original_order = self.baseline['routes']['blog.html']['posts'][:]
        original_pagination = sorted((p for p in self.baseline['routes'] if '/previous/' in p), key=lambda p: int(p.split('/')[-2]))
        for path in original_pagination: original_order.extend(self.baseline['routes'][path]['posts'])
        paths = ['blog.html'] + sorted((p for p in self.pages if '/previous/' in p), key=lambda p: int(p.split('/')[-2]))
        actual_order = [title['id'].removeprefix('post-title-') for p in paths for title in self.pages[p].select('.post-title')]
        self.assertEqual([x for x in actual_order if x in self.baseline['posts']], original_order)

    def test_all_original_page_and_post_text(self):
        for name, expected in self.baseline['pages'].items():
            path = 'index.html' if name == 'welcome' else name + '.html'
            node = self.pages[path].select_one('.page-content')
            if name in ('welcome', 'faq'):
                node = BeautifulSoup(str(node), 'html.parser')
                node.select_one('.visually-hidden').decompose()
            with self.subTest(page=name): self.assertEqual(text_hash(node), expected['text_sha256'])
        for path, soup in self.pages.items():
            for post in soup.select('.post'):
                title = post.select_one('.post-title')
                slug = title['id'].removeprefix('post-title-')
                if slug not in self.baseline['posts']: continue
                expected = self.baseline['posts'][slug]
                with self.subTest(path=path, post=slug):
                    self.assertEqual(text_hash(post.select_one('.post-content')), expected['text_sha256'])
                    self.assertEqual(normalize(title.get_text()), normalize(expected['title']))
                    self.assertEqual(post.select_one('time').get_text(strip=True), expected['date'])

    def test_photographs_are_identical_and_in_original_order(self):
        for relative, digest in self.images.items():
            with self.subTest(image=relative): self.assertEqual(file_hash(DOCS / 'assets' / relative), digest)
        for path, soup in self.pages.items():
            for post in soup.select('.post'):
                slug = post.select_one('.post-title')['id'].removeprefix('post-title-')
                if slug not in self.baseline['posts']: continue
                photos = [file_hash((DOCS / path).parent / img['src']) for img in post.select('.post-content img')]
                with self.subTest(path=path): self.assertEqual(photos, self.baseline['posts'][slug]['photos'])
        for name, expected in self.baseline['pages'].items():
            path = 'index.html' if name == 'welcome' else name + '.html'
            photos = [file_hash((DOCS / path).parent / img['src']) for img in self.pages[path].select('.page-content img')]
            with self.subTest(page=name): self.assertEqual(photos, expected['photos'])

    def test_reader_comments_authors_dates_and_anchors_preserved(self):
        total = 0
        for slug, expected in self.baseline['comments'].items():
            soup = self.pages[f'blog/{slug}/index.html']
            comments = soup.select('.comment')
            self.assertEqual(len(comments), len(expected))
            self.assertIsNotNone(soup.select_one('#comments'))
            for comment, original in zip(comments, expected):
                with self.subTest(post=slug, comment=original['id']):
                    self.assertEqual(comment['id'], original['id'])
                    self.assertEqual(comment.select_one('.comment-author').get_text(), original['author'])
                    self.assertEqual(comment.select_one('time').get_text(), original['date_label'])
                    self.assertEqual(text_hash(comment.select_one('.comment-content')), original['body_sha256'])
                    total += 1
        self.assertEqual(total, sum(len(x) for x in self.baseline['comments'].values()))

    def test_semantics_accessibility_and_no_legacy_markup(self):
        for path, soup in self.pages.items():
            with self.subTest(path=path):
                self.assertEqual(len(soup.find_all('main')), 1)
                self.assertEqual(len(soup.find_all('h1')), 1)
                self.assertIsNotNone(soup.select_one('header.site-header'))
                self.assertIsNotNone(soup.select_one('footer.site-footer'))
                self.assertIsNotNone(soup.select_one('a.skip-link[href="#main-content"]'))
                self.assertEqual(soup.html['lang'], 'en')
                self.assertFalse(soup.select('[style], table, iframe, [class*="wsite"], [id*="wsite"], [class*="blogComment"]'))
                ids = [x['id'] for x in soup.select('[id]')]
                self.assertEqual(len(ids), len(set(ids)))
                for nav in soup.find_all('nav'): self.assertTrue(nav.get('aria-label'))
                for img in soup.select('img[src]'):
                    self.assertTrue(img.get('alt'))
                    self.assertTrue(img.get('width') and img.get('height'))
                for script in soup.find_all('script'):
                    self.assertTrue(script.get('src', '').endswith('assets/js/site.js'))
                for link in soup.select('link[rel="stylesheet"]'):
                    self.assertFalse(urlsplit(link['href']).scheme)

    def test_local_links_assets_and_fragments(self):
        for path, soup in self.pages.items():
            for tag in soup.find_all(True):
                for attr in ('href', 'src'):
                    value = tag.get(attr)
                    if not value: continue
                    parts = urlsplit(value)
                    if parts.scheme or parts.netloc: continue
                    target = ((DOCS / path).parent / unquote(parts.path)).resolve() if parts.path else (DOCS / path).resolve()
                    if target.is_dir(): target /= 'index.html'
                    with self.subTest(path=path, link=value):
                        self.assertTrue(target.is_relative_to(DOCS.resolve()))
                        self.assertTrue(target.is_file())
                        if parts.fragment and target.suffix == '.html':
                            dest = self.pages[target.relative_to(DOCS.resolve()).as_posix()]
                            self.assertIsNotNone(dest.find(id=unquote(parts.fragment)))
        for file in (DOCS / 'assets/css').glob('*.css'):
            for value in re.findall(r'url\(["\']?([^\)"\'\s;]+)', file.read_text(encoding='utf-8')):
                self.assertTrue((file.parent / value).is_file(), value)

    def test_sitemap_and_contact(self):
        sitemap = ET.parse(DOCS / 'sitemap.xml')
        locs = [x.text for x in sitemap.iter() if x.tag.endswith('}loc')]
        self.assertEqual(len(locs), len(self.pages))
        self.assertTrue(all(x.startswith('https://mnetzel.github.io/emmanuel-pilgrim/') for x in locs))
        self.assertIsNotNone(self.pages['contact.html'].select_one('a[href="mailto:emmanuel.french.pilgrim@proton.me"]'))


if __name__ == '__main__': unittest.main()
