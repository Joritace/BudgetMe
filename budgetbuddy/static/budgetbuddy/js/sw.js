/* BudgetMe service worker — instant PWA shell on cold start. */
'use strict';

var SW_VERSION = 'bb-sw-2';
var STATIC_CACHE = SW_VERSION + '-static';
var PAGE_CACHE = SW_VERSION + '-pages';

var APP_PATHS = ['/', '/transfer/', '/savings/', '/budget/', '/profile/'];

function isAppPath(pathname) {
    return APP_PATHS.indexOf(pathname) !== -1;
}

function isAuthPath(pathname) {
    return pathname.indexOf('/accounts/') === 0 || pathname.indexOf('/admin/') === 0;
}

function isTurboRequest(request) {
    return request.headers.get('X-BB-Turbo') === '1';
}

function isAppHtmlRequest(request) {
    if (request.method !== 'GET') {
        return false;
    }
    var url = new URL(request.url);
    if (url.origin !== self.location.origin) {
        return false;
    }
    if (isAuthPath(url.pathname) || url.pathname.indexOf('/api/') === 0) {
        return false;
    }
    if (request.mode === 'navigate' && isAppPath(url.pathname)) {
        return true;
    }
    var accept = request.headers.get('Accept') || '';
    return accept.indexOf('text/html') !== -1 && isAppPath(url.pathname);
}

function isStaticRequest(request) {
    if (request.method !== 'GET') {
        return false;
    }
    var url = new URL(request.url);
    return url.pathname.indexOf('/static/') === 0
        || url.pathname === '/site.webmanifest'
        || url.pathname === '/icon-192.png'
        || url.pathname === '/icon-512.png'
        || url.pathname === '/apple-touch-icon.png';
}

function cachePut(request, response) {
    if (!response || !response.ok) {
        return;
    }
    var cacheName = isStaticRequest(request) ? STATIC_CACHE : PAGE_CACHE;
    caches.open(cacheName).then(function (cache) {
        cache.put(request, response);
    });
}

function staleWhileRevalidate(request) {
    return caches.open(PAGE_CACHE).then(function (cache) {
        return cache.match(request).then(function (cached) {
            var network = fetch(request).then(function (response) {
                cachePut(request, response.clone());
                return response;
            });

            if (cached) {
                network.catch(function () {});
                return cached;
            }

            return network.catch(function () {
                return cached;
            });
        });
    });
}

function networkFirst(request) {
    return fetch(request).then(function (response) {
        cachePut(request, response.clone());
        return response;
    }).catch(function () {
        return caches.match(request).then(function (cached) {
            if (cached) {
                return cached;
            }
            throw new Error('Offline');
        });
    });
}

self.addEventListener('install', function (event) {
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(keys.map(function (key) {
                if (key.indexOf(SW_VERSION) === 0) {
                    return undefined;
                }
                return caches.delete(key);
            }));
        }).then(function () {
            return self.clients.claim();
        })
    );
});

self.addEventListener('message', function (event) {
    if (!event.data || event.data.type !== 'CLEAR_CACHES') {
        return;
    }
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(keys.map(function (key) {
                return caches.delete(key);
            }));
        })
    );
});

self.addEventListener('fetch', function (event) {
    var request = event.request;

    if (isStaticRequest(request)) {
        event.respondWith(
            caches.match(request).then(function (cached) {
                var network = fetch(request).then(function (response) {
                    cachePut(request, response.clone());
                    return response;
                });
                return cached || network;
            })
        );
        return;
    }

    if (!isAppHtmlRequest(request)) {
        return;
    }

    event.respondWith(networkFirst(request));
});
