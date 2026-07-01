(function () {
    var AUTH_STATUS_URL = '/auth/status/';
    var HOME_URL = '/';

    function isAuthShell() {
        return Boolean(document.querySelector('.auth-shell'));
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

    function redirectIfLoggedIn() {
        if (!isAuthShell()) {
            return;
        }
        fetchAuthState().then(function (data) {
            if (data && data.authenticated) {
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
                submit.dataset.authSubmitLabel = submit.innerHTML;
                submit.innerHTML = '<i class="bx bx-loader-alt bx-spin" aria-hidden="true"></i> Signing in…';
            });
        });
    }

    function init() {
        bindLoginForms();
        if (isAuthShell()) {
            // After OAuth redirect or returning to login while already signed in.
            setTimeout(redirectIfLoggedIn, 1200);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
