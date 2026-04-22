import http from 'k6/http';
import { check, sleep } from 'k6';
import { commonOptions, BASE_URL, getRandomId } from './shared.js';

/**
 * Сценарий S1: Имитация потребительского поведения при просмотре каталога (Browsing).
 * Моделирование типовой последовательности переходов: обращение к списку товаров 
 * с последующей детализацией характеристик конкретной позиции.
 */

export const options = commonOptions;

export default function () {
    // Эмуляция просмотра перечня продукции (GET /products)
    // Моделирование постраничной навигации через случайное смещение
    const offset = Math.floor(Math.random() * 20);
    const listRes = http.get(`${BASE_URL}/products?limit=10&offset=${offset}`);
    
    check(listRes, {
        'list status is 200': (r) => r.status === 200,
        'list is array': (r) => Array.isArray(r.json()),
    });

    sleep(1); // Имитация времени изучения списка пользователем

    // Запрос детализированных сведений о случайной позиции (GET /products/{id})
    const productId = getRandomId(500);
    const detailRes = http.get(`${BASE_URL}/products/${productId}`);

    check(detailRes, {
        'detail status is 200': (r) => r.status === 200,
        'detail has correct id': (r) => r.json().id !== undefined,
    });

    sleep(2); // Имитация ознакомления с описанием товара
}
