// ========================
// ОСНОВНОЙ СКРИПТ САЙТА
// ========================

// Плавная прокрутка к якорям
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
        return totalWidth > viewportWidth + 1;
    }

    function enableSlider() {
        sliderEnabled = true;
        viewport.classList.remove('no-slider');
        if (prevBtn) prevBtn.style.display = 'flex';
        if (nextBtn) nextBtn.style.display = 'flex';
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

    if (viewport) {
        viewport.addEventListener('mouseenter', stopAutoScroll);
        viewport.addEventListener('mouseleave', restartAutoScroll);
    }

    function initSlider() {
        if (isSliderNeeded()) {
            enableSlider();
        } else {
            disableSlider();
        }
    }

    initSlider();
    window.addEventListener('resize', initSlider);
})();

// Лоадер страницы
const pageLoader = document.getElementById('page-loader');

function showLoader() {
    if (pageLoader) pageLoader.classList.add('show');
}

function hideLoader() {
    if (pageLoader) pageLoader.classList.remove('show');
}

window.addEventListener('beforeunload', showLoader);

window.addEventListener('load', function () {
    setTimeout(hideLoader, 300);
});

document.addEventListener('submit', function (e) {
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

    document.addEventListener('click', function (e) {
        if (!accountDropdown.contains(e.target) && e.target !== accountToggle) {
            accountDropdown.classList.remove('open');
        }
    });
}

// AJAX добавление в корзину
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
                const cartCount = document.querySelector('.cart-count');
                if (cartCount) {
                    cartCount.textContent = data.cart_total;
                }
            } else {
                console.error('Ошибка:', data.message);
            }
        })
        .catch(error => console.error('Ошибка сети:', error));
}

// Бургер-меню
const burgerMenu = document.getElementById('burger-menu');
const mainNav = document.getElementById('main-nav');

if (burgerMenu && mainNav) {
    burgerMenu.addEventListener('click', function () {
        mainNav.classList.toggle('open');
    });

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
// Кастомный лайтбокс для галереи товара
// ========================
(function () {
    const gallery = document.getElementById('product-gallery');
    if (!gallery) return;

    const mainImage = document.getElementById('main-product-image');
    const thumbnails = document.querySelectorAll('.thumbnail');
    const zoomButton = document.getElementById('zoom-button');
    const counter = document.getElementById('image-counter');

    // Собираем URL всех изображений из миниатюр
    const images = Array.from(thumbnails).map(thumb => thumb.src);
    if (images.length === 0 && mainImage) {
        images.push(mainImage.src);
    }

    let currentIndex = 0;

    function changeImage(index) {
        if (index < 0 || index >= images.length) return;
        currentIndex = index;
        if (mainImage) {
            mainImage.src = images[currentIndex];
        }
        if (counter) {
            counter.textContent = `${currentIndex + 1} / ${images.length}`;
        }
        thumbnails.forEach((thumb, i) => {
            thumb.classList.toggle('active', i === currentIndex);
        });
    }

    thumbnails.forEach((thumb, idx) => {
        thumb.addEventListener('click', () => changeImage(idx));
    });

    // Создание оверлея лайтбокса
    const overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay';
    overlay.innerHTML = `
        <span class="lightbox-close">&times;</span>
        <button class="lightbox-prev">&#10094;</button>
        <button class="lightbox-next">&#10095;</button>
        <div class="lightbox-image-container">
            <img class="lightbox-image" src="" alt="Просмотр изображения">
        </div>
        <div class="lightbox-caption"></div>
    `;
    document.body.appendChild(overlay);

    const lightboxImg = overlay.querySelector('.lightbox-image');
    const caption = overlay.querySelector('.lightbox-caption');
    const closeBtn = overlay.querySelector('.lightbox-close');
    const prevBtn = overlay.querySelector('.lightbox-prev');
    const nextBtn = overlay.querySelector('.lightbox-next');

    function showLightbox(index) {
        currentIndex = index;
        lightboxImg.src = images[currentIndex];
        caption.textContent = `${currentIndex + 1} / ${images.length}`;
        overlay.classList.add('show');
    }

    function hideLightbox() {
        overlay.classList.remove('show');
        lightboxImg.classList.remove('zoomed');
    }

    function nextImage() {
        currentIndex = (currentIndex + 1) % images.length;
        lightboxImg.src = images[currentIndex];
        caption.textContent = `${currentIndex + 1} / ${images.length}`;
    }

    function prevImage() {
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        lightboxImg.src = images[currentIndex];
        caption.textContent = `${currentIndex + 1} / ${images.length}`;
    }

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) hideLightbox();
    });

    closeBtn.addEventListener('click', hideLightbox);
    prevBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        prevImage();
    });
    nextBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        nextImage();
    });

    lightboxImg.addEventListener('click', () => {
        lightboxImg.classList.toggle('zoomed');
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('show')) {
            hideLightbox();
        }
    });

    if (zoomButton) {
        zoomButton.addEventListener('click', () => showLightbox(currentIndex));
    }

    if (mainImage) {
        mainImage.addEventListener('dblclick', () => showLightbox(currentIndex));
    }

    let touchStartX = 0;
    let touchEndX = 0;
    const container = document.querySelector('.main-image-container');
    if (container) {
        container.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, {passive: true});
        container.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            const diff = touchStartX - touchEndX;
            if (Math.abs(diff) > 50 && images.length > 1) {
                if (diff > 0) changeImage(currentIndex + 1);
                else changeImage(currentIndex - 1);
            }
        }, {passive: true});
    }

    if (images.length > 0) {
        changeImage(0);
    }
})();

const cartIcon = document.querySelector('.header-cart a');
if (cartIcon) {
    cartIcon.classList.add('bump');
    setTimeout(() => cartIcon.classList.remove('bump'), 300);
}

document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
        flash.style.display = 'none';
    }, 5000);
});

