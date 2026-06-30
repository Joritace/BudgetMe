(function () {
    var AUTH_STATUS_URL = '/auth/status/';
    var HOME_URL = '/';
    var POLL_MS = 2500;

    function isAuthShell() {
        return Boolean(document.querySelector('.auth-shell'));
    }

    function isAppShell() {
        return Boolean(document.querySelector('.sidebar, .bottom-nav, .dash'));
    }

    function fetchAuthState() {
        return fetch(AUTH_STATUS_URL, {
            credentials: 'same-origin',
            headers: { Accept: 'application/json' },
            cache: 'no-store',
        }).then(function (response) {
            if (!response.ok) {
                return null;
            }
            return response.json();
        }).catch(function () {
            return null;
        });
    }

    function syncAuthState() {
        return fetchAuthState().then(function (data) {
            if (!data) {
                return;
            }
            if (isAuthShell() && data.authenticated) {
                window.location.replace(HOME_URL);
                return;
            }
            if (isAppShell() && !data.authenticated) {
                window.location.replace(HOME_URL);
            }
        });
    }

    function bindLoginForms() {
        document.querySelectorAll('.auth-form').forEach(function (form) {
            if (form.dataset.authBound === '1') {
                return;
            }
            form.dataset.authBound = '1';

            form.addEventListener('submit', function () {
                var submit = form.querySelector('[type="submit"]');
                if (!submit || submit.disabled) {
                    return;
                }
                submit.disabled = true;
                submit.setAttribute('aria-busy', 'true');
                var label = submit.innerHTML;
                submit.dataset.authSubmitLabel = label;
                submit.innerHTML = '<i class="bx bx-loader-alt bx-spin" aria-hidden="true"></i> Signing in…';
            });
        });
    }

    function startPolling() {
        if (!isAuthShell() && !isAppShell()) {
            return;
        }
        setInterval(syncAuthState, POLL_MS);
    }

    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible') {
            syncAuthState();
        }
    });

    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            syncAuthState();
        }
    });

    window.addEventListener('focus', syncAuthState);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            bindLoginForms();
            startPolling();
        });
    } else {
        bindLoginForms();
        startPolling();
    }
})();
