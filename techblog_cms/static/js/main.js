document.addEventListener('DOMContentLoaded', () => {
    const menuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (!menuButton || !mobileMenu) {
        return;
    }

    const openLabel = 'メインメニューを開く';
    const closeLabel = 'メインメニューを閉じる';
    const srLabel = menuButton.querySelector('[data-menu-button-label]');

    const setMenuState = (shouldOpen) => {
        if (shouldOpen) {
            mobileMenu.classList.remove('hidden');
            menuButton.setAttribute('aria-expanded', 'true');
            menuButton.classList.add('open');
            menuButton.setAttribute('aria-label', closeLabel);
            if (srLabel) {
                srLabel.textContent = closeLabel;
            }
        } else {
            mobileMenu.classList.add('hidden');
            menuButton.setAttribute('aria-expanded', 'false');
            menuButton.classList.remove('open');
            menuButton.setAttribute('aria-label', openLabel);
            if (srLabel) {
                srLabel.textContent = openLabel;
            }
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
