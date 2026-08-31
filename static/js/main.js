// Простой скрипт для плавной прокрутки к якорям
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Кнопка "Наверх"
const scrollToTopBtn = document.getElementById('scrollToTopBtn');

if (scrollToTopBtn) {
    window.addEventListener('scroll', () => {
        // Показываем кнопку, когда прокрутили больше высоты шапки (например, 150px)
        if (window.scrollY > 150) {
            scrollToTopBtn.classList.add('show');
        } else {
            scrollToTopBtn.classList.remove('show');
        }
    });

    scrollToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Слайдер на главной странице
(function () {
    const track = document.querySelector('.slider-track');
    if (!track) return;

    const slides = Array.from(track.children);
    const prevBtn = document.querySelector('.slider-btn.prev');
    const nextBtn = document.querySelector('.slider-btn.next');
    const viewport = document.querySelector('.slider-viewport');

    let currentIndex = 0;
    let autoScrollInterval = null;
    let sliderEnabled = false;

    // Проверка: нужен ли слайдер (ширина трека больше ширины viewport)
    function isSliderNeeded() {
        if (slides.length === 0) return false;
        const viewportWidth = viewport.clientWidth;
        let totalWidth = 0;
        slides.forEach(slide => {
            const style = window.getComputedStyle(slide);
            const width = slide.getBoundingClientRect().width;
            const marginRight = parseFloat(style.marginRight) || 0;
            totalWidth += width + marginRight;
        });
        return totalWidth > viewportWidth + 1; // +1 для надёжности
    }

    function enableSlider() {
        sliderEnabled = true;
        viewport.classList.remove('no-slider');
        if (prevBtn) prevBtn.style.display = 'flex';
        if (nextBtn) nextBtn.style.display = 'flex';
        // Запускаем автопрокрутку, если слайдов больше одного
        if (slides.length > 1 && !autoScrollInterval) {
            startAutoScroll();
        }
        updateSlider();
    }

    function disableSlider() {
        sliderEnabled = false;
        viewport.classList.add('no-slider');
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
        stopAutoScroll();
        track.style.transform = 'none';
    }

    function getSlideStep() {
        if (slides.length === 0) return 0;
        const slide = slides[0];
        const slideWidth = slide.getBoundingClientRect().width;
        const marginRight = parseFloat(window.getComputedStyle(slide).marginRight) || 0;
        return slideWidth + marginRight;
    }

    function updateSlider() {
        if (!sliderEnabled) return;
        const step = getSlideStep();
        track.style.transform = `translateX(-${currentIndex * step}px)`;
    }

    function nextSlide() {
        if (!sliderEnabled) return;
        currentIndex = (currentIndex + 1) % slides.length;
        updateSlider();
    }

    function prevSlide() {
        if (!sliderEnabled) return;
        currentIndex = (currentIndex - 1 + slides.length) % slides.length;
        updateSlider();
    }

    function startAutoScroll() {
        stopAutoScroll();
        autoScrollInterval = setInterval(nextSlide, 5000);
    }

    function stopAutoScroll() {
        if (autoScrollInterval) {
            clearInterval(autoScrollInterval);
            autoScrollInterval = null;
        }
    }

    function restartAutoScroll() {
        if (sliderEnabled && slides.length > 1) {
            startAutoScroll();
        }
    }

    // Обработчики кнопок
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            nextSlide();
            restartAutoScroll();
        });
    }
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            prevSlide();
            restartAutoScroll();
        });
    }

    // Остановка при наведении
    if (viewport) {
        viewport.addEventListener('mouseenter', stopAutoScroll);
        viewport.addEventListener('mouseleave', restartAutoScroll);
    }

    // Инициализация и реакция на изменение размера окна
    function initSlider() {
        if (isSliderNeeded()) {
            enableSlider();
        } else {
            disableSlider();
        }
    }

    initSlider();

    // Пересчитываем при изменении размера окна
    window.addEventListener('resize', () => {
        initSlider();
    });
})();
// Управление лоадером страницы
const pageLoader = document.getElementById('page-loader');

function showLoader() {
    if (pageLoader) pageLoader.classList.add('show');
}

function hideLoader() {
    if (pageLoader) pageLoader.classList.remove('show');
}

// Показываем лоадер при уходе со страницы
window.addEventListener('beforeunload', showLoader);

// Скрываем лоадер после полной загрузки новой страницы
window.addEventListener('load', function () {
    // Небольшая задержка, чтобы лоадер не мигал
    setTimeout(hideLoader, 300);
});

// Также показываем лоадер при отправке форм (POST)
document.addEventListener('submit', function (e) {
    // Игнорируем формы с AJAX (если есть)
    if (e.target.closest('form[data-ajax="true"]')) return;
    showLoader();
});
// Выпадающее меню аккаунта
const accountToggle = document.getElementById('account-toggle');
const accountDropdown = document.getElementById('account-dropdown');

if (accountToggle && accountDropdown) {
    accountToggle.addEventListener('click', function (e) {
        e.stopPropagation();
        accountDropdown.classList.toggle('open');
    });

    // Закрытие меню при клике вне его
    document.addEventListener('click', function (e) {
        if (!accountDropdown.contains(e.target) && e.target !== accountToggle) {
            accountDropdown.classList.remove('open');
        }
    });
}

function addToCart(productId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    fetch(`/add_to_cart_ajax/${productId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем счётчик корзины в шапке
                const cartCount = document.querySelector('.cart-count');
                if (cartCount) {
                    cartCount.textContent = data.cart_total;
                }
                // Можно показать всплывающее сообщение (например, через alert или кастомное)
                // Простой вариант:
                //alert(`Товар "${data.product_name}" добавлен в корзину`);
            } else {
                alert('Ошибка: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при добавлении товара');
        });
}

// Бургер-меню
const burgerMenu = document.getElementById('burger-menu');
const mainNav = document.getElementById('main-nav');

if (burgerMenu && mainNav) {
    burgerMenu.addEventListener('click', function () {
        mainNav.classList.toggle('open');
    });

    // Закрывать меню при клике на ссылку (необязательно)
    mainNav.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            mainNav.classList.remove('open');
        });
    });
}

// Переключение тёмной темы
const themeToggle = document.getElementById('theme-toggle');
const currentTheme = localStorage.getItem('theme');

if (currentTheme === 'dark') {
    document.body.classList.add('dark-theme');
    if (themeToggle) themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
}

if (themeToggle) {
    themeToggle.addEventListener('click', function () {
        document.body.classList.toggle('dark-theme');
        if (document.body.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            localStorage.setItem('theme', 'light');
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        }
    });
}


// ========================
// Улучшенная галерея товара
// ========================
(function () {
    const gallery = document.getElementById('product-gallery');
    if (!gallery) return;

    const mainImage = document.getElementById('main-product-image');
    const container = document.getElementById('main-image-container');
    const counter = document.getElementById('image-counter');
    const thumbnails = document.querySelectorAll('.thumbnail');
    const zoomButton = document.getElementById('zoom-button');

    // Получаем список изображений из data-атрибута
    let images = [];
    if (container && container.dataset.images) {
        try {
            images = JSON.parse(container.dataset.images);
        } catch (e) {
            console.error('Ошибка парсинга data-images', e);
        }
    }

    let currentIndex = parseInt(container?.dataset.current || '0');

    // Функция смены изображения
    function changeImage(index) {
        if (index < 0 || index >= images.length) return;
        currentIndex = index;
        mainImage.src = images[currentIndex];
        if (counter) {
            counter.textContent = `${currentIndex + 1} / ${images.length}`;
        }
        // Обновляем активную миниатюру
        thumbnails.forEach((thumb, i) => {
            if (i === currentIndex) thumb.classList.add('active');
            else thumb.classList.remove('active');
        });
        // Обновляем data-current
        container.dataset.current = currentIndex;
    }

    // Навешиваем обработчик на миниатюры (если клики уже подключены через onclick, можно не дублировать)
    thumbnails.forEach((thumb, idx) => {
        thumb.addEventListener('click', () => changeImage(idx));
    });

    // Зум по кнопке
    if (zoomButton) {
        zoomButton.addEventListener('click', () => {
            openLightbox(currentIndex);
        });
    }

    // Двойной клик по главному изображению тоже открывает лайтбокс
    mainImage.addEventListener('dblclick', () => openLightbox(currentIndex));

    // Свайп на мобильных для главного изображения
    let touchStartX = 0;
    let touchEndX = 0;

    container.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, {passive: true});

    container.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) { // минимальный порог свайпа
            if (diff > 0 && currentIndex < images.length - 1) {
                changeImage(currentIndex + 1);
            } else if (diff < 0 && currentIndex > 0) {
                changeImage(currentIndex - 1);
            }
        }
    }, {passive: true});

    // ========================
    // Лайтбокс (полноэкранный просмотр)
    // ========================
    function createLightbox() {
        // Создаём оверлей
        const overlay = document.createElement('div');
        overlay.className = 'lightbox-overlay';
        overlay.id = 'lightbox-overlay';

        // Кнопка закрытия
        const closeBtn = document.createElement('span');
        closeBtn.className = 'lightbox-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = closeLightbox;

        // Кнопки навигации
        const prevBtn = document.createElement('button');
        prevBtn.className = 'lightbox-prev';
        prevBtn.innerHTML = '&#10094;';
        prevBtn.onclick = (e) => {
            e.stopPropagation();
            changeLightboxImage(-1);
        };

        const nextBtn = document.createElement('button');
        nextBtn.className = 'lightbox-next';
        nextBtn.innerHTML = '&#10095;';
        nextBtn.onclick = (e) => {
            e.stopPropagation();
            changeLightboxImage(1);
        };

        // Контейнер изображения
        const imgContainer = document.createElement('div');
        imgContainer.className = 'lightbox-image-container';
        const img = document.createElement('img');
        img.className = 'lightbox-image';
        img.id = 'lightbox-img';
        imgContainer.appendChild(img);

        // Подпись (счётчик)
        const caption = document.createElement('div');
        caption.className = 'lightbox-caption';
        caption.id = 'lightbox-caption';

        overlay.appendChild(closeBtn);
        overlay.appendChild(prevBtn);
        overlay.appendChild(nextBtn);
        overlay.appendChild(imgContainer);
        overlay.appendChild(caption);

        // Закрытие при клике на фон
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeLightbox();
        });

        // Зум по клику на изображение
        img.addEventListener('click', () => {
            img.classList.toggle('zoomed');
        });

        document.body.appendChild(overlay);
        return overlay;
    }

    const lightbox = createLightbox();
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxCaption = document.getElementById('lightbox-caption');

    function openLightbox(index) {
        currentIndex = index;
        updateLightboxImage();
        lightbox.classList.add('show');
    }

    function closeLightbox() {
        lightbox.classList.remove('show');
        lightboxImg.classList.remove('zoomed');
    }

    function updateLightboxImage() {
        lightboxImg.src = images[currentIndex];
        lightboxCaption.textContent = `${currentIndex + 1} / ${images.length}`;
    }

    function changeLightboxImage(delta) {
        currentIndex += delta;
        if (currentIndex < 0) currentIndex = images.length - 1;
        if (currentIndex >= images.length) currentIndex = 0;
        updateLightboxImage();
    }

    // Закрытие по клавише Esc
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && lightbox.classList.contains('show')) {
            closeLightbox();
        }
    });

    // Инициализация
    if (images.length > 0) {
        changeImage(0);
    }
})();