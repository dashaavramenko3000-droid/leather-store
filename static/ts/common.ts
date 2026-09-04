/**
 * Общие утилиты: лоадер, кнопка "Наверх", плавная прокрутка, аккаунт, бургер-меню,
 * автоматическое скрытие flash-уведомлений и SPA-навигация в личном кабинете.
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
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Лоадер
    const pageLoader = document.getElementById('page-loader') as HTMLElement | null;
    function showLoader(): void { pageLoader?.classList.add('show'); }
    function hideLoader(): void { pageLoader?.classList.remove('show'); }
    window.addEventListener('beforeunload', showLoader);
    window.addEventListener('load', () => { setTimeout(hideLoader, 300); });
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

    // Автоматическое скрытие flash-уведомлений
    const flashMessages = document.querySelectorAll<HTMLElement>('.flash-message');
    flashMessages.forEach((el) => {
        setTimeout(() => {
            el.style.transition = 'opacity 0.5s, transform 0.5s';
            el.style.opacity = '0';
            el.style.transform = 'translateX(30px)';
            setTimeout(() => el.remove(), 500);
        }, 5000);
    });

    // SPA-навигация внутри личного кабинета
    initProfileNavigation();
}

/**
 * Инициализирует SPA-навигацию в личном кабинете.
 */
function initProfileNavigation(): void {
    const profileLinks = document.querySelectorAll<HTMLAnchorElement>('.profile-link');
    if (profileLinks.length === 0) return;

    const profileContent = document.getElementById('profile-content') as HTMLElement | null;
    const pageLoader = document.getElementById('page-loader') as HTMLElement | null;

    // Функция подсветки активного пункта
    const setActive = (link: HTMLAnchorElement): void => {
        profileLinks.forEach((el) => el.classList.remove('active'));
        link.classList.add('active');
    };

    // Обработчик клика по ссылкам меню
    document.addEventListener('click', (e: MouseEvent) => {
        const link = (e.target as HTMLElement).closest<HTMLAnchorElement>('.profile-link');
        if (!link) return;

        e.preventDefault();
        const url = link.href;

        // Мгновенно подсвечиваем выбранный пункт
        setActive(link);

        // Показываем лоадер
        pageLoader?.classList.add('show');

        // Загружаем содержимое через fetch
        fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
            .then((response) => {
                if (!response.ok) throw new Error('Ошибка сети');
                return response.text();
            })
            .then((html: string) => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.getElementById('profile-content');
                if (newContent && profileContent) {
                    profileContent.innerHTML = newContent.innerHTML;
                    history.pushState({}, '', url);
                    // Обновляем хлебные крошки
                    const breadcrumbActive = document.querySelector<HTMLElement>('.breadcrumb-item.active');
                    if (breadcrumbActive && link.dataset.title) {
                        breadcrumbActive.textContent = link.dataset.title;
                    }
                }
            })
            .catch((error: unknown) => {
                console.error('Ошибка загрузки раздела:', error);
                // В случае ошибки переходим обычным способом
                window.location.href = url;
            })
            .finally(() => {
                pageLoader?.classList.remove('show');
            });
    });

    // Обработчик кнопки "Назад" браузера
    window.addEventListener('popstate', () => {
        // Простейший способ – перезагрузить страницу с текущим URL
        window.location.reload();
    });
}