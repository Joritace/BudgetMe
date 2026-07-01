(function () {
    'use strict';

    var loaderEl = null;
    var loaderCount = 0;
    var loaderTimer = null;

    function getLoader() {
        if (!loaderEl) {
            loaderEl = document.getElementById('bb-loader');
        }
        return loaderEl;
    }

    function showLoader(message, subtext) {
        var el = getLoader();
        if (!el) {
            return;
        }
        loaderCount += 1;
        if (message) {
            var text = el.querySelector('.bb-loader__text');
            if (text) {
                text.textContent = message;
            }
        }
        if (subtext) {
            var sub = el.querySelector('.bb-loader__sub');
            if (sub) {
                sub.textContent = subtext;
            }
        }
        el.hidden = false;
        el.classList.remove('is-leaving');
        el.setAttribute('aria-busy', 'true');
        document.body.classList.add('is-loading');
    }

    function hideLoader() {
        var el = getLoader();
        if (!el) {
            return;
        }
        loaderCount = Math.max(0, loaderCount - 1);
        if (loaderCount > 0) {
            return;
        }
        el.classList.add('is-leaving');
        el.setAttribute('aria-busy', 'false');
        window.setTimeout(function () {
            if (loaderCount === 0) {
                el.hidden = true;
                el.classList.remove('is-leaving');
                document.body.classList.remove('is-loading');
            }
        }, 280);
    }

    function debounceLoader(fn, delay) {
        return function () {
            var args = arguments;
            clearTimeout(loaderTimer);
            loaderTimer = window.setTimeout(function () {
                showLoader();
            }, delay || 120);
            return fn.apply(null, args).finally(function () {
                clearTimeout(loaderTimer);
                hideLoader();
            });
        };
    }

    function movePeriodSlider(tabs, activeBtn) {
        var slider = tabs.querySelector('[data-period-slider]');
        if (!slider || !activeBtn) {
            return;
        }
        var index = Array.prototype.indexOf.call(
            tabs.querySelectorAll('.period-tabs__btn'),
            activeBtn,
        );
        slider.style.transform = 'translateX(' + (index * 100) + '%)';
    }

    function initPeriodTabs(tabs) {
        var endpoint = tabs.dataset.endpoint;
        var targetId = tabs.dataset.target;
        var subtitleId = tabs.dataset.subtitle;
        if (!endpoint || !targetId) {
            return;
        }

        var target = document.getElementById(targetId);
        var subtitle = subtitleId ? document.getElementById(subtitleId) : null;
        var buttons = tabs.querySelectorAll('.period-tabs__btn');
        var active = tabs.querySelector('.period-tabs__btn.is-active');
        if (active) {
            movePeriodSlider(tabs, active);
        }

        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                if (btn.classList.contains('is-active')) {
                    return;
                }

                buttons.forEach(function (b) {
                    b.classList.remove('is-active');
                    b.removeAttribute('aria-current');
                });
                btn.classList.add('is-active');
                btn.setAttribute('aria-current', 'true');
                movePeriodSlider(tabs, btn);

                if (target) {
                    target.classList.add('is-loading');
                }
                showLoader('Updating…', 'Fetching your transactions');

                var url = endpoint + '?period=' + encodeURIComponent(btn.dataset.period);
                fetch(url, {
                    credentials: 'same-origin',
                    headers: { Accept: 'application/json' },
                })
                    .then(function (res) {
                        if (!res.ok) {
                            throw new Error('Failed to load');
                        }
                        return res.json();
                    })
                    .then(function (data) {
                        if (!target) {
                            return;
                        }
                        target.classList.remove('is-loading');
                        target.innerHTML = data.html;
                        target.classList.add('is-entering');
                        window.setTimeout(function () {
                            target.classList.remove('is-entering');
                        }, 420);
                        if (subtitle && data.label) {
                            var prefix = tabs.dataset.subtitlePrefix || 'Recent · ';
                            subtitle.textContent = prefix + data.label;
                        }
                        var newUrl = window.location.pathname + '?period=' + data.period;
                        window.history.replaceState({ period: data.period }, '', newUrl);
                    })
                    .catch(function () {
                        if (target) {
                            target.classList.remove('is-loading');
                        }
                    })
                    .finally(hideLoader);
            });
        });
    }

    function initProviderPicker() {
        var select = document.getElementById('id_provider');
        var picker = document.getElementById('provider-picker');
        if (!select || !picker) {
            return;
        }

        function sync(value) {
            picker.querySelectorAll('.provider-picker__option').forEach(function (opt) {
                var selected = opt.dataset.provider === value;
                opt.classList.toggle('is-selected', selected);
                opt.setAttribute('aria-pressed', selected ? 'true' : 'false');
            });
            select.value = value;
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }

        picker.querySelectorAll('.provider-picker__option').forEach(function (opt) {
            opt.addEventListener('click', function () {
                sync(opt.dataset.provider);
            });
        });

        sync(select.value || 'mtn');
    }

    function initPageEnter() {
        var page = document.querySelector('.dash, .page-inner');
        if (page) {
            page.classList.add('page-enter');
        }
    }

    function initNav() {
        var nav = document.querySelector('.bottom-nav');
        if (!nav) {
            return;
        }

        var prefetched = {};

        function onNavIntent(link) {
            if (!link || !link.href || link.classList.contains('active')) {
                return;
            }
            showLoader('Opening…', 'One sec');
            if (!prefetched[link.href]) {
                prefetched[link.href] = true;
                var prefetch = document.createElement('link');
                prefetch.rel = 'prefetch';
                prefetch.href = link.href;
                prefetch.as = 'document';
                document.head.appendChild(prefetch);
            }
        }

        nav.addEventListener('pointerdown', function (e) {
            onNavIntent(e.target.closest('a.nav-item'));
        }, { passive: true });
    }

    function initFormLoaders() {
        document.querySelectorAll('form.setup-form, form.auth-form').forEach(function (form) {
            form.addEventListener('submit', function () {
                if (form.dataset.noLoader === 'true') {
                    return;
                }
                showLoader('Saving…', 'Almost there');
            });
        });
    }

    window.BudgetMe = {
        showLoader: showLoader,
        hideLoader: hideLoader,
    };

    function init() {
        initPageEnter();
        initNav();
        initFormLoaders();
        initProviderPicker();
        document.querySelectorAll('[data-period-tabs]').forEach(initPeriodTabs);
    }

    window.addEventListener('pageshow', function () {
        loaderCount = 0;
        hideLoader();
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
