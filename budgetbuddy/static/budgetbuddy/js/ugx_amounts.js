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

        var stepOnArrows = input.getAttribute('data-ugx-step-arrows') !== 'false';

        if (!stepOnArrows) {
            return;
        }

        input.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                stepAmount(input, 1);
                return;
            }
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                stepAmount(input, -1);
            }
        });
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
