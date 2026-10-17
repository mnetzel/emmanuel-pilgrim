"""Resolve reviewed journal locations on the archived, directed route, offline.

Publication dates are a rough model, not GPS timestamps. Regional references
remain estimates, including when they bound a date interpolation.
"""
from bisect import bisect_right
from datetime import date
from hashlib import sha256
import json
import math

from bs4 import BeautifulSoup


def distance_km(a, b):
    lat_a, lat_b = math.radians(a[1]), math.radians(b[1])
    dlat, dlon = lat_b - lat_a, math.radians(b[0] - a[0])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1, math.sqrt(h)))


class RecordedRoute:
    def __init__(self, coordinates):
        self.coordinates = [p[:2] for p in coordinates]
        self.offsets = [0.0]
        for a, b in zip(self.coordinates, self.coordinates[1:]):
            self.offsets.append(self.offsets[-1] + distance_km(a, b))

    def point_at(self, offset):
        if not 0 <= offset <= self.offsets[-1]:
            raise ValueError('Position is outside the recorded route')
        i = min(bisect_right(self.offsets, offset) - 1, len(self.coordinates) - 2)
        a, b = self.coordinates[i:i + 2]
        length = self.offsets[i + 1] - self.offsets[i]
        fraction = (offset - self.offsets[i]) / length if length else 0
        return [a[j] + (b[j] - a[j]) * fraction for j in (0, 1)]

    def project(self, point, minimum=0):
        """Nearest point after the previous stage, preserving return passages."""
        candidates = []
        scale = math.cos(math.radians(point[1]))
        for i, (a, b) in enumerate(zip(self.coordinates, self.coordinates[1:])):
            end = self.offsets[i + 1]
            if end < minimum:
                continue
            length = end - self.offsets[i]
            dx, dy = (b[0] - a[0]) * scale, b[1] - a[1]
            denominator = dx * dx + dy * dy
            fraction = (((point[0] - a[0]) * scale * dx + (point[1] - a[1]) * dy) / denominator) if denominator else 0
            lower = max(0, (minimum - self.offsets[i]) / length) if length else 0
            fraction = max(lower, min(1, fraction))
            projected = [a[j] + fraction * (b[j] - a[j]) for j in (0, 1)]
            candidates.append((distance_km(point, projected), self.offsets[i] + length * fraction))
        if not candidates:
            raise ValueError('No chronological route section for location')
        return min(candidates)[1]


def locate_entries(folder, posts):
    config = json.loads((folder / 'map.json').read_text(encoding='utf-8'))
    reviews = json.loads((folder / config['entry_locations_file']).read_text(encoding='utf-8'))
    entries = reviews['entries']
    if len(entries) != len(posts) or {e['post'] for e in entries} != set(posts):
        raise ValueError('Review every post in content/journey/entry-locations.json before building')
    features = json.loads((folder / config['route_file']).read_text(encoding='utf-8'))['features']
    line = next(f for f in features if f['properties']['role'] == 'main')
    route = RecordedRoute(line['geometry']['coordinates'])
    places = []
    previous_offset = 0
    for review in sorted(entries, key=lambda e: (posts[e['post']]['date'], e['post'])):
        place = dict(review)
        post = posts[place['post']]
        text = ' '.join(BeautifulSoup(post['body'], 'html.parser').get_text(' ', strip=True).split())
        if sha256(text.encode()).hexdigest() != place.pop('reviewed_text_sha256'):
            raise ValueError(f"Review the changed location evidence for {place['post']}")
        if not place['evidence'] or not all(quote in text for quote in place['evidence']):
            raise ValueError(f"Missing source evidence for {place['post']}")
        place.update(id=place['post'], date=post['date'], date_label=post['date_label'],
                     post_path=post['path'], post_title=post['title'])
        method = place['method']
        expected_status = 'documented' if method in ('named_place', 'identified_place') else 'estimated'
        if place['status'] != expected_status:
            raise ValueError(f"Inconsistent certainty for {place['post']}")
        if method == 'route_start':
            place.update(coordinates=route.point_at(0), route_offset_km=0,
                         coordinate_source='route.geojson', location_precision='departure_area')
        elif 'coordinates' in place and place.get('on_recorded_route', True):
            offset = route.project(place['coordinates'], previous_offset)
            place['route_offset_km'] = offset
            previous_offset = offset
            if method == 'content_estimate':
                place['reference_coordinates'] = place['coordinates']
                place['reference_coordinate_source'] = place['coordinate_source']
                place.update(coordinates=route.point_at(offset), coordinate_source='route.geojson',
                             location_precision='region')
        elif method != 'date_interpolation' and 'coordinates' not in place:
            raise ValueError(f"Missing coordinates for {place['post']}")
        places.append(place)

    # Every interpolated position stays between two dated references along the
    # recorded line. There is no straight-line shortcut, extrapolation or routing API.
    for i, place in enumerate(places):
        if place['method'] != 'date_interpolation':
            continue
        before = next((p for p in reversed(places[:i]) if p['method'] != 'date_interpolation' and 'route_offset_km' in p), None)
        after = next((p for p in places[i + 1:] if p['method'] != 'date_interpolation' and 'route_offset_km' in p), None)
        if before is None or after is None:
            raise ValueError(f"Two route references are required for {place['post']}")
        start, end, day = map(date.fromisoformat, (before['date'], after['date'], place['date']))
        fraction = (day - start).days / (end - start).days
        if not 0 <= fraction <= 1 or before['route_offset_km'] > after['route_offset_km']:
            raise ValueError('Invalid interpolation interval')
        offset = before['route_offset_km'] + fraction * (after['route_offset_km'] - before['route_offset_km'])
        place.update(coordinates=route.point_at(offset), route_offset_km=offset,
                     coordinate_source='route.geojson', location_precision='route_estimate',
                     interpolation={'before': before['id'], 'after': after['id'],
                                    'fraction': fraction, 'days_from_start': (day - start).days,
                                    'interval_days': (end - start).days,
                                    'before_status': before['status'], 'after_status': after['status']})
        place['interpolation_note'] = f"Estimated along the recorded route between {before['name']} ({before['date_label']}) and {after['name']} ({after['date_label']}), using publication dates."
        if before['status'] == 'estimated' or after['status'] == 'estimated':
            place['interpolation_note'] += ' At least one bounding location is itself approximate.'

    labels = {'named_place': 'Place named in the entry', 'identified_place': 'Place identified from the entry',
              'content_estimate': 'Estimated area from the text', 'date_interpolation': 'Estimated from dates',
              'route_start': 'Approximate departure area'}
    for place in places:
        place['method_label'] = labels[place['method']]
    config['places'] = places
    config['counts'] = {status: sum(p['status'] == status for p in places) for status in ('documented', 'estimated')}
    config['reviewed_at'] = reviews['reviewed_at']
    return config
