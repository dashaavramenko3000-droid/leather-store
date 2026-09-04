/**
 * Модуль лайтбокса для галереи товара.
 * Предоставляет функцию changeImage для миниатюр.
 */
export function initLightbox(): (index: number) => void {
    const gallery = document.getElementById('product-gallery');
    if (!gallery) return () => {};

    const mainImage = document.getElementById('main-product-image') as HTMLImageElement | null;
    const thumbnails = document.querySelectorAll<HTMLImageElement>('.thumbnail');
    const zoomButton = document.getElementById('zoom-button') as HTMLButtonElement | null;
    const counter = document.getElementById('image-counter') as HTMLElement | null;

    const images: string[] = Array.from(thumbnails).map((thumb) => thumb.src);
    if (images.length === 0 && mainImage) {
        images.push(mainImage.src);
    }

    let currentIndex = 0;

    function changeImage(index: number): void {
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

    const lightboxImg = overlay.querySelector<HTMLImageElement>('.lightbox-image')!;
    const caption = overlay.querySelector<HTMLElement>('.lightbox-caption')!;
    const closeBtn = overlay.querySelector<HTMLElement>('.lightbox-close')!;
    const prevBtn = overlay.querySelector<HTMLButtonElement>('.lightbox-prev')!;
    const nextBtn = overlay.querySelector<HTMLButtonElement>('.lightbox-next')!;

    function showLightbox(index: number): void {
        currentIndex = index;
        lightboxImg.src = images[currentIndex];
        caption.textContent = `${currentIndex + 1} / ${images.length}`;
        overlay.classList.add('show');
    }

    function hideLightbox(): void {
        overlay.classList.remove('show');
        lightboxImg.classList.remove('zoomed');
    }

    function nextImage(): void {
        currentIndex = (currentIndex + 1) % images.length;
        lightboxImg.src = images[currentIndex];
        caption.textContent = `${currentIndex + 1} / ${images.length}`;
    }

    function prevImage(): void {
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        lightboxImg.src = images[currentIndex];
        caption.textContent = `${currentIndex + 1} / ${images.length}`;
    }

    overlay.addEventListener('click', (e: MouseEvent) => {
        if (e.target === overlay) hideLightbox();
    });
    closeBtn.addEventListener('click', hideLightbox);
    prevBtn.addEventListener('click', (e: MouseEvent) => {
        e.stopPropagation();
        prevImage();
    });
    nextBtn.addEventListener('click', (e: MouseEvent) => {
        e.stopPropagation();
        nextImage();
    });
    lightboxImg.addEventListener('click', () => {
        lightboxImg.classList.toggle('zoomed');
    });

    document.addEventListener('keydown', (e: KeyboardEvent) => {
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

    // Свайп на главном изображении
    let touchStartX = 0;
    let touchEndX = 0;
    const container = document.querySelector<HTMLElement>('.main-image-container');
    if (container) {
        container.addEventListener(
            'touchstart',
            (e: TouchEvent) => {
                touchStartX = e.changedTouches[0].screenX;
            },
            { passive: true }
        );
        container.addEventListener(
            'touchend',
            (e: TouchEvent) => {
                touchEndX = e.changedTouches[0].screenX;
                const diff = touchStartX - touchEndX;
                if (Math.abs(diff) > 50 && images.length > 1) {
                    if (diff > 0) changeImage(currentIndex + 1);
                    else changeImage(currentIndex - 1);
                }
            },
            { passive: true }
        );
    }

    if (images.length > 0) {
        changeImage(0);
    }

    return changeImage;
}