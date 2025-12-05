// 服务工作者 - 贵州天气健康PWA
const CACHE_NAME = 'guizhou-weather-health-v1.0';
const OFFLINE_URL = 'offline.html';

// 需要缓存的资源
const urlsToCache = [
    '/',
    '/manifest.json',
    '/icon-192.png',
    '/icon-512.png',
    '/offline.html'
];

// 安装事件 - 初次安装时缓存必要资源
self.addEventListener('install', event => {
    console.log(' Service Worker 安装中...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log(' 缓存核心资源');
                return cache.addAll(urlsToCache);
            })
            .then(() => {
                console.log('✅ Service Worker 安装完成');
                return self.skipWaiting();
            })
    );
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', event => {
    console.log(' Service Worker 激活中...');

    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log(`️ 删除旧缓存: ${cacheName}`);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('✅ Service Worker 激活完成');
            return self.clients.claim();
        })
    );
});

// 获取事件 - 拦截网络请求
self.addEventListener('fetch', event => {
    // 跳过非GET请求
    if (event.request.method !== 'GET') return;

    // 处理API请求（实时天气数据）
    if (event.request.url.includes('open-meteo.com')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // 克隆响应以进行缓存
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // 网络失败时尝试返回缓存
                    return caches.match(event.request)
                        .then(cachedResponse => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            // 返回离线数据
                            return new Response(
                                JSON.stringify({
                                    status: 'offline',
                                    message: '网络连接失败，请检查网络',
                                    data: { temperature: 20, humidity: 60 },
                                    timestamp: new Date().toISOString()
                                }),
                                {
                                    headers: { 'Content-Type': 'application/json' }
                                }
                            );
                        });
                })
        );
        return;
    }

    // 处理页面资源请求（缓存优先策略）
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                // 如果有缓存，返回缓存
                if (cachedResponse) {
                    return cachedResponse;
                }

                // 否则从网络获取
                return fetch(event.request)
                    .then(response => {
                        // 只缓存成功的响应
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // 克隆响应进行缓存
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(() => {
                        // 如果是页面请求且网络失败，返回离线页面
                        if (event.request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }

                        return new Response('网络连接失败', {
                            status: 408,
                            headers: { 'Content-Type': 'text/plain' }
                        });
                    });
            })
    );
});

// 后台同步 - 天气数据预加载
self.addEventListener('sync', event => {
    if (event.tag === 'sync-weather-data') {
        console.log('️ 后台同步天气数据...');
        event.waitUntil(syncWeatherData());
    }
});

// 消息推送处理
self.addEventListener('push', event => {
    if (!event.data) return;

    const data = event.data.json();
    const options = {
        body: data.body || '贵州天气健康提醒',
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title || '天气健康通知', options)
    );
});

// 通知点击处理
self.addEventListener('notificationclick', event => {
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});

// 同步天气数据的函数
async function syncWeatherData() {
    try {
        const cache = await caches.open(CACHE_NAME);

        // 预缓存一些城市的数据
        const cities = [
            { name: '贵阳市', lat: 26.6470, lon: 106.6302 },
            { name: '毕节市', lat: 27.3026, lon: 105.2840 },
            { name: '遵义市', lat: 27.7064, lon: 106.9373 }
        ];

        for (const city of cities) {
            const apiUrl = `https://api.open-meteo.com/v1/forecast?latitude=${city.lat}&longitude=${city.lon}&current=temperature_2m,relative_humidity_2m&forecast_days=1`;

            try {
                const response = await fetch(apiUrl);
                if (response.ok) {
                    await cache.put(`weather-${city.name}`, response.clone());
                    console.log(`✅ ${city.name} 天气数据已预缓存`);
                }
            } catch (error) {
                console.warn(`⚠️ ${city.name} 数据同步失败:`, error);
            }
        }

        return Promise.resolve('天气数据同步完成');
    } catch (error) {
        console.error('❌ 同步失败:', error);
        return Promise.reject(error);
    }
