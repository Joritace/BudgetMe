(function () {
    'use strict';

    var client = null;
    var channel = null;
    var refreshTimer = null;
    var started = false;

    var REALTIME_TABLES = [
        'budgetbuddy_transaction',
        'budgetbuddy_mobilemoneytransaction',
        'budgetbuddy_savingsdeposit',
    ];

    function getConfig() {
        var el = document.getElementById('supabase-realtime-config');
        if (!el) {
            return null;
        }
        try {
            return JSON.parse(el.textContent);
        } catch (err) {
            return null;
        }
    }

    function debouncedRefresh() {
        clearTimeout(refreshTimer);
        refreshTimer = window.setTimeout(function () {
            if (window.BudgetMe && typeof window.BudgetMe.refreshFromRealtime === 'function') {
                window.BudgetMe.refreshFromRealtime();
            }
        }, 350);
    }

    function fetchToken(cfg) {
        return fetch(cfg.tokenUrl, {
            credentials: 'same-origin',
            headers: { Accept: 'application/json' },
        }).then(function (res) {
            if (!res.ok) {
                throw new Error('Token request failed');
            }
            return res.json();
        }).then(function (data) {
            return data.token;
        });
    }

    function subscribe(cfg) {
        if (!window.supabase || !window.supabase.createClient) {
            return;
        }

        client = window.supabase.createClient(cfg.url, cfg.anonKey);

        fetchToken(cfg).then(function (token) {
            return client.realtime.setAuth(token);
        }).then(function () {
            if (channel) {
                client.removeChannel(channel);
            }

            channel = client.channel('budgetme-profile-' + cfg.profileId);

            REALTIME_TABLES.forEach(function (table) {
                channel.on(
                    'postgres_changes',
                    {
                        event: '*',
                        schema: 'public',
                        table: table,
                        filter: 'profile_id=eq.' + cfg.profileId,
                    },
                    debouncedRefresh
                );
            });

            channel.subscribe();
            started = true;
        }).catch(function () {
            started = false;
        });
    }

    function stop() {
        if (client && channel) {
            client.removeChannel(channel);
            channel = null;
        }
        started = false;
    }

    function start() {
        var cfg = getConfig();
        if (!cfg) {
            return;
        }
        subscribe(cfg);
    }

    function refreshAuth() {
        if (!started) {
            start();
            return;
        }
        var cfg = getConfig();
        if (!cfg || !client) {
            return;
        }
        fetchToken(cfg).then(function (token) {
            return client.realtime.setAuth(token);
        }).catch(function () {});
    }

    window.BudgetMeRealtime = {
        start: start,
        stop: stop,
        refreshAuth: refreshAuth,
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }

    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible') {
            refreshAuth();
        }
    });
})();
