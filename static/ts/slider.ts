/**
 * Модуль слайдера на главной странице.
 * Адаптивный, с автопрокруткой и отключением при малом количестве слайдов.
 */
export function initSlider(): void {
    const track = document.querySelector<HTMLElement>('.slider-track');
    if (!track) return;

    const slides = Array.from(track.children) as HTMLElement[];
    const prevBtn = document.querySelector<HTMLButtonElement>('.slider-btn.prev');
    const nextBtn = document.querySelector<HTMLButtonElement>('.slider-btn.next');
    const viewport = document.querySelector<HTMLElement>('.slider-viewport');
    if (!viewport) return;

    let currentIndex = 0;
    let autoScrollInterval: number | null = null;
    let sliderEnabled = false;

    function isSliderNeeded(): boolean {
        if (slides.length === 0) return false;
        const viewportWidth = viewport.clientWidth;
        let totalWidth = 0;
        slides.forEach((slide) => {
            const style = window.getComputedStyle(slide);
            const width = slide.getBoundingClientRect().width;
            const marginRight = parseFloat(style.marginRight) || 0;
            totalWidth += width + marginRight;
        });
        return totalWidth > viewportWidth + 1;
    }

    function enableSlider(): void {
        sliderEnabled = true;
        viewport.classList.remove('no-slider');
        if (prevBtn) prevBtn.style.display = 'flex';
        if (nextBtn) nextBtn.style.display = 'flex';
        if (slides.length > 1 && !autoScrollInterval) {
            startAutoScroll();
        }
        updateSlider();
    }

    function disableSlider(): void {
        sliderEnabled = false;
        viewport.classList.add('no-slider');
        if (prevBtn) prevBtn.style.display = 'none';
        if (nextBtn) nextBtn.style.display = 'none';
        stopAutoScroll();
        track.style.transform = 'none';
    }

    function getSlideStep(): number {
        if (slides.length === 0) return 0;
        const slide = slides[0];
        const slideWidth = slide.getBoundingClientRect().width;
        const marginRight = parseFloat(window.getComputedStyle(slide).marginRight) || 0;
        return slideWidth + marginRight;
    }

    function updateSlider(): void {
        if (!sliderEnabled) return;
        const step = getSlideStep();
        track.style.transform = `translateX(-${currentIndex * step}px)`;
    }

    function nextSlide(): void {
        if (!sliderEnabled) return;
        currentIndex = (currentIndex + 1) % slides.length;
        updateSlider();
    }

    function prevSlide(): void {
        if (!sliderEnabled) return;
        currentIndex = (currentIndex - 1 + slides.length) % slides.length;
        updateSlider();
    }

    function startAutoScroll(): void {
        stopAutoScroll();
        autoScrollInterval = window.setInterval(nextSlide, 5000);
    }

    function stopAutoScroll(): void {
        if (autoScrollInterval) {
            clearInterval(autoScrollInterval);
            autoScrollInterval = null;
        }
    }

    function restartAutoScroll(): void {
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

    viewport.addEventListener('mouseenter', stopAutoScroll);
    viewport.addEventListener('mouseleave', restartAutoScroll);

    function init(): void {
        if (isSliderNeeded()) {
            enableSlider();
        } else {
            disableSlider();
        }
    }

    init();
    window.addEventListener('resize', init);
}