const CACHE = 'decarie-v247';
const MODELS = 'decarie-models';   // studio-photo cut-out model: kept across app updates
const ASSETS = [
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  'https://unpkg.com/@zxing/browser@0.1.5/umd/zxing-browser.min.js',
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
  'https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js',
  'https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.all(ASSETS.map(u => c.add(u).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE && k !== MODELS).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);

  // Never intercept GitHub API calls (recipe writes / sha lookups).
  if (url.hostname === 'api.github.com') return;

  // Studio photo model + wasm (~80 MB): download once, keep forever (own cache)
  if (url.hostname === 'staticimgly.com') {
    e.respondWith(caches.open(MODELS).then((c) => c.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      if (res && res.status === 200) c.put(e.request, res.clone());
      return res;
    }))));
    return;
  }

  // index.html and config.js: always network-first so SW updates propagate.
  // no-store: skip the browser's 10-minute HTTP cache so a new version shows right away
  if (url.pathname.endsWith('/') || url.pathname.endsWith('index.html') || url.pathname.endsWith('config.js')) {
    e.respondWith(
      fetch(e.request.url, { cache: 'no-store', credentials: 'same-origin' }).then((res) => {
        if (res && res.ok && !url.pathname.endsWith('config.js')) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put('./index.html', copy)); }
        return res;
      }).catch(() => caches.match('./index.html'))
    );
    return;
  }

  // Recipe JSON: network-first so edits appear promptly.
  if (url.hostname === 'raw.githubusercontent.com' && (url.pathname.includes('/recipes/') || url.pathname.includes('/ecom/') || url.pathname.includes('/txns/') || url.pathname.endsWith('/edit.json') || url.pathname.endsWith('/overrides.json'))) {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }

  // data.json / live.json: network-first, cache as fallback for offline.
  if (url.pathname.endsWith('data.json') || url.pathname.endsWith('live.json')) {
    e.respondWith(
      fetch(e.request).then((res) => {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // Everything else: cache-first (CDN libs, icons, etc.)
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      if (res && res.status === 200) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
      }
      return res;
    }))
  );
});
