"""Convert the archived My Maps export without simplifying its coordinates.

Run manually when replacing content/journey/source.kml. Builds local GeoJSON;
the normal website build never contacts Google or a geocoding service.
"""
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'content/journey'
NS = {'k': 'http://www.opengis.net/kml/2.2'}


def convert():
    raw = (SOURCE / 'source.kml').read_bytes()
    root = ET.fromstring(raw)
    lines, points = [], []
    for folder_index, folder in enumerate(root.findall('.//k:Folder', NS)):
        layer = folder.findtext('k:name', namespaces=NS)
        for mark in folder.findall('k:Placemark', NS):
            name = mark.findtext('k:name', namespaces=NS)
            for kind, collection in [('LineString', lines), ('Point', points)]:
                for geometry in mark.findall('.//k:' + kind, NS):
                    coordinates = [list(map(float, c.split(','))) for c in geometry.findtext('k:coordinates', namespaces=NS).split()]
                    collection.append({'type': 'Feature', 'id': f'{kind.lower()}-{len(collection) + 1}',
                                       'properties': {'name': name, 'source_layer': layer, 'source_layer_index': folder_index},
                                       'geometry': {'type': kind, 'coordinates': coordinates[0] if kind == 'Point' else coordinates}})
    main = max(lines, key=lambda x: len(x['geometry']['coordinates']))
    for line in lines: line['properties']['role'] = 'main' if line is main else 'additional'
    for filename, features in [('route.geojson', lines), ('locations.geojson', points)]:
        (SOURCE / filename).write_text(json.dumps({'type': 'FeatureCollection', 'features': features}, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    metadata = {'source_url': 'https://www.google.com/maps/d/viewer?mid=1GTi_1Xw6pLS4P5BCh-5w0k_4JwjN1gY',
                'source_sha256': sha256(raw).hexdigest(), 'exported_on': '2026-10-18',
                'line_count': len(lines), 'point_count': len(points), 'main_line_id': main['id'],
                'main_line_vertices': len(main['geometry']['coordinates']),
                'notes': 'Original geometry preserved. Additional sketches overlap the main route. Point order has no timestamps and must not be treated as a chronological track.'}
    (SOURCE / 'source.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(f'Converted {len(lines)} lines and {len(points)} points without simplification.')


if __name__ == '__main__': convert()
