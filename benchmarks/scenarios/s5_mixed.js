import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { commonOptions, BASE_URL, getRandomId, DEFAULT_HEADERS } from './shared.js';

/**
 * Сценарий S5: Реализация смешанного профиля нагрузки (Mixed Workflow).
 * Комплексная имитация функционирования системы со следующим распределением: 
 * 70% операции чтения, 20% транзакции оформления, 10% аналитические выборки.
 */

export const options = commonOptions;

export default function () {
    const rnd = Math.random();

    if (rnd < 0.7) {
        // --- 70% ЧТЕНИЕ (Browsing) ---
        group('Browsing', function () {
            const listRes = http.get(`${BASE_URL}/products?limit=10`);
            check(listRes, { 'browse list status is 200': (r) => r.status === 200 });
            
            sleep(1);
            
            const detailRes = http.get(`${BASE_URL}/products/${getRandomId(500)}`);
            check(detailRes, { 'browse detail status is 200': (r) => r.status === 200 });
        });
    } else if (rnd < 0.9) {
        // --- 20% ОФОРМЛЕНИЕ ЗАКАЗА (Ordering) ---
        group('Ordering', function () {
            const payload = JSON.stringify({
                items: [{ product_id: getRandomId(500), quantity: 1 }]
            });
            const orderRes = http.post(`${BASE_URL}/orders`, payload, { headers: DEFAULT_HEADERS });
            check(orderRes, { 'order status is 201': (r) => r.status === 201 });
        });
    } else {
        // --- 10% АНАЛИТИКА (Analytics) ---
        group('Analytics', function () {
            const topRes = http.get(`${BASE_URL}/analytics/products/top`);
            check(topRes, { 'analytics status is 200': (r) => r.status === 200 });
        });
    }

    sleep(1.5);
}
