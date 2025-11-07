self.addEventListener('install', event => {
  console.log('Service Worker Installed');
  event.waitUntil(
    caches.open('fitpro-cache').then(cache => {
      return cache.addAll(['/', '/?homescreen=1']);
    })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
