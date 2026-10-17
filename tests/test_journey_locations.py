"""Location coverage, evidence and the geographic/date interpolation contract."""
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from journey_locations import RecordedRoute, distance_km, locate_entries


class LocationTests(unittest.TestCase):
    def test_interpolation_follows_distance_around_bend_and_unequal_dates(self):
        # A diagonal midpoint would be (0.5, 0.5). Halfway along this L is (1, 0).
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            folder.joinpath('map.json').write_text(json.dumps({'route_file': 'route.geojson', 'entry_locations_file': 'review.json'}))
            folder.joinpath('route.geojson').write_text(json.dumps({'features': [{'properties': {'role': 'main'}, 'geometry': {'coordinates': [[0, 0], [1, 0], [1, 1]]}}]}))
            entries = []
            posts = {}
            for slug, day, coordinates in [('first', '2020-01-01', [0, 0]), ('middle', '2020-01-02', None), ('last', '2020-01-05', [1, 1])]:
                posts[slug] = dict(date=day, date_label=day, path=slug + '.html', title=slug, body='<p>Evidence.</p>')
                entry = dict(post=slug, name=slug, country='Example', status='documented' if coordinates is not None else 'estimated',
                             method='named_place' if coordinates is not None else 'date_interpolation', evidence=['Evidence.'], explanation='Example.',
                             reviewed_text_sha256=sha256(b'Evidence.').hexdigest())
                if coordinates is not None:
                    entry.update(coordinates=coordinates, coordinate_source='https://example.com', location_precision='town')
                entries.append(entry)
            folder.joinpath('review.json').write_text(json.dumps({'reviewed_at': '2026-10-18', 'entries': entries}))
            middle = locate_entries(folder, posts)['places'][1]
            self.assertEqual(middle['interpolation']['fraction'], .25)
            self.assertAlmostEqual(middle['coordinates'][0], .5, places=5)
            self.assertEqual(middle['coordinates'][1], 0)
            route = RecordedRoute([[0, 0], [1, 0], [1, 1]])
            self.assertAlmostEqual(route.point_at(route.offsets[-1] / 2)[0], 1, places=5)
            self.assertAlmostEqual(route.point_at(route.offsets[-1] / 2)[1], 0, places=5)
            posts['new'] = posts['last']
            with self.assertRaisesRegex(ValueError, 'Review every post'):
                locate_entries(folder, posts)

    def test_projection_respects_return_passages_and_rejects_extrapolation(self):
        route = RecordedRoute([[0, 0], [1, 0], [0, 0], [0, 1]])
        self.assertAlmostEqual(route.project([0, 0]), 0)
        self.assertAlmostEqual(route.project([0, 0], route.offsets[1]), route.offsets[2])
        with self.assertRaises(ValueError): route.point_at(-1)
        with self.assertRaises(ValueError): route.point_at(route.offsets[-1] + 1)

    def test_all_estimates_stay_on_the_route_and_between_their_dated_references(self):
        config = json.loads((ROOT / 'docs/assets/data/journey/config.json').read_text(encoding='utf-8'))
        places = {p['id']: p for p in config['places']}
        features = json.loads((ROOT / 'content/journey/route.geojson').read_text(encoding='utf-8'))['features']
        route = RecordedRoute(next(f['geometry']['coordinates'] for f in features if f['properties']['role'] == 'main'))
        self.assertEqual(config['counts'], {'documented': 22, 'estimated': 16})
        for place in places.values():
            with self.subTest(post=place['post']):
                if place['status'] == 'estimated':
                    self.assertLess(distance_km(route.point_at(place['route_offset_km']), place['coordinates']), .000001)
                if place['method'] != 'date_interpolation': continue
                calculation = place['interpolation']
                before, after = places[calculation['before']], places[calculation['after']]
                self.assertLess(before['date'], place['date'])
                self.assertLess(place['date'], after['date'])
                start, end, day = map(date.fromisoformat, (before['date'], after['date'], place['date']))
                fraction = (day - start).days / (end - start).days
                expected = before['route_offset_km'] + fraction * (after['route_offset_km'] - before['route_offset_km'])
                self.assertAlmostEqual(place['route_offset_km'], expected)
                self.assertEqual(calculation['before_status'], before['status'])
                self.assertEqual(calculation['after_status'], after['status'])

        # The Romanian route returns through the same city; never project the
        # April 2024 visit onto the outward passage from July 2023.
        self.assertGreater(places['a-pilgrims-trials-and-kindness-along-the-way']['route_offset_km'], places['the-pilgrims-winter-trial']['route_offset_km'])
        self.assertLess(places['meeting-with-a-bear']['route_offset_km'], places['decision']['route_offset_km'])
        balkans = places['a-winter-odyssey-in-the-balkans']
        self.assertEqual(balkans['coordinate_source'], 'https://www.wikidata.org/wiki/Q11194')
        self.assertAlmostEqual(balkans['coordinates'][0], 18.413055555555555)
        final = places['five-years-walking-across-europe-15-countries-10000-km-5-winters-and-now-a-pause']
        self.assertFalse(final['on_recorded_route'])
        self.assertNotIn('route_offset_km', final)


if __name__ == '__main__': unittest.main()
