self.addEventListener('install', (e) => {
  console.log('✅ Service Worker installed');
  e.waitUntil(
    caches.open('fitpro-cache').then((cache) => {
      return cache.addAll(['/', '/manifest.json']);
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});

self.addEventListener('activate', () => {
  console.log('🔥 FIT PRO ready to work offline!');
});