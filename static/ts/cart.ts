/**
 * Модуль корзины: AJAX-добавление товара и анимация иконки.
 */

interface CartResponse {
    success: boolean;
    cart_total?: number;
    message?: string;
}

function getCsrfToken(): string | null {
    return document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.getAttribute('content') ?? null;
}

/**
 * Добавляет товар в корзину через fetch.
 * Функция доступна глобально (window.addToCart).
 */
export function addToCart(productId: number): void {
    const csrfToken = getCsrfToken();
    if (!csrfToken) {
        console.error('CSRF token not found');
        return;
    }

    fetch(`/add_to_cart_ajax/${productId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    })
        .then((response) => response.json())
        .then((data: CartResponse) => {
            if (data.success && data.cart_total !== undefined) {
                const cartCount = document.querySelector<HTMLElement>('.cart-count');
                if (cartCount) {
                    cartCount.textContent = data.cart_total.toString();
                }
                const cartIcon = document.querySelector<HTMLElement>('.header-cart a');
                if (cartIcon) {
                    cartIcon.classList.add('bump');
                    setTimeout(() => cartIcon.classList.remove('bump'), 300);
                }
            } else {
                console.error('Ошибка:', data.message);
            }
        })
        .catch((error) => console.error('Ошибка сети:', error));
}