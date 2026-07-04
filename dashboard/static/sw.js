/*
 * REEL GOD — Service Worker
 * Makes the dashboard installable and gives it a fast, resilient shell.
 * Strategy:
 *   - Static assets (/static/…): cache-first (instant loads, offline-friendly).
 *   - Everything else (pages, /api, socket.io): network-only, never cached, so
 *     you always see live agent state and real-time updates.
 */
const CACHE = 'reelgod-static-v1';
const ASSETS = [
  '/static/style.css',
  '/static/app.js',
  '/static/manifest.webmanifest',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle same-origin GETs; let the browser deal with the rest
  // (POSTs, socket.io upgrades, cross-origin CDN scripts, etc.).
  if (req.method !== 'GET' || url.origin !== self.location.origin) {
    return;
  }

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then((cached) =>
        cached ||
        fetch(req).then((resp) => {
          const copy = resp.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copy)).catch(() => {});
          return resp;
        })
      )
    );
    return;
  }

  // Never cache dynamic pages / API — always go to the network.
  event.respondWith(fetch(req));
});
