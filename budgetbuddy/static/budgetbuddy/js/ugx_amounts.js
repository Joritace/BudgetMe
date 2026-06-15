(function () {
    function parseAmount(input) {
        var raw = (input.value || '').trim();
        if (raw === '') {
            return null;
        }
        var n = parseInt(raw, 10);
        return Number.isNaN(n) ? null : n;
    }

    function setAmount(input, value) {
        input.value = value <= 0 ? '' : String(value);
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function stepAmount(input, direction) {
        var step = parseInt(input.getAttribute('data-ugx-step') || '1000', 10);
        var min = parseInt(input.getAttribute('min') || '0', 10);
        var current = parseAmount(input);
        var base = current === null ? 0 : current;
        var next = Math.max(min, base + direction * step);
        setAmount(input, next);
    }

    function bindUgxInput(input) {
        if (input.dataset.ugxBound === '1') {
            return;
        }
        input.dataset.ugxBound = '1';

        var lastValue = null;
        var keyUsed = false;

        input.addEventListener('focus', function () {
            lastValue = parseAmount(input);
        });

        input.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                stepAmount(input, 1);
                lastValue = parseAmount(input);
                return;
            }
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                stepAmount(input, -1);
                lastValue = parseAmount(input);
                return;
            }
            keyUsed = true;
        });

        input.addEventListener('input', function () {
            var step = parseInt(input.getAttribute('data-ugx-step') || '1000', 10);
            var current = parseAmount(input);

            if (!keyUsed && lastValue !== null && current !== null) {
                var diff = current - lastValue;
                if (Math.abs(diff) === 1) {
                    var next = Math.max(0, lastValue + (diff > 0 ? step : -step));
                    setAmount(input, next);
                    current = parseAmount(input);
                }
            }

            keyUsed = false;
            lastValue = current;
        });

        input.addEventListener('wheel', function (e) {
            if (document.activeElement !== input) {
                return;
            }
            e.preventDefault();
            stepAmount(input, e.deltaY < 0 ? 1 : -1);
            lastValue = parseAmount(input);
        }, { passive: false });
    }

    function init() {
        document.querySelectorAll('.ugx-amount-input').forEach(bindUgxInput);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    document.addEventListener('focusin', function (e) {
        if (e.target && e.target.classList && e.target.classList.contains('ugx-amount-input')) {
            bindUgxInput(e.target);
        }
    });
})();
