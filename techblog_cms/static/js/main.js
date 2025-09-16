document.addEventListener('DOMContentLoaded', function() {
    const menuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (!menuButton || !mobileMenu) {
        return;
    }

    const closeMenu = () => {
        mobileMenu.classList.add('hidden');
        menuButton.setAttribute('aria-expanded', 'false');
    };

    menuButton.addEventListener('click', (event) => {
        event.preventDefault();
        const isHidden = mobileMenu.classList.contains('hidden');

        if (isHidden) {
            mobileMenu.classList.remove('hidden');
            menuButton.setAttribute('aria-expanded', 'true');
        } else {
            closeMenu();
        }
    });

    mobileMenu.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => {
            closeMenu();
        });
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
});