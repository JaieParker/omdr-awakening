// Self-destruct: clear all caches and unregister
// The service worker was causing navigation/cache issues.
// This version cleans up after itself.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
    .then(() => self.registration.unregister())
  );
});
