const CACHE_NAME = 'asha-vani-cache-v4';

const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png'
];


// ===============================
// INSTALL
// ===============================
self.addEventListener('install', (event) => {

  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {

      console.log('[Service Worker] Caching core assets');

      return cache.addAll(ASSETS_TO_CACHE);

    })
  );

  self.skipWaiting();
});


// ===============================
// ACTIVATE
// ===============================
self.addEventListener('activate', (event) => {

  event.waitUntil(

    caches.keys().then((cacheNames) => {

      return Promise.all(

        cacheNames.map((cache) => {

          if (cache !== CACHE_NAME) {

            console.log(
              '[Service Worker] Deleting old cache:',
              cache
            );

            return caches.delete(cache);

          }

        })

      );

    })

  );

  self.clients.claim();

});


// ===============================
// FETCH
// ===============================
self.addEventListener('fetch', (event) => {

  const request = event.request;
  const url = new URL(request.url);


  // ==========================================
  // NEVER CACHE API / BACKEND REQUESTS
  // ==========================================
  if (
    url.port === '8000' ||
    url.pathname.startsWith('/api/') ||
    url.pathname.includes('/chat') ||
    url.pathname.includes('/sync')
  ) {

    return;

  }


  // ==========================================
  // HTML PAGES
  // ALWAYS TRY NETWORK FIRST
  // ==========================================
  if (
    request.mode === 'navigate' ||
    request.headers.get('accept')?.includes('text/html')
  ) {

    event.respondWith(

      fetch(request)
        .then((response) => {

          // Save latest HTML in cache
          const responseClone = response.clone();

          caches.open(CACHE_NAME).then((cache) => {

            cache.put(request, responseClone);

          });

          return response;

        })

        .catch(() => {

          console.log(
            '[Service Worker] Network unavailable. Loading cached index.html'
          );

          return caches.match('./index.html');

        })

    );

    return;

  }


  // ==========================================
  // OTHER STATIC FILES
  // CACHE FIRST
  // ==========================================
  event.respondWith(

    caches.match(request).then((cachedResponse) => {

      if (cachedResponse) {

        return cachedResponse;

      }

      return fetch(request)
        .then((response) => {

          const responseClone = response.clone();

          caches.open(CACHE_NAME).then((cache) => {

            cache.put(request, responseClone);

          });

          return response;

        })
        .catch(() => {

          return caches.match('./index.html');

        });

    })

  );

});