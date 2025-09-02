// Service Worker for UNDOKAI Scanner PWA
const CACHE_NAME = 'undokai-scanner-v1';
const OFFLINE_URL = '/offline';

// Essential assets to cache for offline functionality
const STATIC_ASSETS = [
  '/',
  '/scanner',
  '/static/css/custom.css',
  '/static/js/scanner.js',
  '/static/js/search.js',
  '/static/js/dashboard.js',
  '/static/manifest.json',
  // External CDN resources
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

// URLs that should always be fetched from network when online
const NETWORK_FIRST = [
  '/api/',
  '/checkin/',
  '/validate_qr'
];

// Install event - cache essential assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching essential assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Installation complete');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Installation failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activation complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategy
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip Chrome extensions
  if (url.protocol === 'chrome-extension:') {
    return;
  }

  // Handle API requests with network-first strategy
  if (NETWORK_FIRST.some(path => url.pathname.startsWith(path))) {
    event.respondWith(networkFirstStrategy(request));
    return;
  }

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigate(request));
    return;
  }

  // Handle other requests with cache-first strategy
  event.respondWith(cacheFirstStrategy(request));
});

// Cache-first strategy for static assets
async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Cache-first strategy failed:', error);
    return new Response('Offline - Resource not available', { status: 503 });
  }
}

// Network-first strategy for API requests
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful API responses for offline access
    if (networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Network request failed, trying cache:', error);
    
    // Try to serve from cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline response for API requests
    return new Response(JSON.stringify({
      error: 'Offline',
      message: 'Dispositivo está offline. Os dados serão sincronizados quando a conexão for restaurada.',
      offline: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Handle navigation requests
async function handleNavigate(request) {
  try {
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.error('Navigation request failed, serving from cache:', error);
    
    // Try to serve cached version
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback to offline page or scanner page
    const offlineResponse = await caches.match('/scanner');
    if (offlineResponse) {
      return offlineResponse;
    }
    
    return new Response('Offline - Page not available', { status: 503 });
  }
}

// Handle background sync for offline data
self.addEventListener('sync', event => {
  if (event.tag === 'offline-checkins') {
    console.log('Service Worker: Syncing offline check-ins');
    event.waitUntil(syncOfflineCheckins());
  }
});

// Sync offline check-ins when connection is restored
async function syncOfflineCheckins() {
  try {
    // Get offline data from IndexedDB or localStorage
    const offlineData = await getOfflineData();
    
    if (offlineData && offlineData.length > 0) {
      console.log('Service Worker: Syncing', offlineData.length, 'offline check-ins');
      
      for (const item of offlineData) {
        try {
          const response = await fetch('/api/checkin', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(item)
          });
          
          if (response.ok) {
            // Remove successfully synced item
            await removeOfflineData(item.id);
          }
        } catch (error) {
          console.error('Failed to sync item:', error);
        }
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Helper function to get offline data (to be implemented based on storage strategy)
async function getOfflineData() {
  // This would typically interact with IndexedDB
  // For now, return empty array as placeholder
  return [];
}

// Helper function to remove synced offline data
async function removeOfflineData(id) {
  // This would typically remove from IndexedDB
  console.log('Removing synced offline data:', id);
}

// Handle push notifications (for future enhancement)
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || 'Nova notificação do UNDOKAI Scanner',
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-192x192.png',
      vibrate: [200, 100, 200],
      tag: 'undokai-notification',
      requireInteraction: true
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'UNDOKAI Scanner', options)
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('Notification clicked:', event);
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/scanner')
  );
});