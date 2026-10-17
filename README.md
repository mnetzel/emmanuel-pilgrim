# Emmanuel, French Pilgrim

Blog: https://mnetzel.github.io/emmanuel-pilgrim/

Prosta strona statyczna: HTML, CSS i niewielki JavaScript. Bez kodu, stylów,
kontenerów i usług Weebly. Python i szablony Jinja są używane wyłącznie lokalnie
do składania plików; odwiedzający dostaje gotowe strony z GitHub Pages.

## Gdzie co jest

| Katalog / plik | Przeznaczenie |
| --- | --- |
| `content/posts/<slug>/body.html` | Treść jednego wpisu: akapity, linki i zdjęcia |
| `content/posts/<slug>/post.json` | Tytuł, data, adres, identyfikator i komentarze wpisu |
| `content/pages/` | Welcome, About, Contact, FAQ: osobno treść HTML i ustawienia JSON |
| `content/site.json` | Nazwa bloga, menu, liczba wpisów na stronie i zdjęcie nagłówka bloga |
| `templates/base.html` | Wspólny szkielet i metadane strony |
| `templates/components/` | Nagłówek, menu, zdjęcie tytułowe, wpis, archiwa, komentarze, paginacja, podgląd zdjęć |
| `templates/page.html`, `listing.html`, `post-page.html` | Układy zwykłej strony, listy wpisów i pojedynczego wpisu |
| `static/css/site.css` | Kolory, typografia, odstępy, układy i widok mobilny |
| `static/css/fonts.css`, `static/fonts/` | Lokalne fonty Cardo, Crimson Text i Quattrocento Sans |
| `static/js/site.js` | Menu mobilne i dostępny z klawiatury podgląd zdjęć |
| `static/images/` | Oryginalne pliki fotografii z czytelnymi nazwami |
| `scripts/build.py` | Składanie całej strony i automatyczne tworzenie archiwów oraz mapy strony |
| `tests/` | Kontrola tekstów, zdjęć, komentarzy, adresów i struktury HTML |
| `docs/` | Gotowe pliki publikowane przez GitHub Pages; nie edytować ręcznie |

## Budowanie i podgląd

Wymagany Python 3.10 lub nowszy.

```sh
python -m pip install -r requirements.txt
python scripts/build.py
python scripts/check.py
python -m http.server 8000 --directory docs
```

Podgląd: http://localhost:8000/. Po zmianie treści, szablonów lub zasobów uruchom
ponownie budowanie i kontrolę. Skrypt budujący odtwarza cały katalog `docs/`,
dlatego wszystkie własne zmiany należy zapisywać w katalogach źródłowych.

## Dodawanie wpisu

1. Utwórz `content/posts/nazwa-wpisu/`.
2. Dodaj `post.json`, na przykład:

```json
{
  "slug": "nazwa-wpisu",
  "path": "blog/nazwa-wpisu/index.html",
  "title": "The next part of the journey",
  "date": "2026-10-18",
  "date_label": "18/10/2026",
  "anchor_id": "post-nazwa-wpisu",
  "comments": []
}
```

3. Dodaj `body.html` z normalnymi elementami HTML:

```html
<p>Treść wpisu...</p>

<figure class="journey-photo">
  <a href="assets/images/nazwa-zdjecia.jpg" data-lightbox>
    <img src="assets/images/nazwa-zdjecia.jpg" alt="Opis zdjęcia"
         width="1824" height="1368" loading="lazy" decoding="async">
  </a>
</figure>
```

4. Zdjęcie dodaj do `static/images/`; wymiary muszą odpowiadać plikowi.
5. Uruchom budowanie i kontrolę. Strona wpisu, indeks, miesiąc w archiwum,
menu archiwów, paginacja i sitemap powstaną automatycznie.

Odnośniki wewnątrz treści zapisuj względem głównego katalogu strony, np.
`blog/inny-wpis/index.html`. Skrypt zamienia je na prawidłowe odnośniki względne
na każdej stronie, także w głębokich archiwach.

## Publikowanie

GitHub Pages publikuje `main` → `/docs`. Do commita dodawaj źródła i wynik
budowania. Workflow `Check static site` ponownie buduje stronę, sprawdza testy
i wykrywa sytuację, gdy wygenerowane pliki nie odpowiadają źródłom.

## Zachowana zawartość i kontrola regresji

Przebudowa zachowuje wszystkie 38 oryginalnych wpisów, cztery strony treści,
75 dotychczasowych adresów, fotografie i oba istniejące komentarze czytelników.
Daty, autorzy oraz identyfikatory komentarzy są zachowane. Formularza dodawania
komentarzy nie ma, ponieważ wymagałby odrębnej usługi.

`tests/fixtures/` zawiera niezależny zapis stanu sprzed przebudowy: odciski
tekstów, kolejność zdjęć i ich sumy SHA-256, komentarze oraz adresy. Testy
pozwalają dodawać nowe wpisy, ale chronią historyczne treści przed przypadkowym
usunięciem lub zmianą. Celowa korekta historycznej treści wymaga świadomej
aktualizacji odpowiedniego rekordu kontrolnego w `tests/fixtures/`.

Pierwotny import Weebly i poprzednie wersje kodu pozostają dostępne w historii
Git. Nie są używane do budowania ani działania obecnej strony. Lokalne foldery
`assets/` i `output/` z próbami zdjęć i propozycjami logo pozostają poza stroną.

## Journey Map

`Journey Map` is a separate page (`journey-map.html`) in the main navigation.
The map uses a local, licensed copy of Leaflet 1.9.4 in `static/vendor/leaflet/`.
Only the OpenStreetMap background tiles are fetched from an external service;
there is no Google Maps runtime, geocoding API, account, or API key.

- `content/journey/source.kml`: archived original export of Emmanuel’s map.
- `content/journey/source.json`: provenance, checksum and geometry inventory.
- `content/journey/route.geojson`: all eight original polylines, unchanged.
- `content/journey/locations.geojson`: all 2567 original points, including repeats.
- `content/journey/map.json`: tile provider and local data file names.
- `content/journey/entry-locations.json`: one reviewed location per entry, with evidence, certainty, explanation and coordinate sources.
- `scripts/journey_locations.py`: offline projection and date interpolation along the directed recorded route.
- `templates/journey-map.html`: accessible page, story list and controls.
- `static/css/journey-map.css`, `static/js/journey-map.js`: map-specific presentation and interactions.

The default view shows the main recorded route and journal places. Supplementary
sketches and original points are separate, optional layers. Point data is loaded
only when requested, and exact duplicate coordinates are displayed once without
changing the archived data. The source has no point timestamps; its point order
must not be interpreted as a chronological GPS track. No route smoothing or
new route calculation is performed by the importer.

All 38 entries have a marker: 22 identified places (ochre) and 16 estimates
(blue, with a dashed border). Each marker and sidebar item explains its basis.
Both year and location-type filters are available. The complete review is also
downloadable from the page; original post text and photos are unchanged.

To add a journal marker, add a review to `content/journey/entry-locations.json`:

```json
{
  "post": "existing-post-folder-name",
  "name": "Place name",
  "country": "Country",
  "status": "documented",
  "method": "named_place",
  "evidence": ["An exact excerpt from the entry naming the visited place."],
  "explanation": "Why this place represents the entry, including any timing caveat.",
  "coordinates": [17.0325, 51.11],
  "coordinate_source": "https://www.wikidata.org/wiki/Q1799",
  "location_precision": "town",
  "reviewed_text_sha256": "SHA-256 of whitespace-normalized BeautifulSoup body text"
}
```

Coordinates are **longitude, latitude** (GeoJSON order). Preserve their source.
`named_place` and `identified_place` are documented locations; the latter also
records an `identification_source`. A named place may represent an earlier visit
described in the entry, not the exact writing location or every event in it.
Future destinations must not be treated as completed visits.

For a regional inference, use `status: estimated`, `method: content_estimate`
and reference coordinates with a source. The builder projects the reference onto
the relevant section of the recorded line and keeps it blue. Explain uncertainty
explicitly. For an entry without a usable place, use `method: date_interpolation`
and omit coordinates: the builder computes a position between the neighbouring
dated references, in proportion to elapsed days and cumulative distance along
the original polyline. References can themselves be regional estimates; this is
disclosed in the result. The first entry uses `route_start` rather than an
unsupported backward extrapolation. A confirmed place beyond the supplied line
(Dubrovnik) uses `on_recorded_route: false` and is not an interpolation anchor.

Projection proceeds in chronological order, so return passages through Lithuania,
Poland and Târgu Mureș are not confused with earlier visits. The line has no
timestamps and is a coarse route, not a measured daily track: constant progress
between publication dates is only a visual estimate. Internal route offsets are
not claimed as actual kilometres walked. The recorded geometry is never changed.

Dates and titles come from the posts. Popups use the first accompanying photograph;
it is not claimed to depict the exact marker position. The review hash uses
`sha256(' '.join(BeautifulSoup(body, 'html.parser').get_text(' ', strip=True).split()).encode()).hexdigest()`.
The build requires one review per post and detects text changes that need a new
location review. Rebuild and run the checks after editing. Generated coordinates,
reference IDs, dates and interpolation fractions are inspectable in
`docs/assets/data/journey/config.json`; do not edit that generated file.

If the source map changes, replace `source.kml`, then run
`python scripts/import_journey.py` followed by the normal build and checks.
Keep the export date in `source.json` current. The importer runs manually and
never downloads data during a website build.

Tile URL and attribution are configurable in `map.json`. Standard OSM tiles
must retain visible attribution, use normal browser caching and Referer headers,
and must not be bulk downloaded, prefetched, or packaged for offline use.
Policy: https://operations.osmfoundation.org/policies/tiles/.
Town-coordinate sources are recorded per marker (Wikidata, CC0).
