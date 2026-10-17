"""Build the entire site locally. No server or client framework is required."""
from functools import partial
from collections import defaultdict
from datetime import date
from html import escape, unescape
import json
from pathlib import Path
import posixpath
import re
import shutil
from urllib.parse import urljoin, urlsplit, urlunsplit
from xml.sax.saxutils import escape as xml_escape

from jinja2 import Environment, FileSystemLoader, StrictUndefined, pass_context, select_autoescape
from markupsafe import Markup
from journey_locations import locate_entries

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content'
OUTPUT = ROOT / 'docs'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def relative_url(value, current):
    parts = urlsplit(value)
    if parts.scheme or parts.netloc or value.startswith('#'): return value
    path = posixpath.relpath(parts.path, posixpath.dirname(current) or '.')
    return urlunsplit(('', '', path, parts.query, parts.fragment))


@pass_context
def render_content(context, html):
    def rewrite(match):
        return match[1] + escape(context['url'](unescape(match[2])), quote=True) + '"'
    return Markup(re.sub(r'((?:href|src)=")([^"]+)"', rewrite, html))


def build():
    site = read_json(CONTENT / 'site.json')
    posts = {}
    for meta in sorted((CONTENT / 'posts').glob('*/post.json')):
        post = read_json(meta)
        post['body'] = meta.with_name('body.html').read_text(encoding='utf-8')
        posts[post['slug']] = post
    journey = locate_entries(CONTENT / 'journey', posts)
    for place in journey['places']:
        post = posts[place['post']]
        place.update({'post_path': post['path'], 'post_title': post['title'], 'date': post['date'], 'date_label': post['date_label']})
        match = re.search(r'<img[^>]+src="([^"]+)"', post['body'])
        place['image'] = match[1] if match else None
    ordered = sorted(posts.values(), key=lambda p: (p['date'], p['slug']), reverse=True)
    months = defaultdict(list)
    for post in ordered:
        months[post['date'][:7]].append(post['slug'])
    site['archives'] = [{'label': date.fromisoformat(month + '-01').strftime('%B %Y'),
                         'path': f'blog/archives/{month[5:]}-{month[:4]}/index.html'} for month in months]
    routes = []
    for meta in sorted((CONTENT / 'pages').glob('*.json')):
        routes.append({**read_json(meta), 'kind': 'page', 'content': meta.stem})
    for post in ordered:
        plain = re.sub(r'<[^>]+>', ' ', post['body'])
        description = ' '.join(unescape(plain).split())[:260]
        routes.append({'kind': 'post', 'path': post['path'], 'post': post['slug'], 'section': 'blog',
                       'title': post['title'] + ' — ' + site['name'], 'description': description,
                       'hero': site['blog']['hero']})
    page_size = site['blog']['page_size']
    def page_path(number):
        return 'blog.html' if number == 1 else f'blog/previous/{number}/index.html'
    total_pages = (len(ordered) + page_size - 1) // page_size
    for number in range(1, total_pages + 1):
        pagination = []
        if number < total_pages: pagination.append({'label': 'Older posts', 'path': page_path(number + 1), 'direction': 'older'})
        if number > 1: pagination.append({'label': 'Newer posts', 'path': page_path(number - 1), 'direction': 'newer'})
        routes.append({'kind': 'listing', 'path': page_path(number), 'section': 'blog',
                       'title': 'Blog — ' + site['name'], 'heading': 'Blog',
                       'description': site['blog']['description'], 'hero': site['blog']['hero'],
                       'posts': [p['slug'] for p in ordered[(number - 1) * page_size:number * page_size]], 'pagination': pagination})
    for archive, slugs in zip(site['archives'], months.values()):
        routes.append({'kind': 'listing', 'path': archive['path'], 'section': 'blog',
                       'title': archive['label'] + ' — ' + site['name'], 'heading': archive['label'],
                       'description': site['blog']['description'], 'hero': site['blog']['hero'],
                       'posts': slugs, 'pagination': []})
    env = Environment(loader=FileSystemLoader(ROOT / 'templates'),
                      autoescape=select_autoescape(['html']), undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    env.filters['render_content'] = render_content
    # The generated directory contains no hand-authored files.
    resolved = OUTPUT.resolve()
    if resolved != ROOT / 'docs' or not resolved.is_relative_to(ROOT):
        raise RuntimeError('Refusing to clean an unexpected output directory')
    if OUTPUT.exists(): shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    shutil.copytree(ROOT / 'static', OUTPUT / 'assets')
    journey_output = OUTPUT / 'assets/data/journey'
    journey_output.mkdir(parents=True, exist_ok=True)
    for name in ['route.geojson', 'locations.geojson', 'source.kml', 'entry-locations.json']:
        shutil.copyfile(CONTENT / 'journey' / name, journey_output / name)
    (journey_output / 'config.json').write_text(json.dumps(journey, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    for route in routes:
        post = posts.get(route.get('post'))
        body = (CONTENT / 'pages' / (route['content'] + '.html')).read_text(encoding='utf-8') if route['kind'] == 'page' else None
        context = {'site': site, 'route': route, 'posts': posts, 'journey': journey,
                   'post': post, 'body': body,
                   'route_posts': [posts[x] for x in route.get('posts', [])],
                   'url': partial(relative_url, current=route['path']),
                   'absolute_url': partial(urljoin, site['url']),
                   'canonical': urljoin(site['url'], route['path'].removesuffix('index.html')),
                   'active_navigation': 'blog.html' if route['section'] == 'blog' else route['path'],
                   'page_title': post['title'] if post else route.get('heading', site['name'])}
        name = route.get('template') or {'page': 'page.html', 'post': 'post-page.html', 'listing': 'listing.html'}[route['kind']]
        path = OUTPUT / route['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(env.get_template(name).render(**context), encoding='utf-8', newline='\n')
    (OUTPUT / '.nojekyll').touch()
    urls = [urljoin(site['url'], r['path'].removesuffix('index.html')) for r in routes]
    (OUTPUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                      ''.join('  <url><loc>' + xml_escape(url) + '</loc></url>\n' for url in urls) + '</urlset>\n', encoding='utf-8')
    (OUTPUT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + site['url'] + 'sitemap.xml\n', encoding='utf-8')
    print(f'Built {len(routes)} pages from {len(posts)} posts and shared templates.')


if __name__ == '__main__': build()
