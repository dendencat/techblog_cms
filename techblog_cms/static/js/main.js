document.addEventListener('DOMContentLoaded', () => {
    // Dismissible flash messages
    document.querySelectorAll('[data-dismissible] [data-dismiss]').forEach((button) => {
        button.addEventListener('click', () => button.closest('[data-dismissible]').remove());
    });

    // "Copy link" buttons on article pages
    document.querySelectorAll('[data-copy-url]').forEach((button) => {
        button.addEventListener('click', async () => {
            const label = button.querySelector('[data-copy-label]');
            try {
                await navigator.clipboard.writeText(button.dataset.copyUrl);
                if (label) {
                    const original = label.textContent;
                    label.textContent = 'コピーしました';
                    setTimeout(() => { label.textContent = original; }, 2000);
                }
            } catch (error) {
                window.prompt('このURLをコピーしてください', button.dataset.copyUrl);
            }
        });
    });

    const menuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (!menuButton || !mobileMenu) {
        return;
    }

    const openLabel = 'メニューを開く';
    const closeLabel = 'メニューを閉じる';

    const setMenuState = (shouldOpen) => {
        if (shouldOpen) {
            mobileMenu.classList.remove('hidden');
            menuButton.setAttribute('aria-expanded', 'true');
            menuButton.classList.add('open');
            menuButton.setAttribute('aria-label', closeLabel);
        } else {
            mobileMenu.classList.add('hidden');
            menuButton.setAttribute('aria-expanded', 'false');
            menuButton.classList.remove('open');
            menuButton.setAttribute('aria-label', openLabel);
        }
    };

    const closeMenu = () => setMenuState(false);

    menuButton.addEventListener('click', (event) => {
        event.preventDefault();
        const shouldOpen = mobileMenu.classList.contains('hidden');
        setMenuState(shouldOpen);
    });

    mobileMenu.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', closeMenu);
    });

    document.addEventListener('click', (event) => {
        if (
            !mobileMenu.classList.contains('hidden') &&
            !mobileMenu.contains(event.target) &&
            !menuButton.contains(event.target)
        ) {
            closeMenu();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeMenu();
        }
    });

    setMenuState(false);
});
