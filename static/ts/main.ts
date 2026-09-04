// Главный файл: импортирует и инициализирует все модули
import { initCommon } from './common';
import { initSlider } from './slider';
import { initTheme } from './theme';
import { initLightbox } from './lightbox';
import { addToCart } from './cart';

// Инициализация общих функций (прокрутка, лоадер, аккаунт, бургер)
initCommon();

// Инициализация слайдера
initSlider();

// Инициализация темы
initTheme();

// Инициализация лайтбокса и получение функции changeImage
const changeImage = initLightbox();

// Делаем функции глобальными для использования в inline-обработчиках
(window as any).addToCart = addToCart;
(window as any).changeImage = changeImage;