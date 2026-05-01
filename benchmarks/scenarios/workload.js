import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { BASE_URL, getRandomId, DEFAULT_HEADERS } from './shared.js';

/**
 * Смешанный профиль нагрузки (Mixed Workload).
 * Распределение операций приближено к реальному production-трафику:
 *   70% — чтение (просмотр каталога и карточки товара)
 *   20% — запись (оформление заказа)
 *   10% — аналитика (тяжёлые агрегирующие SQL-запросы)
 */
export function mixedWorkload() {
    const rnd = Math.random();

    if (rnd < 0.7) {
        // --- 70% ЧТЕНИЕ (Browsing) ---
        group('Browsing', function () {
            const offset = Math.floor(Math.random() * 20);
            const listRes = http.get(`${BASE_URL}/products?limit=10&offset=${offset}`);
            check(listRes, {
                'list status is 200': (r) => r.status === 200,
            });

            sleep(0.3);

            const detailRes = http.get(`${BASE_URL}/products/${getRandomId(500)}`);
            check(detailRes, {
                'detail status is 200': (r) => r.status === 200,
            });
        });
    } else if (rnd < 0.9) {
        // --- 20% ЗАПИСЬ (Ordering) ---
        group('Ordering', function () {
            const items = [];
            const numItems = Math.floor(Math.random() * 3) + 1;
            for (let i = 0; i < numItems; i++) {
                items.push({
                    product_id: getRandomId(500),
                    quantity: Math.floor(Math.random() * 2) + 1,
                });
            }
            const payload = JSON.stringify({ items: items });
            const orderRes = http.post(`${BASE_URL}/orders`, payload, { headers: DEFAULT_HEADERS });
            check(orderRes, {
                'order created (201)': (r) => r.status === 201,
            });
        });
    } else {
        // --- 10% АНАЛИТИКА (Analytics) ---
        group('Analytics', function () {
            const topRes = http.get(`${BASE_URL}/analytics/products/top?limit=10`);
            check(topRes, {
                'analytics status is 200': (r) => r.status === 200,
            });
        });
    }

    sleep(0.5);
}
