// Only local interactions; no hosted Weebly runtime or analytics.
document.querySelectorAll('.hamburger').forEach(button => {
  button.setAttribute('aria-expanded', 'false');
  button.addEventListener('click', event => {
    event.preventDefault();
    const open = document.body.classList.toggle('static-menu-open');
    button.setAttribute('aria-expanded', String(open));
  });
});
const viewer = document.createElement('dialog');
viewer.className = 'photo-viewer';
viewer.innerHTML = '<button type="button" aria-label="Close image">×</button><img alt="">';
document.body.append(viewer);
viewer.querySelector('button').addEventListener('click', () => viewer.close());
viewer.addEventListener('click', event => { if (event.target === viewer) viewer.close(); });
document.querySelectorAll('a[data-lightbox]').forEach(link => {
  link.addEventListener('click', event => {
    event.preventDefault();
    const image = viewer.querySelector('img');
    image.src = link.href;
    image.alt = link.querySelector('img')?.alt || 'Photograph from the pilgrimage';
    viewer.showModal();
  });
});
