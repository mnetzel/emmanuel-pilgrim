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
