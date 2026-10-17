/* Local geometry and journal links; only background tiles use an outside service. */
(() => {
  'use strict';
  const explorer = document.querySelector('#journey-explorer');
  if (!explorer) return;
  const status = document.querySelector('#journey-status');
  const fitButton = document.querySelector('#journey-fit');
  const fullscreenButton = document.querySelector('#journey-fullscreen');
  const yearSelect = document.querySelector('#journey-year');
  const layers = document.querySelector('#journey-layers');
  const mainToggle = document.querySelector('#journey-main');
  const storiesToggle = document.querySelector('#journey-stories');
  const additionalToggle = document.querySelector('#journey-additional');
  const locationsToggle = document.querySelector('#journey-locations');
  const root = new URL('./', new URL(explorer.dataset.siteRoot, location.href));
  const configURL = new URL(explorer.dataset.configUrl, location.href);
  const siteURL = path => new URL(path, root).href;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function say(message, error = false) {
    status.textContent = message;
    status.dataset.state = error ? 'error' : 'ready';
  }

  async function json(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Map data unavailable (${response.status})`);
    return response.json();
  }

  function markerIcon(label, endpoint = false) {
    // Labels are generated numbers or fixed S/E characters, never HTML from data.
    return L.divIcon({ className: `journey-marker${endpoint ? ' journey-marker-endpoint' : ''}`,
      html: `<span>${label}</span>`, iconSize: [29, 29], iconAnchor: [14, 14], popupAnchor: [0, -13] });
  }

  function popup(place) {
    const content = document.createElement('div');
    content.className = 'journey-popup';
    const heading = document.createElement('h3');
    heading.textContent = place.name;
    content.append(heading);
    if (place.image) {
      const image = document.createElement('img');
      image.src = siteURL(place.image);
      image.alt = `Photograph accompanying “${place.post_title}”`;
      image.loading = 'lazy';
      image.width = 230;
      content.append(image);
    }
    const link = document.createElement('a');
    link.href = siteURL(place.post_path);
    link.textContent = place.post_title;
    content.append(link);
    const note = document.createElement('p');
    note.className = 'journey-popup-note';
    note.textContent = `Published ${place.date_label}. Approximate location of the place mentioned in this entry.`;
    content.append(note);
    return content;
  }

  async function start() {
    if (typeof L === 'undefined') throw new Error('Map library unavailable');
    const config = await json(configURL);
    const route = await json(new URL(config.route_file, configURL));
    const mainFeature = route.features.find(f => f.properties.role === 'main');
    if (!mainFeature) throw new Error('Recorded route unavailable');
    const map = L.map('journey-map', { minZoom: 3, maxZoom: config.tiles.max_zoom,
      scrollWheelZoom: true, zoomAnimation: !reducedMotion, fadeAnimation: !reducedMotion });
    L.tileLayer(config.tiles.url, { maxZoom: config.tiles.max_zoom,
      attribution: `<a href="${config.tiles.attribution_url}">${config.tiles.attribution}</a>`
    }).on('tileerror', () => say('Some background tiles could not load. The route and journal places are still available.', true)).addTo(map);
    L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);
    const routeHalo = L.geoJSON(mainFeature, { style: { color: '#faf8f3', weight: 7, opacity: .85 }, interactive: false });
    const routeLine = L.geoJSON(mainFeature, { style: { color: '#354b30', weight: 3.5, opacity: .95 }, smoothFactor: 0 });
    const endpoints = L.layerGroup();
    const coordinates = mainFeature.geometry.coordinates;
    for (const [coordinate, label, text] of [
      [coordinates[0], 'S', 'Start of the recorded route · Paris region'],
      [coordinates[coordinates.length - 1], 'E', 'End of the recorded route · Bosnia and Herzegovina']
    ]) {
      L.marker([coordinate[1], coordinate[0]], { icon: markerIcon(label, true), title: text, alt: text }).bindPopup(text).addTo(endpoints);
    }
    const mainLayer = L.layerGroup([routeHalo, routeLine, endpoints]).addTo(map);
    const additionalLayer = L.geoJSON(route.features.filter(f => f.properties.role !== 'main'), {
      style: { color: '#a97850', weight: 2.5, dashArray: '5 6', opacity: .85 }, smoothFactor: 0,
      onEachFeature(feature, layer) { layer.bindPopup(document.createTextNode(`Original route sketch: ${feature.properties.name}`)); }
    });
    const storyLayer = L.layerGroup().addTo(map);
    const markers = new Map();
    const items = new Map([...document.querySelectorAll('.journey-story')].map(item => [item.dataset.placeId, item]));
    config.places.forEach((place, index) => {
      const marker = L.marker([place.coordinates[1], place.coordinates[0]], {
        icon: markerIcon(index + 1), title: `${place.name} · ${place.post_title}`, alt: `Journal place: ${place.name}`, riseOnHover: true
      }).bindPopup(() => popup(place), { maxWidth: 265 });
      marker.on('popupopen', () => {
        items.forEach(item => item.classList.remove('is-selected'));
        items.get(place.id)?.classList.add('is-selected');
      });
      marker.on('popupclose', () => items.get(place.id)?.classList.remove('is-selected'));
      markers.set(place.id, marker);
    });

    function fit() { const padding = map.getSize().x < 450 ? 14 : 32; map.fitBounds(routeLine.getBounds(), { padding: [padding, padding], animate: false }); }
    fit();
    fitButton.disabled = false;
    fitButton.addEventListener('click', fit);
    mainToggle.addEventListener('change', () => mainToggle.checked ? mainLayer.addTo(map) : map.removeLayer(mainLayer));
    additionalToggle.addEventListener('change', () => additionalToggle.checked ? additionalLayer.addTo(map) : map.removeLayer(additionalLayer));
    storiesToggle.addEventListener('change', () => storiesToggle.checked ? storyLayer.addTo(map) : map.removeLayer(storyLayer));

    function filter() {
      storyLayer.clearLayers();
      let count = 0;
      config.places.forEach(place => {
        const visible = yearSelect.value === 'all' || place.date.startsWith(yearSelect.value);
        items.get(place.id).hidden = !visible;
        if (visible) { markers.get(place.id).addTo(storyLayer); count += 1; }
      });
      document.querySelector('#journey-empty').hidden = count !== 0;
      say(`${count} journal places shown.`);
      map.closePopup();
    }
    [...new Set(config.places.map(place => place.date.slice(0, 4)))].sort().forEach(year => {
      const option = document.createElement('option'); option.value = year; option.textContent = year; yearSelect.append(option);
    });
    yearSelect.disabled = false;
    yearSelect.addEventListener('change', filter);
    filter();
    document.querySelectorAll('.journey-locate').forEach(button => {
      button.disabled = false;
      button.addEventListener('click', () => {
        const marker = markers.get(button.dataset.placeId);
        storiesToggle.checked = true;
        if (!map.hasLayer(storyLayer)) storyLayer.addTo(map);
        map.setView(marker.getLatLng(), 10, { animate: !reducedMotion });
        marker.openPopup();
        if (window.matchMedia('(max-width: 650px)').matches) document.querySelector('#journey-map').scrollIntoView({ behavior: reducedMotion ? 'instant' : 'smooth', block: 'center' });
      });
    });

    let originalLocations;
    let locationRequest;
    locationsToggle.addEventListener('change', async () => {
      if (!locationsToggle.checked) { if (originalLocations) map.removeLayer(originalLocations); return; }
      try {
        if (!originalLocations) {
          say('Loading the original map points…');
          locationRequest ||= json(new URL(config.locations_file, configURL));
          const data = await locationRequest;
          const seen = new Set();
          const pointRenderer = L.canvas();
          originalLocations = L.geoJSON(data, {
            filter(feature) { const key = feature.geometry.coordinates.slice(0, 2).join(','); if (seen.has(key)) return false; seen.add(key); return true; },
            pointToLayer(feature, latlng) { return L.circleMarker(latlng, { renderer: pointRenderer, radius: 3, color: '#8c6650', weight: 1, fillOpacity: .55 }); },
            onEachFeature(feature, layer) { layer.bindPopup(document.createTextNode(`${feature.properties.name} · Original map point; no date recorded.`)); }
          });
        }
        if (locationsToggle.checked) originalLocations.addTo(map);
        say('Original map points loaded. Repeated coordinates are shown once.');
      } catch (error) {
        locationRequest = undefined;
        locationsToggle.checked = false;
        say('Original map points could not load. Please try again.', true);
      }
    });
    layers.disabled = false;
    if (document.fullscreenEnabled) {
      fullscreenButton.hidden = false;
      fullscreenButton.addEventListener('click', async () => {
        try { if (document.fullscreenElement === explorer) await document.exitFullscreen(); else await explorer.requestFullscreen(); }
        catch (error) { say('Full screen is unavailable in this browser.', true); }
      });
      document.addEventListener('fullscreenchange', () => {
        fullscreenButton.textContent = document.fullscreenElement === explorer ? 'Exit full screen' : 'Full screen';
        map.invalidateSize({ pan: false });
      });
    }
    new ResizeObserver(() => map.invalidateSize({ pan: false })).observe(document.querySelector('#journey-map'));
    explorer.dataset.ready = 'true';
  }

  start().catch(() => say('The interactive map could not load. Please reload, or use the journal links and route downloads below.', true));
})();
