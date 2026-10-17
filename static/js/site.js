// Progressive enhancement: navigation and photographs work as normal links
// without JavaScript. No third-party code, trackers, or network dependencies.
const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#primary-navigation');

function closeMenu() {
  navigation?.classList.remove('is-open');
  menuButton?.setAttribute('aria-expanded', 'false');
  menuButton?.setAttribute('aria-label', 'Open navigation');
}

if (menuButton && navigation) {
  menuButton.addEventListener('click', () => {
    const open = menuButton.getAttribute('aria-expanded') !== 'true';
    navigation.classList.toggle('is-open', open);
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  });
  navigation.addEventListener('click', event => {
    if (event.target.closest('a')) closeMenu();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
      closeMenu();
      menuButton.focus();
    }
  });
  window.matchMedia('(min-width: 768px)').addEventListener('change', closeMenu);
}

const viewer = document.querySelector('.photo-viewer');
let photoTrigger;

if (viewer && typeof viewer.showModal === 'function') {
  const image = viewer.querySelector('.photo-viewer-image');
  viewer.querySelector('.photo-viewer-close').addEventListener('click', () => viewer.close());
  viewer.addEventListener('click', event => { if (event.target === viewer) viewer.close(); });
  viewer.addEventListener('close', () => {
    image.removeAttribute('src');
    photoTrigger?.focus({ preventScroll: true });
  });
  document.addEventListener('click', event => {
    const link = event.target.closest('a[data-lightbox]');
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    photoTrigger = link;
    image.src = link.href;
    image.alt = link.querySelector('img')?.alt || 'Photograph from Emmanuel’s journey';
    viewer.showModal();
  });
}

// JavaScript-free mobile navigation remains visible until enhancement is ready.
document.documentElement.classList.add('has-js');
