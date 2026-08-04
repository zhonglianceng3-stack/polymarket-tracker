// Service Worker - 控制缓存策略
const CACHE_NAME = 'polymarket-tracker-v1';
const STATIC_CACHE = 'static-v1';

// 安装事件
self.addEventListener('install', (event) => {
  console.log('SW: 安装');
  self.skipWaiting(); // 立即激活
});

// 激活事件
self.addEventListener('activate', (event) => {
  console.log('SW: 激活');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== STATIC_CACHE) {
            console.log('SW: 清除旧缓存', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim(); // 立即控制所有客户端
});

// 请求拦截 - 写穿透策略
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // API请求 - 网络优先，不缓存
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          console.log('SW: API请求成功', url.pathname);
          return response;
        })
        .catch((error) => {
          console.log('SW: API请求失败', error);
          return new Response(JSON.stringify({ error: 'Network error' }), {
            headers: { 'Content-Type': 'application/json' }
          });
        })
    );
    return;
  }
  
  // 静态资源 - 缓存优先
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.open(STATIC_CACHE).then((cache) => {
        return cache.match(event.request).then((response) => {
          return response || fetch(event.request).then((networkResponse) => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        });
      })
    );
    return;
  }
  
  // 其他请求 - 网络优先
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});

// 消息处理 - 手动清除缓存
self.addEventListener('message', (event) => {
  if (event.data === 'clearCache') {
    caches.keys().then((cacheNames) => {
      cacheNames.forEach((cacheName) => {
        caches.delete(cacheName);
      });
    });
  }
});