(function () {
    'use strict';

    var loaderEl = null;
    var loaderTimer = null;
    var loaderShown = false;
    var navAbort = null;

    function getLoader() {
        if (!loaderEl) {
            loaderEl = document.getElementById('bb-loader');
        }
        return loaderEl;
    }

    function showLoader(message, subtext) {
        var el = getLoader();
        if (!el || loaderShown) {
            return;
        }
        loaderShown = true;
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
    }

    function hideLoader() {
        var el = getLoader();
        if (!el) {
            return;
        }
        loaderShown = false;
        el.classList.add('is-leaving');
        el.setAttribute('aria-busy', 'false');
        window.setTimeout(function () {
            if (!loaderShown) {
                el.hidden = true;
                el.classList.remove('is-leaving');
            }
        }, 200);
    }

    function showLoaderDelayed(message, subtext, delay) {
        clearTimeout(loaderTimer);
        loaderTimer = window.setTimeout(function () {
            showLoader(message, subtext);
        }, delay || 450);
    }

    function cancelLoaderDelayed() {
        clearTimeout(loaderTimer);
        hideLoader();
    }

    function movePeriodSlider(tabs, activeBtn) {
        var slider = tabs.querySelector('[data-period-slider]');
        if (!slider || !activeBtn) {
            return;
        }
        var buttons = tabs.querySelectorAll('.period-tabs__btn');
        var index = Array.prototype.indexOf.call(buttons, activeBtn);
        slider.style.transform = 'translateX(' + (index * 100) + '%)';
    }

    function loadPeriod(periodBtn) {
        var tabs = periodBtn.closest('[data-period-tabs]');
        if (!tabs) {
            return;
        }

        var endpoint = tabs.dataset.endpoint;
        var targetId = tabs.dataset.target;
        var subtitleId = tabs.dataset.subtitle;
        var target = document.getElementById(targetId);
        var subtitle = subtitleId ? document.getElementById(subtitleId) : null;
        var buttons = tabs.querySelectorAll('.period-tabs__btn');

        buttons.forEach(function (b) {
            b.classList.remove('is-active');
            b.removeAttribute('aria-current');
        });
        periodBtn.classList.add('is-active');
        periodBtn.setAttribute('aria-current', 'true');
        movePeriodSlider(tabs, periodBtn);

        if (target) {
            target.classList.add('is-loading');
        }

        fetch(endpoint + '?period=' + encodeURIComponent(periodBtn.dataset.period), {
            credentials: 'same-origin',
            headers: { Accept: 'application/json' },
        })
            .then(function (res) {
                if (!res.ok) {
                    throw new Error('Failed');
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
                }, 350);
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
            });
    }

    function swapPage(html, url) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var nextWrap = doc.querySelector('.page-wrap');
        if (!nextWrap) {
            throw new Error('Missing page content');
        }

        var wrap = document.querySelector('.page-wrap');
        wrap.innerHTML = nextWrap.innerHTML;

        var nextNav = doc.querySelector('.bottom-nav');
        var nav = document.querySelector('.bottom-nav');
        if (nextNav && nav) {
            nav.replaceWith(nextNav);
        }

        if (doc.title) {
            document.title = doc.title;
        }

        history.pushState({ turbo: true }, '', url);
        bootstrapPage();
    }

    function setNavActive(link) {
        document.querySelectorAll('.bottom-nav a.nav-item').forEach(function (el) {
            el.classList.toggle('active', el === link);
        });
    }

    function navigateTurbo(link) {
        if (!link || !link.href || link.classList.contains('active')) {
            return;
        }

        var targetUrl;
        try {
            targetUrl = new URL(link.href, window.location.origin);
        } catch (err) {
            return;
        }

        if (targetUrl.origin !== window.location.origin) {
            return;
        }

        if (navAbort) {
            navAbort.abort();
        }
        navAbort = new AbortController();

        setNavActive(link);
        link.classList.add('is-pending');
        document.body.classList.add('is-navigating');

        fetch(targetUrl.href, {
            credentials: 'same-origin',
            headers: {
                Accept: 'text/html',
                'X-BB-Turbo': '1',
            },
            signal: navAbort.signal,
        })
            .then(function (res) {
                if (!res.ok) {
                    throw new Error('Bad response');
                }
                return res.text();
            })
            .then(function (html) {
                swapPage(html, targetUrl.href);
            })
            .catch(function (err) {
                if (err && err.name === 'AbortError') {
                    return;
                }
                window.location.assign(targetUrl.href);
            })
            .finally(function () {
                document.body.classList.remove('is-navigating');
                document.querySelectorAll('.nav-item.is-pending').forEach(function (el) {
                    el.classList.remove('is-pending');
                });
                navAbort = null;
            });
    }

    function initProviderPicker() {
        var select = document.getElementById('id_provider');
        var picker = document.getElementById('provider-picker');
        if (!select || !picker || picker.dataset.bound === '1') {
            return;
        }
        picker.dataset.bound = '1';

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

    function initTransferForm() {
        var form = document.getElementById('transfer-form');
        if (!form || form.dataset.bound === '1') {
            return;
        }
        form.dataset.bound = '1';

        var provider = document.getElementById('id_provider');
        var amountRow = document.getElementById('amount-row');
        var phoneGroup = document.getElementById('phone-group');
        var phoneDisplay = document.getElementById('phone-display');
        var submitLabel = document.getElementById('submit-label');
        var phonesEl = document.getElementById('profile-phones-data');
        var profilePhones = phonesEl ? JSON.parse(phonesEl.textContent) : {};

        function selectedDirection() {
            var checked = form.querySelector('input[name="direction"]:checked');
            return checked ? checked.value : 'withdraw';
        }

        function updateForm() {
            if (!provider) {
                return;
            }
            var isCash = provider.value === 'cash';
            var isWithdraw = selectedDirection() === 'withdraw';

            if (amountRow) {
                amountRow.classList.toggle('transfer-amount-row--cash', isCash);
            }
            if (phoneGroup) {
                phoneGroup.hidden = isCash;
            }
            if (phoneDisplay && !isCash) {
                var phone = profilePhones[provider.value] || '';
                phoneDisplay.textContent = phone || 'Not set — add in Profile';
            }
            if (submitLabel) {
                submitLabel.textContent = isWithdraw ? 'Record spend' : 'Record deposit';
            }
            var directionTabs = document.getElementById('direction-tabs');
            var checked = form.querySelector('input[name="direction"]:checked');
            if (directionTabs && checked) {
                directionTabs.dataset.selected = checked.value;
            }
            form.querySelectorAll('.direction-tab').forEach(function (tab) {
                var input = tab.querySelector('input[type="radio"]');
                tab.classList.toggle('active', input && input.checked);
            });
        }

        if (provider) {
            provider.addEventListener('change', updateForm);
        }
        form.querySelectorAll('input[name="direction"]').forEach(function (input) {
            input.addEventListener('change', updateForm);
        });
        updateForm();
    }

    function initBudgetSeeMore() {
        var btn = document.getElementById('budget-see-more');
        var list = document.getElementById('budget-list');
        if (!btn || !list || btn.dataset.bound === '1') {
            return;
        }
        btn.dataset.bound = '1';
        btn.addEventListener('click', function () {
            var expanded = list.classList.toggle('is-expanded');
            btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
            btn.querySelector('.dash-more__label').textContent = expanded ? 'Show less' : 'See more categories';
            var count = btn.querySelector('.dash-more__count');
            if (count) {
                count.hidden = expanded;
            }
            btn.classList.toggle('is-open', expanded);
        });
    }

    function initPageEnter() {
        var page = document.querySelector('.dash, .page-inner');
        if (!page) {
            return;
        }
        page.classList.remove('page-enter');
        void page.offsetWidth;
        page.classList.add('page-enter');
    }

    function bindGlobalHandlers() {
        if (document.body.dataset.bbBound === '1') {
            return;
        }
        document.body.dataset.bbBound = '1';

        document.addEventListener('click', function (event) {
            var periodBtn = event.target.closest('.period-tabs__btn');
            if (periodBtn && !periodBtn.classList.contains('is-active')) {
                event.preventDefault();
                loadPeriod(periodBtn);
                return;
            }

            var navLink = event.target.closest('.bottom-nav a.nav-item');
            if (navLink) {
                event.preventDefault();
                navigateTurbo(navLink);
            }
        });

        document.addEventListener('submit', function (event) {
            var form = event.target;
            if (form.matches('form.sidebar-logout-form, form[action*="logout"]')) {
                clearServiceWorkerCaches();
            }
            if (!form.matches('form.setup-form, form.auth-form, #transfer-form, #savings-form')) {
                return;
            }
            if (form.dataset.noLoader === 'true') {
                return;
            }
            showLoaderDelayed('Saving…', 'Almost there', 500);
        });
    }

    function bootstrapPage() {
        hideLoader();
        cancelLoaderDelayed();
        initPageEnter();
        initProviderPicker();
        initTransferForm();
        initBudgetSeeMore();
        document.querySelectorAll('[data-period-tabs]').forEach(function (tabs) {
            var active = tabs.querySelector('.period-tabs__btn.is-active');
            if (active) {
                movePeriodSlider(tabs, active);
            }
        });
    }

    function clearServiceWorkerCaches() {
        if (navigator.serviceWorker && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHES' });
        }
    }

    function registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            return;
        }
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () {});
        });
    }

    window.BudgetMe = {
        showLoader: showLoader,
        hideLoader: hideLoader,
        bootstrapPage: bootstrapPage,
    };

    bindGlobalHandlers();
    bootstrapPage();
    registerServiceWorker();

    window.addEventListener('pageshow', function () {
        cancelLoaderDelayed();
        hideLoader();
    });

    window.addEventListener('popstate', function () {
        window.location.reload();
    });
})();
