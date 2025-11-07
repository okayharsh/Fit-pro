# 1️⃣ MANIFEST
# 2️⃣ SERVICE WORKER
# 3️⃣ SMART INSTALL BUTTON (this new one)



self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('fitpro-cache-v1').then(cache => {
      return cache.addAll([
        '/',
        '/?utm_source=pwa',
        '/manifest.json'
      ]);
    })
  );
  console.log('✅ Service Worker installed');
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
