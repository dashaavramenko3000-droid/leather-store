/**
 * Общие утилиты: лоадер, кнопка "Наверх", плавная прокрутка, аккаунт, бургер-меню.
 */
export function initCommon(): void {
    // Плавная прокрутка к якорям
    document.querySelectorAll<HTMLAnchorElement>('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', function (e: Event) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId) {
                const target = document.querySelector(targetId) as HTMLElement | null;
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                    });
                }
            }
        });
    });

    // Кнопка "Наверх"
    const scrollToTopBtn = document.getElementById('scrollToTopBtn') as HTMLButtonElement | null;
    if (scrollToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 150) {
                scrollToTopBtn.classList.add('show');
            } else {
                scrollToTopBtn.classList.remove('show');
            }
        });

        scrollToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth',
            });
        });
    }

    // Лоадер
    const pageLoader = document.getElementById('page-loader') as HTMLElement | null;
    function showLoader(): void {
        pageLoader?.classList.add('show');
    }
    function hideLoader(): void {
        pageLoader?.classList.remove('show');
    }
    window.addEventListener('beforeunload', showLoader);
    window.addEventListener('load', () => {
        setTimeout(hideLoader, 300);
    });
    document.addEventListener('submit', (e: SubmitEvent) => {
        const form = e.target as HTMLFormElement;
        if (form.closest('form[data-ajax="true"]')) return;
        showLoader();
    });

    // Выпадающее меню аккаунта
    const accountToggle = document.getElementById('account-toggle') as HTMLButtonElement | null;
    const accountDropdown = document.getElementById('account-dropdown') as HTMLElement | null;
    if (accountToggle && accountDropdown) {
        accountToggle.addEventListener('click', (e: Event) => {
            e.stopPropagation();
            accountDropdown.classList.toggle('open');
        });

        document.addEventListener('click', (e: MouseEvent) => {
            if (!accountDropdown.contains(e.target as Node) && e.target !== accountToggle) {
                accountDropdown.classList.remove('open');
            }
        });
    }

    // Бургер-меню
    const burgerMenu = document.getElementById('burger-menu') as HTMLButtonElement | null;
    const mainNav = document.getElementById('main-nav') as HTMLElement | null;
    if (burgerMenu && mainNav) {
        burgerMenu.addEventListener('click', () => {
            mainNav.classList.toggle('open');
            const icon = burgerMenu.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-bars');
                icon.classList.toggle('fa-times');
            }
        });

        mainNav.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                mainNav.classList.remove('open');
                const icon = burgerMenu.querySelector('i');
                if (icon) {
                    icon.classList.add('fa-bars');
                    icon.classList.remove('fa-times');
                }
            });
        });

        document.addEventListener('click', (e: MouseEvent) => {
            if (!mainNav.contains(e.target as Node) && !burgerMenu.contains(e.target as Node)) {
                mainNav.classList.remove('open');
                const icon = burgerMenu.querySelector('i');
                if (icon) {
                    icon.classList.add('fa-bars');
                    icon.classList.remove('fa-times');
                }
            }
        });
    }
}